# Backend Overview

The backend is a FastAPI service for the DigiHuman assistant. Its main runtime
entry is `backend.main:app`, which currently builds the app through
`DigiHumanWebSocketServer` in `backend/server.py`.

## Important Runtime Flow

1. Frontend connects to `/ws`.
2. `backend/ws_handler.py` receives messages and owns the conversation pipeline.
3. The pipeline can call ASR, LLM, memory, emotion analysis, TTS, and Live2D.
4. HTTP APIs under `/api/*` support login, settings, TTS testing, database
   inspection, session overview, and study assistant actions.

## Directory Guide

- `api`: APIRouter-style endpoints. Some files are legacy and are not currently
  mounted by `server.py`.
- `asr`: speech-to-text implementations.
- `core`: configuration.
- `emotion`: emotion analysis and control.
- `langchain`: LLM orchestration, memory, chains, and tools.
- `live2d`: avatar model abstractions.
- `llm`: older/simple LLM service wrapper.
- `models`: Pydantic schemas and shared data models.
- `prompts`: prompt loading.
- `study_assistant`: study planning, knowledge import, and vector search.
- `tts`: text-to-speech implementations.
- `utils`: logging and helper utilities.

## Refactor Target

`server.py` is doing too much. The next good maintenance step is to split route
registration into focused modules while keeping the public URL paths unchanged.
