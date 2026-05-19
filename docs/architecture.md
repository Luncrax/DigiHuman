# DigiHuman Architecture Notes

This project is a virtual human assistant with a Vue frontend and a FastAPI
backend. The runtime path is centered on WebSocket chat, speech input/output,
memory, emotion analysis, Live2D state, and the study assistant knowledge base.

## Runtime Entry Points

- `run_server.py` starts the backend with Uvicorn and loads `backend.main:app`.
- `start_all.py` starts both backend and frontend in separate Windows consoles.
- `backend/main.py` creates `DigiHumanWebSocketServer` and exposes its FastAPI app.
- `frontend/src/main.js` starts the Vue app.
- `frontend/src/router/index.js` defines frontend pages and login guards.

## Backend Map

- `backend/server.py`
  - Owns FastAPI app creation, middleware, HTTP routes, static mounts, frontend
    fallback routes, and health checks.
  - This is the highest-priority refactor target because it mixes too many
    responsibilities in one file.
- `backend/ws_handler.py`
  - Owns the real-time chat pipeline over `/ws`.
  - Coordinates ASR, LLM, memory, emotion analysis, TTS, and Live2D commands.
- `backend/core`
  - App configuration and environment variable parsing.
- `backend/auth.py` and `backend/sqlite_store.py`
  - Authentication, token/session persistence, user records, chat history, and
    local SQLite storage.
- `backend/langchain`
  - LLM orchestration, conversation chains, memory adapters, and tool wrappers.
- `backend/asr`
  - Speech-to-text implementations. Vosk is local/offline; Whisper uses OpenAI.
- `backend/tts`
  - Text-to-speech implementations. Edge TTS is the default lightweight path;
    Qwen3 TTS and OpenAI TTS are available as alternatives.
- `backend/emotion`
  - Emotion classification and mapping from dialogue state to avatar state.
- `backend/live2d`
  - Backend-side Live2D model abstractions and emotion-to-expression mapping.
- `backend/study_assistant`
  - Study planning, knowledge import, embedding, and Milvus/fallback search.
- `backend/api`
  - Older APIRouter-style endpoints. These are not currently mounted by
    `backend/server.py`, so treat them as legacy or staging code until routed.
- `backend/services` and `backend/memory`
  - Currently empty except caches. Either fill them as stable service boundaries
    or remove them after confirming no imports depend on them.
- `backend/models`
  - Pydantic schemas and shared request/response models.
- `backend/prompts`
  - Prompt loading utilities.
- `backend/utils`
  - Cross-cutting helpers such as logging and transforms.

## Frontend Map

- `frontend/src/views`
  - Page-level Vue screens: chat, dashboard, memory, database, settings,
    character config, login, and study assistant.
- `frontend/src/components`
  - Reusable UI and avatar components.
- `frontend/src/composables`
  - Shared browser-side logic for auth, theme, health detail, audio recording,
    and audio playback.
- `frontend/src/lib/live2d`
  - Live2D/Pixi integration.
- `frontend/public`
  - Static assets that Vite serves directly, including Live2D models and vendor
    runtime files.
- `frontend/dist`
  - Built frontend output. This should be treated as generated.

## Data And Runtime State

- `data`
  - Local SQLite database and character config data.
- `chat_memory`
  - JSON conversation memory files.
- `models`
  - Local ASR/model assets, currently Vosk.
- `study_assets`
  - User/imported study knowledge and music files.
- `logs`
  - Runtime logs.
- `backups`
  - Exported chat history and backups.

## Recommended Refactor Order

1. Split `backend/server.py` into focused route modules.
   - `backend/api/health.py`
   - `backend/api/auth.py`
   - `backend/api/tts.py`
   - `backend/api/study_assistant.py`
   - `backend/api/character.py`
   - `backend/api/debug.py`
   - `backend/api/session.py`
   - Keep static/frontend mounting in a small app setup module.
2. Introduce `backend/app.py` or `backend/factory.py`.
   - Provide `create_app()` and keep `backend/main.py` almost empty.
3. Move request models out of `server.py`.
   - Place API payload models in `backend/models/api.py` or near each route.
4. Decide the fate of legacy `backend/api/chat.py` and `memory_chat.py`.
   - Either mount and test them or remove them to avoid confusing future work.
5. Normalize human-facing Chinese strings.
   - Several strings are mojibake. Fixing them will make logs and API responses
     easier to understand.
6. Add smoke tests around app startup and core routes before deeper refactors.
   - At minimum: import `backend.main:app`, call `/health`, and verify route
     registration.

## Maintenance Rules

- Keep route files thin. Route handlers should validate/authenticate, call a
  service, and format a response.
- Keep long-running orchestration in service classes, not in route modules.
- Avoid importing optional heavy services at module import time when possible.
  Lazy-load ASR/TTS/model code so local development and tests start quickly.
- Treat `frontend/dist`, logs, caches, databases, and model files as generated or
  local runtime state.
- Keep `pyproject.toml` as the source of truth for Python dependencies. If
  `requirements.txt` remains, update it together with `pyproject.toml`.
