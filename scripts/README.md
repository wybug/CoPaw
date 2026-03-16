# Scripts

Run from **repo root**.

## Initialize CoPaw

```bash
bash scripts/init.sh [OPTIONS]
```

- Initializes CoPaw configuration in a clean, consistent way
- Creates `~/.copaw/` directory structure
- Generates `config.json` with default settings
- Creates `working.secret/` for sensitive data
- Sets up model provider configuration
- Verifies installation

**Options:**
- `-m, --mode MODE`: Init mode (`defaults`, `interactive`, `minimal`)
- `--no-accept-security`: Require manual confirmation for security prompts
- `--skip-working-secret`: Skip creating working.secret directory
- `--no-verify`: Skip verification after initialization
- `-h, --help`: Show help

**Examples:**
```bash
bash scripts/init.sh                          # Initialize with defaults
bash scripts/init.sh --mode interactive       # Interactive setup
bash scripts/init.sh --mode minimal           # Minimal config
```

**Note:** This is the recommended way to initialize CoPaw after installation to avoid configuration confusion.

## Run local testing

```bash
bash scripts/run_local.sh [OPTIONS] [--] [copaw_options]
```

- Quick start for local testing and development
- Creates isolated virtual environment (`.venv/`)
- Installs CoPaw in editable mode
- Auto-runs initialization on first use

**Options:**
- `--backend BACKEND`: Local model backend (`mlx`, `llamacpp`, `none`)
- `--enterprise`: Enable enterprise mode
- `--no-mlx`: Disable mlx-lm (legacy)
- `--reinit`: Reinitialize environment
- `--python VER`: Specify Python version (default: 3.12)

**Examples:**
```bash
bash scripts/run_local.sh                      # Start with defaults
bash scripts/run_local.sh --backend mlx        # Force MLX backend
bash scripts/run_local.sh -- --port 9000       # Custom port
```

## Build wheel (with latest console)

```bash
bash scripts/wheel_build.sh
```

- Builds the console frontend (`console/`), copies `console/dist` to `src/copaw/console/dist`, then builds the wheel. Output: `dist/*.whl`.

## Build website

```bash
bash scripts/website_build.sh
```

- Installs dependencies (pnpm or npm) and runs the Vite build. Output: `website/dist/`.

## Build Docker image

```bash
bash scripts/docker_build.sh [IMAGE_TAG] [EXTRA_ARGS...]
```

- Default tag: `copaw:latest`. Uses `deploy/Dockerfile` (multi-stage: builds console then Python app).
- Example: `bash scripts/docker_build.sh myreg/copaw:v1 --no-cache`.

## Run Test

```bash
# Run all tests
python scripts/run_tests.py

# Run all unit tests
python scripts/run_tests.py -u

# Run unit tests for a specific module
python scripts/run_tests.py -u providers

# Run integration tests
python scripts/run_tests.py -i

# Run all tests and generate a coverage report
python scripts/run_tests.py -a -c

# Run tests in parallel (requires pytest-xdist)
python scripts/run_tests.py -p

# Show help
python scripts/run_tests.py -h
```