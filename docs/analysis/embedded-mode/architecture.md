# MLX Backend Architecture

## System Overview

The MLX backend is part of CoPaw's local model system, enabling in-process inference on Apple Silicon.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CoPaw Application                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Agent Runner (agentscope)                │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │            LocalChatModel (ChatModelBase)             │  │ │
│  │  │  - Async interface                                    │  │ │
│  │  │  - Streaming support                                  │  │ │
│  │  │  - Tool calling wrapper                               │  │ │
│  │  └──────────────────────┬───────────────────────────────┘  │ │
│  │                         │                                   │ │
│  │  ┌──────────────────────▼───────────────────────────────┐  │ │
│  │  │              MlxBackend (LocalBackend)                │  │ │
│  │  │  - Model loading/unloading                           │  │ │
│  │  │  - Tokenization                                       │  │ │
│  │  │  - Generation loop                                    │  │ │
│  │  └──────────────────────┬───────────────────────────────┘  │ │
│  │                         │                                   │ │
│  └─────────────────────────┼───────────────────────────────────┘ │
│                            │                                      │
│  ┌─────────────────────────▼───────────────────────────────────┐ │
│  │                    MLX Framework                             │ │
│  │  - mlx_lm (model loading and generation)                    │ │
│  │  - mlx (tensor operations)                                  │ │
│  └──────────────────────┬──────────────────────────────────────┘ │
│                           │                                        │
│  ┌──────────────────────▼──────────────────────────────────────┐ │
│  │              Apple Silicon Hardware                          │ │
│  │  - Unified Memory (CPU/GPU shared)                          │ │
│  │  - Metal Performance Shaders (GPU acceleration)             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. LocalChatModel (`chat_model.py`)

**Purpose**: Adapter between AgentScope's `ChatModelBase` and `LocalBackend`

**Key Responsibilities**:
- Convert AgentScope messages to backend format
- Handle async/sync bridging via thread executor
- Stream responses via asyncio.Queue
- Parse tool calls and structured output

**Data Flow**:
```
AgentScope ChatModel API
    ↓ (async call)
LocalChatModel.__call__()
    ↓ (run in executor)
MlxBackend.chat_completion()
    ↓ (sync response)
LocalChatModel._parse_completion_response()
    ↓ (ChatResponse)
AgentScope Agent
```

### 2. MlxBackend (`mlx_backend.py`)

**Purpose**: Direct wrapper around `mlx-lm` library

**Key Methods**:

| Method | Purpose |
|--------|---------|
| `__init__()` | Load model and tokenizer from disk |
| `_build_prompt()` | Apply chat template to messages |
| `chat_completion()` | Generate non-streaming response |
| `chat_completion_stream()` | Generate streaming response |
| `unload()` | Free model from memory |

**Implementation Notes**:
- Uses `_resolve_model_dir()` to handle both file and directory paths
- Normalizes messages for MLX tokenizer (content must be string)
- Supports tool calling via `tokenizer.has_tool_calling` attribute
- Structured output via prompt engineering (appends JSON schema to prompt)

### 3. LocalModelManager (`manager.py`)

**Purpose**: Model download and manifest management

**Key Methods**:

| Method | Purpose |
|--------|---------|
| `download_model_sync()` | Download from HuggingFace/ModelScope |
| `_download_from_huggingface()` | HF-specific download logic |
| `_validate_mlx_directory()` | Verify required files present |
| `_register_model()` | Add model to manifest.json |

**MLX-Specific Handling**:
```python
# Directory-based download (snapshot_download)
snapshot_dir = snapshot_download(
    repo_id=repo_id,
    local_dir=str(local_dir),
)

# Validation: requires config.json + safetensors
required = ["config.json"]
st_files = [f for f in model_dir.rglob("*.safetensors")]
```

### 4. Factory (`factory.py`)

**Purpose**: Singleton pattern for active model management

**Key Components**:
- `_active_backend`: Currently loaded backend instance
- `_active_model_id`: ID of currently loaded model
- `_lock`: Thread-safe access control

**Loading Flow**:
```
create_local_chat_model(model_id)
    ↓
get_local_model(model_id)  # from manifest
    ↓
_create_backend(info)  # instantiate MlxBackend
    ↓
Store in _active_backend
    ↓
Return LocalChatModel wrapper
```

## Memory Management

### Unified Memory Architecture

Apple Silicon's unified memory enables:

1. **Zero-copy data transfer**: CPU and GPU access same memory
2. **Dynamic allocation**: Memory allocated as needed
3. **No explicit GPU memory management**: Handled by MLX framework

### Model Loading

```python
# In MlxBackend.__init__()
self._model, self._tokenizer = mlx_lm.load(model_dir)

# Model weights loaded into unified memory
# Available to both CPU and GPU automatically
```

