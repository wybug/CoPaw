# MLX Backend Quick Reference

## Installation

```bash
# Quick install (macOS only)
bash scripts/run_local.sh

# Manual install
pip install 'copaw[mlx]'
```

## Available Models

### 2B Models (4GB+ RAM)

| Model | ID | Size |
|-------|-----|------|
| Gemma 2 2B | `mlx-community/gemma-2-2b-it` | ~2GB |
| | `mlx-community/gemma-2-2b-it-4bit` | ~1.5GB |

### 3B-4B Models (6GB+ RAM)

| Model | ID | Size |
|-------|-----|------|
| Llama 3.2 3B | `mlx-community/Llama-3.2-3B-Instruct-4bit` | ~2GB |
| Qwen 2.5 4B | `mlx-community/Qwen2.5-4B` | ~3GB |
| Qwen 3.5 4B | `mlx-community/Qwen3.5-4B-MLX-4bit` | ~3GB |

## Download Models

```bash
# Install ModelScope dependency (for faster downloads in China)
pip install modelscope

# Download from ModelScope (recommended for China)
copaw models download mlx-community/Llama-3.2-3B-Instruct-4bit --backend mlx --source modelscope
copaw models download mlx-community/Qwen3.5-4B-MLX-4bit --backend mlx --source modelscope

# Or download from HuggingFace (international users)
copaw models download mlx-community/Llama-3.2-3B-Instruct-4bit --backend mlx
copaw models download mlx-community/Qwen3.5-4B-MLX-4bit --backend mlx

# List downloaded models
copaw models local --backend mlx

# Delete a model
copaw models remove-local mlx-community/Qwen3.5-4B-MLX-4bit
```

## Configuration

### Via Console

1. Open http://127.0.0.1:8088
2. Settings → Models
3. Select MLX provider
4. Choose model from dropdown
5. Configure parameters:
   - `max_tokens`: 2048 (output length)
   - `temp`: 0.7 (creativity)
   - `top_p`: 0.9 (sampling)
6. Save

### Via Config File

```json
{
  "model": {
    "provider": "mlx",
    "model_name": "mlx-community/Qwen3.5-4B-MLX-4bit",
    "config": {
      "max_tokens": 2048,
      "temp": 0.7,
      "top_p": 0.9
    }
  }
}
```

### Via CLI

```bash
copaw config set model.provider mlx
copaw config set model.model_name mlx-community/Qwen3.5-4B-MLX-4bit
```

## Model Selection Guide

| Need | Recommended Model |
|------|-------------------|
| Fastest response | `gemma-2-2b-it-4bit` |
| English chat | `Llama-3.2-3B-Instruct-4bit` |
| Chinese chat | `Qwen3.5-4B-MLX-4bit` |
| Low memory (4GB) | `gemma-2-2b-it` |
| Best quality | `Qwen3.5-4B-MLX-4bit` |

## File Locations

| Location | Path |
|----------|------|
| Models | `~/.copaw/models/` |
| Manifest | `~/.copaw/models/manifest.json` |
| Config | `~/.copaw/working/config.json` |
| Secrets | `~/.copaw/working.secret/` |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Module not found | `pip install 'copaw[mlx]'` |
| Model not found | `copaw models download <id> --backend mlx` |
| Out of memory | Use smaller model or reduce `max_tokens` |
| Slow response | Check Activity Monitor for memory pressure |

## Performance Expectations

| Model Size | Load Time | Speed | Memory |
|------------|-----------|-------|--------|
| 2B | 5-15s | 20-40 tok/s | ~2GB |
| 3B | 10-30s | 15-30 tok/s | ~2GB |
| 4B | 10-30s | 15-30 tok/s | ~3GB |

## Quick Test

```bash
# Start CoPaw
copaw app

# Test in Console chat
"Hello, introduce yourself in one sentence."

# Expected: Coherent response within 5-10 seconds
```

## Verification Commands

```bash
# Check MLX installation
python -c "import mlx_lm; print(mlx_lm.__version__)"

# Verify model files
ls -la ~/.copaw/models/

# Check manifest
cat ~/.copaw/models/manifest.json | jq .

# Test model loading
copaw models list --backend mlx
```

## Common Issues & Solutions

### "mlx_lm not found"
```bash
pip install --upgrade 'copaw[mlx]'
```

### "Model not in manifest"
```bash
copaw models download <model_id> --backend mlx
```

### Out of memory
```json
{
  "model": {
    "config": {
      "max_tokens": 1024
    }
  }
}
```

### Slow first load
- Normal behavior (10-30s)
- Subsequent loads faster if model cached

## Advanced Usage

### Python API

```python
from copaw.local_models import create_local_chat_model
import asyncio

# Create model
model = create_local_chat_model(
    "mlx-community/Qwen3.5-4B-MLX-4bit",
    stream=True
)

# Generate response
async def chat():
    response = await model([
        {"role": "user", "content": "Hello!"}
    ])
    async for chunk in response:
        if chunk.content:
            print(chunk.content[0].text, end="")

asyncio.run(chat())
```

### Custom Parameters

```python
model = create_local_chat_model(
    model_id="mlx-community/Qwen3.5-4B-MLX-4bit",
    backend_kwargs={
        "max_tokens": 4096,
    },
    generate_kwargs={
        "temp": 0.5,
        "top_p": 0.95,
    }
)
```

## Resources

- **MLX Documentation**: https://ml-explore.github.io/mlx/
- **mlx-lm GitHub**: https://github.com/ml-explore/mlx-examples
- **HuggingFace MLX Community**: https://huggingface.co/mlx-community
- **CoPaw Documentation**: See main README.md
