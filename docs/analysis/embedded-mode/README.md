# CoPaw MLX Embedded Mode

## Overview

CoPaw's **MLX Embedded Mode** enables running local LLMs directly in-process on Apple Silicon (M1/M2/M3/M4) Macs using Apple's MLX framework. This provides the fastest possible inference with complete privacy and offline capability.

## What is MLX?

MLX is Apple's machine learning framework designed specifically for Apple Silicon. Key features:

- **Unified Memory Architecture**: GPU and CPU share the same memory, eliminating data transfer overhead
- **Metal Integration**: Leverages Apple's GPU acceleration through Metal Performance Shaders
- **Apple Silicon Optimized**: Designed from the ground up for M-series chips
- **Simple Python API**: Easy integration with Python projects

## Architecture

### Backend Implementation

```
src/copaw/local_models/
├── backends/
│   ├── base.py              # Abstract base class for all backends
│   └── mlx_backend.py       # MLX-specific implementation
├── factory.py               # Singleton factory for model instances
├── chat_model.py            # AgentScope ChatModelBase wrapper
├── manager.py               # Model download and management
└── schema.py                # Data models
```

### Data Flow

```
User Request
    ↓
CoPaw Agent (AgentScope)
    ↓
LocalChatModel (ChatModelBase interface)
    ↓
MlxBackend (in-process)
    ↓
MLX Model (unified memory)
    ↓
Metal GPU Acceleration
```

### Key Components

1. **MlxBackend** (`mlx_backend.py`)
   - Direct wrapper around `mlx-lm` library
   - Handles model loading, tokenization, and generation
   - Supports streaming responses
   - Tool calling via tokenizer's `has_tool_calling` capability

2. **LocalChatModel** (`chat_model.py`)
   - Adapts backend to AgentScope's `ChatModelBase` interface
   - Async compatibility via thread executor
   - Streaming and non-streaming modes
   - Structured output support (prompt-based for MLX)

3. **LocalModelManager** (`manager.py`)
   - Downloads models from HuggingFace Hub or ModelScope
   - Manages model manifest in `~/.copaw/models/manifest.json`
   - Handles directory-based MLX model downloads

## Installation

### Prerequisites

- Apple Silicon Mac (M1/M2/M3/M4)
- Python 3.10-3.13
- 6GB+ unified memory (8GB+ recommended for 4B models)

### Install MLX Backend

```bash
# Using pip
pip install 'copaw[mlx]'

# Using uv (recommended)
uv pip install 'copaw[mlx]'

# Or using the local startup script (auto-detects macOS)
bash scripts/run_local.sh
```

## Model Recommendations

### By Size

| Model | Parameters | VRAM/RAM | Best For |
|-------|-----------|----------|----------|
| **Gemma-2-2B-it-MLX** | 2B | ~2GB | Lightweight, fastest response |
| **Llama-3.2-3B-Instruct-4bit** | 3B | ~2GB | General use, balanced |
| **Qwen2.5-4B** | 4B | ~3GB | Better quality, multilingual |
| **Qwen3.5-4B-MLX-4bit** | 4B | ~3GB | Latest Qwen, Chinese optimized |

### By Use Case

| Use Case | Recommended Model |
|----------|-------------------|
| **General Chat (English)** | Llama-3.2-3B-Instruct-4bit |
| **General Chat (Chinese)** | Qwen3.5-4B-MLX-4bit |
| **Fastest Response** | Gemma-2-2B-it-MLX |
| **Best Quality** | Qwen3.5-4B-MLX-4bit |
| **Low Memory (4GB)** | Gemma-2-2B-it-MLX |

## Usage

### Download Model

```bash
# Install ModelScope dependency (for faster downloads in China)
pip install modelscope

# Download from ModelScope (recommended for China users)
copaw models download mlx-community/Llama-3.2-3B-Instruct-4bit --backend mlx --source modelscope
copaw models download mlx-community/Qwen3.5-4B-MLX-4bit --backend mlx --source modelscope

# Or download from HuggingFace (international users)
copaw models download mlx-community/Llama-3.2-3B-Instruct-4bit --backend mlx
copaw models download mlx-community/Qwen3.5-4B-MLX-4bit --backend mlx

# List downloaded models
copaw models local --backend mlx
```

### Configure via Console

1. Start CoPaw: `copaw app`
2. Open Console: http://127.0.0.1:8088
3. Settings → Models
4. Select MLX provider
5. Choose model from dropdown
6. Save configuration

### Configure via CLI

```bash
# Set MLX model as default
copaw config set model.provider mlx
copaw config set model.model_name mlx-community/Qwen3.5-4B-MLX-4bit
```

## Performance Tips

### Memory Optimization

```python
# In config.json or via Console settings
{
  "max_tokens": 2048,           # Reduce if memory constrained
  "temp": 0.7,                  # Temperature for sampling
  "top_p": 0.9,                 # Nucleus sampling
  "repetition_penalty": 1.0     # Reduce repetition
}
```

### Expected Performance

| Model | First Load | Inference Speed | Memory Usage |
|-------|------------|-----------------|--------------|
| 2B | 5-15s | 20-40 tok/s | ~2GB |
| 3B-4B | 10-30s | 15-30 tok/s | ~3GB |
| 7B | 20-60s | 10-20 tok/s | ~5GB |

## Comparison: MLX vs Cloud APIs

| Feature | MLX Embedded | Cloud APIs |
|---------|--------------|------------|
| **Latency** | Lowest (local) | Higher (network) |
| **Privacy** | 100% local | Data sent to API |
| **Cost** | Free | Per-token |
| **Offline** | Yes | No |
| **Setup** | One-time install | API key only |

## Troubleshooting

### Model Not Loading

```bash
# Verify model files
ls -la ~/.copaw/models/

# Check manifest
cat ~/.copaw/models/manifest.json

# Re-download if corrupted
copaw models delete <model_id> --backend mlx
copaw models download <repo_id> --backend mlx
```

### Out of Memory

- Use a smaller model (2B instead of 4B)
- Reduce `max_tokens` in configuration
- Close other memory-intensive applications

### Import Errors

```bash
# Verify MLX installation
python -c "import mlx_lm; print(mlx_lm.__version__)"

# Reinstall if needed
pip install --upgrade 'copaw[mlx]'
```

### ModelScope Download Errors

When using `--source modelscope`, ensure modelscope is installed:

```bash
pip install modelscope
```

If you get "ModelScope snapshot download is required" error, upgrade modelscope:

```bash
pip install --upgrade modelscope
```

## Summary

MLX Embedded Mode provides:
- **Fastest local inference** on Apple Silicon
- **Complete privacy** with 100% local data processing
- **Offline capability** without internet
- **Native Metal acceleration** through unified memory

**Recommended starting point**: Qwen3.5-4B-MLX-4bit for best balance of quality and performance.
