# Repository Guidelines

## Project Structure & Module Organization

- `main.py`: FastAPI app entrypoint; wires dependencies and mounts routers.
- `routers/`: HTTP/WebSocket endpoints.
  - `process.py`: `POST /api/process` starts a background generation task.
  - `websocket.py`: `GET /ws/{user_id}` streams results; accepts `{"type":"cancel"}`.
  - `cancel.py`: `POST /api/cancel` cancels an in-flight request.
- `services/`: core logic.
  - `agent_service.py`: Agno + DeepSeek model integration (streaming).
  - `connection_manager.py`: in-memory `user_id -> WebSocket` connection map (single-process).
  - `request_registry.py`: in-memory active request + cancel events.
  - `prompt_loader.py`: loads `config/prompts.yaml`.
- `config/prompts.yaml`: prompt templates keyed by `buttonId` and `roleId`.
- `app/`: desktop tray wrapper (service lifecycle, config, autostart, packaging entrypoint).
- `tests/`: pytest suite (`test_*.py`).
- `docs/plans/`: design and implementation notes.

## Build, Test, and Development Commands

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
pytest -v
```

Notes:
- This service is designed for an MVP **single machine / single worker** (`--workers 1`). In-memory connection/routing will not work across multiple workers/instances.
- Streaming protocol uses `requestId`; see `docs/plans/2026-02-08-agent-service-design.md`.

## Coding Style & Naming Conventions

- Python: 4-space indentation, type hints preferred, `async`/`await` for I/O paths.
- Pydantic models: `PascalCase`; request fields use the external API shape (`buttonId`, `roleId`, `userId`).
- Keep changes small and focused; update `config/prompts.yaml` and tests together when adding new buttons/roles.

## Testing Guidelines

- Framework: `pytest` + `pytest-asyncio` (`pytest.ini` sets `asyncio_mode=auto`).
- Naming: tests live in `tests/test_*.py`, functions `test_*`.
- Add/adjust tests for any router behavior changes (status codes, payload schema, cancellation, streaming messages).

## Commit & Pull Request Guidelines

- Commit messages follow a lightweight Conventional Commits style seen in history:
  - Examples: `feat: add cancel router for request cancellation`, `test: add integration tests for full flow`.
- PRs should include:
  - What changed and why, how to run (`uvicorn ...`, `pytest -v`), and any API/protocol changes (update `docs/` when needed).

## Security & Configuration Tips

- Do not commit secrets. In dev, DeepSeek credentials may be read from environment (`DEEPSEEK_API_KEY`) / `.env` (see `.env.example`). In the desktop tray app, the key can be set via tray menu and is persisted to an app-data `settings.json`.
- The agent stores memory in a local SQLite file (`agent_memory.db` by default).
