# Shadowrocket Config Telegram Updater

Telegram bot to manage a Shadowrocket rules file in a GitHub repository. The bot lets authorized users view, add, delete, and normalize rules via Telegram; changes are committed to GitHub with conflict handling and Prometheus metrics.

## Quick Start

1. Create env file and install deps
   - `make env`
   - `make deps-test`  (creates uv-managed .venv for Python 3.13 and installs test extras)
2. Fill `.env` with required tokens (see below).
3. Run the bot
   - Normal: `make run`
   - Verbose dev logs: `make dev`

## Directory Layout

- `bot/`
  - `main.py`: entrypoint; loads settings, logging, metrics; wires aiogram v3 Dispatcher, middlewares, and routers.
  - `handlers/`: routers for menu, view, add, delete, normalize flows.
  - `services/`: `GitHubFileStore` (GitHub Contents API client), `rules_file` parser/renderer.
  - `middlewares/`: structured logging and access control by Telegram user IDs.
  - `validators/`: domain, IPv4/CIDR, and keyword normalization.
  - `metrics.py`: Prometheus counters/histograms and exporter startup.
- `tests/`: unit, integration (mocked HTTP), and e2e-style message flow tests.
- `Makefile`, `pyproject.toml`, `uv.lock`, `Dockerfile`.

## Configuration

Configure via environment variables (see `.env.example`):

- Required: `BOT_TOKEN`, `GITHUB_TOKEN`
- GitHub target: `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_PATH`, `GITHUB_BRANCH`
- Access control (comma-separated Telegram user IDs): `ALLOWED_USERS`
- Logging: `LOG_LEVEL` (e.g., DEBUG), `LOG_JSON` (true/false)
- Prometheus metrics bind: `METRICS_ADDR` (default `0.0.0.0:9123`)

## Makefile Commands

- Setup
  - `make env` — create `.env` from template
  - `make deps` — install runtime deps
  - `make deps-test` — install runtime + test deps
  - `make lock` — update `uv.lock`
- Run
  - `make run` — start the bot
  - `make dev` — start with debug logs
- Test
  - `make test-unit` — unit tests
  - `make test-integration` — tests marked `integration`
  - `make test-e2e` — tests marked `e2e`
  - `make test-all` — run all test suites
  - `make coverage` — coverage for `bot/`
- Maintenance
  - `make clean` — remove `.venv` and caches

Examples:
- Run a single test module: `uv run --python 3.13 pytest tests/unit/test_rules_file.py`
- Run a single test function: `uv run --python 3.13 pytest tests/unit/test_rules_file.py::test_parse_and_list_rules`
- Filter by name: `uv run --python 3.13 pytest -k "add_rule" tests/unit`

## Observability

- Prometheus metrics exported at `METRICS_ADDR` (default `0.0.0.0:9123`).
- Key metrics include GitHub fetch/commit histograms and counters for rule operations and input validity.

## Docker (optional)

- Build: `docker build -t shadowrocket-bot .`
- Run: `docker run --rm --env-file .env -p 9123:9123 shadowrocket-bot`
