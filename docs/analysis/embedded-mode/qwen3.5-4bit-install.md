# Qwen3.5-4B-MLX-4bit Installation Guide

## Overview

Qwen3.5-4B-MLX-4bit is a 4-billion parameter model from the Qwen series, optimized for Apple Silicon using MLX framework. It offers excellent performance for both English and Chinese tasks with minimal memory usage.

## Prerequisites

- **Hardware**: Apple Silicon Mac (M1/M2/M3/M4)
- **Memory**: 6GB+ unified memory (8GB+ recommended)
- **Storage**: 4GB+ free disk space
- **Python**: 3.10-3.13
- **OS**: macOS 12.0+ (Monterey or later)

## Quick Start (Recommended)

### Using the Local Startup Script

The fastest way to get started with Qwen3.5-4B-MLX-4bit:

```bash
# Clone or navigate to CoPaw repository
cd /path/to/CoPaw

# Run the local startup script (auto-detects macOS and enables MLX)
bash scripts/run_local.sh

# Install ModelScope dependency (for faster downloads in China)
uv pip install modelscope --python .venv_local/bin/python

# Download the model from ModelScope (recommended for China users)
.venv_local/bin/copaw models download mlx-community/Qwen3.5-4B-MLX-4bit --backend mlx --source modelscope

# Start CoPaw
.venv_local/bin/copaw app
```

Then configure via Console at http://127.0.0.1:8088:
1. Settings → Models
2. Select MLX provider
3. Choose "Qwen3.5-4B-MLX-4bit" from the dropdown
4. Save configuration

## Manual Installation

### Step 1: Install CoPaw with MLX Support

```bash
# Using uv (recommended)
uv pip install 'copaw[mlx]'

# Or using pip
pip install 'copaw[mlx]'

# Verify installation
python -c "import mlx_lm; print('MLX installed successfully')"
```

### Step 2: Download Qwen3.5-4B-MLX-4bit Model

```bash
# Option A: Download from ModelScope (recommended for China users, faster)
pip install modelscope
copaw models download mlx-community/Qwen3.5-4B-MLX-4bit --backend mlx --source modelscope

# Option B: Download from HuggingFace Hub (international users)
copaw models download mlx-community/Qwen3.5-4B-MLX-4bit --backend mlx

# Verify download
copaw models local --backend mlx
```

Expected output:
```
=== Local Models (1) ===
────────────────────────────────────────────
  Qwen3.5-4B-MLX-4bit
  ID:      mlx-community/Qwen3.5-4B-MLX-4bit
  Backend: mlx
  Source:  modelscope (or huggingface)
  Size:    ~2919 MB
```

### Step 3: Configure Model

**Option A: Via Web Console**

```bash
# Start CoPaw
copaw app

# Open browser to http://127.0.0.1:8088
# Navigate to: Settings → Models → MLX provider
# Select: Qwen3.5-4B-MLX-4bit
# Click Save
```

**Option B: Via Configuration File**

```bash
# Edit config file
nano ~/.copaw/working/config.json

# Add or modify model configuration:
{
  "model": {
    "provider": "mlx",
    "model_name": "mlx-community/Qwen3.5-4B-MLX-4bit"
  }
}
```

**Option C: Via CLI**

```bash
# Set MLX as provider
copaw config set model.provider mlx

# Set model name
copaw config set model.model_name mlx-community/Qwen3.5-4B-MLX-4bit
```

## Verification

### Test the Installation

```bash
# Start CoPaw
copaw app

# In the Console chat interface, send a test message:
# "Hello, can you introduce yourself?"

# Expected response: A coherent introduction in English or Chinese
```

### Performance Check

```python
# Quick performance test (optional)
import time
from copaw.local_models import create_local_chat_model

# Load model
start = time.time()
model = create_local_chat_model("mlx-community/Qwen3.5-4B-MLX-4bit")
load_time = time.time() - start
print(f"Model loaded in {load_time:.1f}s")

# Test inference
import asyncio

async def test():
    response = await model([{"role": "user", "content": "Hello!"}])
    async for chunk in response:
        if chunk.content:
            print(chunk.content[0].text, end="", flush=True)
    print()

start = time.time()
asyncio.run(test())
inference_time = time.time() - start
print(f"\nInference completed in {inference_time:.1f}s")
```

## Expected Performance

| Metric | Expected Value |
|--------|----------------|
| **First Load Time** | 10-30 seconds |
| **Inference Speed** | ~15-30 tokens/second |
| **Memory Usage** | ~3GB unified memory |
| **Model Size** | ~3.2GB disk space |

## Configuration Options

### Recommended Settings

```json
{
  "model": {
    "provider": "mlx",
    "model_name": "mlx-community/Qwen3.5-4B-MLX-4bit",
    "config": {
      "max_tokens": 2048,
      "temp": 0.7,
      "top_p": 0.9,
      "repetition_penalty": 1.0
    }
  }
}
```

### Parameter Descriptions

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_tokens` | 2048 | Maximum tokens to generate |
| `temp` | 0.7 | Sampling temperature (0.0-1.0) |
| `top_p` | 0.9 | Nucleus sampling threshold |
| `repetition_penalty` | 1.0 | Reduce repetition (1.0=off) |

## Troubleshooting

### "Module 'mlx_lm' not found"

```bash
# Install MLX dependencies
pip install --upgrade 'copaw[mlx]'

# Or install MLX directly
pip install mlx-lm>=0.10.0
```

### "ModelScope snapshot download is required"

When downloading from ModelScope, you need to install modelscope:

```bash
# Using pip
pip install modelscope

# Using uv
uv pip install modelscope --python .venv_local/bin/python
```

### "Model not found in manifest"

```bash
# Re-download the model
copaw models download mlx-community/Qwen3.5-4B-MLX-4bit --backend mlx

# Check manifest
cat ~/.copaw/models/manifest.json
```

### Out of Memory Error

```bash
# Close other applications
# Reduce max_tokens in configuration
# Or use a smaller model (Gemma-2-2B-it-MLX)
```

### Slow Performance

- Ensure no other heavy GPU tasks are running
- Check Activity Monitor for memory pressure
- Try closing browser tabs and other apps
- Consider using a smaller model for faster responses

## Uninstall

```bash
# Delete the model
copaw models delete mlx-community/Qwen3.5-4B-MLX-4bit --backend mlx

# Remove CoPaw (optional)
pip uninstall copaw
```

## Next Steps

1. **Explore Skills**: Add custom skills to extend functionality
2. **Configure Channels**: Set up chat platforms (DingTalk, Feishu, etc.)
3. **Memory System**: Enable ReMe for conversation memory
4. **Scheduled Tasks**: Configure cron jobs for automation

## Summary

Qwen3.5-4B-MLX-4bit provides:
- **Excellent bilingual support** (English/Chinese)
- **Fast inference** on Apple Silicon
- **Low memory footprint** (~3GB)
- **Offline capability** with complete privacy

**Perfect for**: Personal assistant tasks, general chat, and light coding assistance on Apple Silicon Macs.