### Unloading

```python
# In MlxBackend.unload()
del self._model
del self._tokenizer
self._model = None
self._tokenizer = None

# Python GC frees memory back to system
```

## Thread Safety

### Singleton Pattern

```python
_lock = threading.Lock()
_active_backend: Optional[LocalBackend] = None
_active_model_id: Optional[str] = None

def create_local_chat_model(model_id: str, ...):
    with _lock:
        # Only one thread can modify active backend
        if _active_model_id == model_id:
            return reuse_model()
        unload_previous()
        load_new()
```

### Async Bridging

```python
# LocalChatModel uses thread executor for async compatibility
loop = asyncio.get_running_loop()
response = await loop.run_in_executor(
    None,  # default executor
    lambda: self._backend.chat_completion(...),
)
```

## Model Format

### MLX Model Directory Structure

```
~/.copaw/models/mlx-community--Qwen3.5-4B-MLX-4bit/
├── config.json              # Model configuration
├── tokenizer.json           # Tokenizer vocabulary
├── tokenizer_config.json    # Tokenizer settings
├── model.safetensors        # Model weights (quantized)
└── special_tokens_map.json  # Special token definitions
```

### Safetensors Format

- Advantages: Memory-mapped loading, memory efficient
- Quantization: 4-bit quantization reduces memory by ~4x
- Memory-mapping: Only accessed pages loaded into RAM

## Generation Process

### Streaming Generation

```python
for response in mlx_lm.stream_generate(
    self._model,
    self._tokenizer,
    prompt=prompt,
    max_tokens=max_tokens,
    sampler=sampler,  # temp, top_p, etc.
):
    # response.text: generated text chunk
    # response.prompt_tokens: prompt length
    # response.generation_tokens: tokens generated so far
    # response.finish_reason: None until complete
    yield response
```

### Sampler Configuration

```python
from mlx_lm.sample_utils import make_sampler

sampler = make_sampler(
    temp=0.7,      # Temperature
    top_p=0.9,     # Nucleus sampling
    top_k=0,       # Disabled when 0
    min_p=0.0,     # Minimum probability
)
```

## Integration Points

### Provider System

```python
# MLX models registered in provider
PROVIDER_MLX = {
    "model_type": "mlx",
    "models": [],  # Populated from local model manifest
}

# Updated when models are downloaded/deleted
update_local_models()  # Scans manifest for MLX models
```

### CLI Integration

```bash
# Download
copaw models download <repo_id> --backend mlx

# List
copaw models list --backend mlx

# Delete
copaw models delete <model_id> --backend mlx
```

### Console Integration

```
Settings → Models → MLX provider
    ↓
Dropdown shows MLX models from manifest
    ↓
Configuration saved to config.json
    ↓
Model loaded on next agent invocation
```

## Performance Considerations

### First Load Time

- Model weights loaded from disk to unified memory
- Tokenizer initialization
- MLX compilation for Metal shaders
- **Typical**: 10-30 seconds for 4B model

### Inference Speed

- **Factors**: Model size, prompt length, max_tokens
- **Typical**: 15-30 tokens/second for 4B model
- **Bottleneck**: Memory bandwidth, not compute

### Memory Usage

- **Model weights**: ~3GB for 4B 4-bit model
- **KV cache**: Grows with sequence length
- **Peak**: Model + cache + overhead (~3.5GB)

## Error Handling

### Import Errors

```python
try:
    import mlx_lm
except ImportError:
    raise ImportError(
        "mlx-lm is required for the MLX backend. "
        "Install it with: pip install 'copaw[mlx]'"
    )
```

### Model Loading Errors

```python
# Invalid directory
raise RuntimeError(
    f"MLX model download appears incomplete — "
    f"missing files in {model_dir}: {missing}"
)

# No safetensors
raise RuntimeError(
    f"MLX model download appears incomplete — "
    f"no .safetensors files found in {model_dir}"
)
```

## Future Enhancements

Potential improvements for MLX backend:

1. **Multi-model support**: Load multiple small models simultaneously
2. **Quantization options**: Support 2-bit, 3-bit quantization
3. **LoRA adapters**: Fine-tuning without full retraining
4. **Speculative decoding**: Faster inference with draft model
5. **Batch processing**: Process multiple prompts simultaneously

## Summary

The MLX backend provides:

- **Clean architecture** with separation of concerns
- **Thread-safe** singleton model management
- **Async-compatible** via thread executor bridging
- **Memory-efficient** unified memory utilization
- **Streaming support** for responsive chat interface
- **Tool calling** through MLX's tokenizer integration

This design enables CoPaw to run local LLMs efficiently on Apple Silicon with minimal overhead and maximum flexibility.
