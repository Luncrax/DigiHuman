"""
DigiHuman WebSocket Server
Based on open-llm-vtuber's server.py
"""
import os
import shutil
import json
import time
import base64
import urllib.error
import urllib.request
from pathlib import Path
from fastapi import FastAPI, WebSocket
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, Response
from starlette.staticfiles import StaticFiles as StarletteStaticFiles
from pydantic import BaseModel

from backend.ws_handler import WebSocketHandler
from backend.character_config import CharacterConfig, get_character_config_store
from backend.core.config import config
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class TTSTestRequest(BaseModel):
    text: str
    mode: str = "custom_voice"
    voice: str | None = None
    emotion: str = "neutral"
    intensity: str = "low"
    instruct: str | None = None
    voice_prompt_path: str | None = None


class CharacterConfigRequest(BaseModel):
    llm_system_prompt: str = ""
    emotion_style: str = ""


# Create a custom StaticFiles class that adds CORS headers
class CORSStaticFiles(StarletteStaticFiles):
    """
    Static files handler that adds CORS headers to all responses.
    Needed because Starlette StaticFiles might bypass standard middleware.
    """

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)

        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

        if path.endswith(".js"):
            response.headers["Content-Type"] = "application/javascript"

        return response


class AvatarStaticFiles(CORSStaticFiles):
    """
    Avatar files handler with security restrictions and CORS headers
    """

    async def get_response(self, path: str, scope):
        allowed_extensions = (".jpg", ".jpeg", ".png", ".gif", ".svg")
        if not any(path.lower().endswith(ext) for ext in allowed_extensions):
            return Response("Forbidden file type", status_code=403)
        response = await super().get_response(path, scope)
        return response


class DigiHumanWebSocketServer:
    """
    API server for DigiHuman. This contains the websocket endpoint for the client, hosts the web tool, and serves static files.

    Creates and configures a FastAPI app, registers all routes
    (WebSocket, web tools, proxy) and mounts static assets with CORS.
    """

    def __init__(self):
        self.app = FastAPI(title=config.PROJECT_NAME, version=config.APP_VERSION)
        self.ws_handler = WebSocketHandler()
        self.project_root = Path(".").resolve()
        
        # Add global CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add WebSocket route using decorator (before any static files)
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            try:
                logger.info("WebSocket connection attempt received")
                # 检查 Origin 头
                origin = websocket.headers.get("origin")
                logger.info(f"WebSocket connection attempt from origin: {origin}")
                # 接受所有 WebSocket 连接
                await websocket.accept()
                logger.info("WebSocket connection accepted")
                # 调用 WebSocket 处理器
                requested_client_uid = websocket.query_params.get("client_id")
                await self.ws_handler.handle_new_connection(
                    websocket,
                    requested_client_uid=requested_client_uid,
                )
                logger.info("WebSocket connection established successfully")
                await self.ws_handler.handle_messages(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await websocket.close()
                except:
                    pass

        # Add health check endpoint SECOND (before any static files)
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "message": "DigiHuman WebSocket Server is running"}

        @self.app.get("/health/detail")
        async def health_detail():
            return await self.get_health_detail()

        @self.app.post("/api/tts/test")
        async def tts_test(payload: TTSTestRequest):
            if not config.TTS_ENABLED or not self.ws_handler.tts_service:
                return {
                    "status": "error",
                    "message": "TTS service is not enabled.",
                }

            text = (payload.text or "").strip()
            if not text:
                return {
                    "status": "error",
                    "message": "Text is required.",
                }

            started_at = time.perf_counter()
            try:
                audio_bytes = await self.ws_handler.tts_service.async_synthesize(
                    text,
                    voice=payload.voice or config.TTS_VOICE,
                    model=payload.mode,
                    emotion=payload.emotion,
                    intensity=payload.intensity,
                    instruct=payload.instruct,
                    voice_prompt_path=payload.voice_prompt_path or None,
                )
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

                return {
                    "status": "ok",
                    "mode": payload.mode,
                    "voice": payload.voice or config.TTS_VOICE,
                    "emotion": payload.emotion,
                    "intensity": payload.intensity,
                    "voice_prompt_path": payload.voice_prompt_path or None,
                    "elapsed_ms": elapsed_ms,
                    "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
                    "audio_format": "audio/wav",
                    "audio_size": len(audio_bytes),
                }
            except Exception as exc:
                return {
                    "status": "error",
                    "message": str(exc),
                    "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 2),
                    "mode": payload.mode,
                    "voice_prompt_path": payload.voice_prompt_path or None,
                }

        @self.app.get("/api/character-config")
        async def get_character_config_api():
            return {
                "status": "ok",
                "config": get_character_config_store().to_dict(),
            }

        @self.app.post("/api/character-config")
        async def save_character_config_api(payload: CharacterConfigRequest):
            saved = get_character_config_store().save(
                CharacterConfig(
                    llm_system_prompt=(payload.llm_system_prompt or "").strip(),
                    emotion_style=(payload.emotion_style or "").strip(),
                )
            )
            return {
                "status": "ok",
                "config": {
                    "llm_system_prompt": saved.llm_system_prompt,
                    "emotion_style": saved.emotion_style,
                },
            }

        @self.app.get("/api/session-overview")
        async def session_overview(client_id: str = "", current_history_uid: str = ""):
            safe_client_id = (client_id or "").strip()
            safe_history_uid = (current_history_uid or "").strip()

            histories = self.ws_handler.history_manager.get_history_list(safe_client_id) if safe_client_id else []
            current_history = (
                self.ws_handler.history_manager.get_history(safe_client_id, safe_history_uid)
                if safe_client_id and safe_history_uid
                else []
            )

            return {
                "status": "ok",
                "client_id": safe_client_id,
                "current_history_uid": safe_history_uid,
                "history_count": len(histories),
                "current_history_message_count": len(current_history),
                "histories": histories,
                "current_history": current_history,
            }

        # Mount cache directory (to ensure audio file access)
        if not os.path.exists("cache"):
            os.makedirs("cache")
        self.app.mount(
            "/cache",
            CORSStaticFiles(directory="cache"),
            name="cache",
        )

        # Mount static files with CORS-enabled handlers
        self.app.mount(
            "/live2d-models",
            CORSStaticFiles(directory="live2d-models"),
            name="live2d-models",
        )
        self.app.mount(
            "/bg",
            CORSStaticFiles(directory="backgrounds"),
            name="backgrounds",
        )
        self.app.mount(
            "/avatars",
            AvatarStaticFiles(directory="avatars"),
            name="avatars",
        )

        # Mount web tool directory separately from frontend
        self.app.mount(
            "/web-tool",
            CORSStaticFiles(directory="web_tool", html=True),
            name="web_tool",
        )

        # Serve the built frontend through HTTP routes instead of mounting it at "/".
        # A root StaticFiles mount also intercepts websocket scopes and causes `/ws`
        # to fail with HTTP 403 before our websocket route can run.
        self.frontend_dist = Path("frontend/dist").resolve()
        self.frontend_index = self.frontend_dist / "index.html"

        @self.app.get("/")
        async def frontend_index():
            if self.frontend_index.exists():
                return FileResponse(self.frontend_index)
            return {
                "status": "frontend_not_built",
                "message": "frontend/dist is missing. Run `npm run build` in frontend/ or use the Vite dev server on port 3000.",
            }

        @self.app.get("/{full_path:path}")
        async def frontend_assets(full_path: str):
            if not self.frontend_dist.exists():
                return Response("Frontend build not found", status_code=404)

            requested = (self.frontend_dist / full_path).resolve()
            try:
                requested.relative_to(self.frontend_dist)
            except ValueError:
                return Response("Forbidden", status_code=403)

            if requested.is_file():
                return FileResponse(requested)

            if self.frontend_index.exists():
                return FileResponse(self.frontend_index)

            return Response("Frontend build not found", status_code=404)

    @staticmethod
    def clean_cache():
        """Clean the cache directory by removing and recreating it."""
        cache_dir = "cache"
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
        os.makedirs(cache_dir, exist_ok=True)

    async def get_health_detail(self):
        llm_status = self._check_llm_status()
        qwen_status = await self._check_qwen_status()
        asr_status = self._check_asr_status()
        live2d_status = self._check_live2d_status()
        websocket_status = self._check_websocket_status()

        services = {
            "websocket": websocket_status,
            "llm": llm_status,
            "qwen_tts": qwen_status,
            "asr": asr_status,
            "live2d": live2d_status,
        }

        overall = "healthy"
        if any(service["status"] == "error" for service in services.values()):
            overall = "degraded"
        elif any(service["status"] == "warning" for service in services.values()):
            overall = "warning"

        return {
            "status": overall,
            "app": {
                "name": config.APP_NAME,
                "version": config.APP_VERSION,
                "host": config.HOST,
                "port": config.PORT,
            },
            "services": services,
        }

    def _check_llm_status(self):
        configured = bool(config.LLM_MODEL and config.LLM_BASE_URL and config.LLM_API_KEY)
        return {
            "status": "healthy" if configured else "error",
            "label": "LLM",
            "summary": "LLM 配置完整，可用于对话与情绪分析。" if configured else "LLM 配置不完整，无法正常调用模型。",
            "details": {
                "model": config.LLM_MODEL,
                "base_url": config.LLM_BASE_URL,
                "api_key_configured": bool(config.LLM_API_KEY),
                "probe": "configuration",
            },
        }

    async def _check_qwen_status(self):
        if not config.TTS_ENABLED or config.TTS_SERVICE != "qwen3_tts":
            return {
                "status": "warning",
                "label": "Qwen3-TTS",
                "summary": "Qwen3-TTS 当前未作为主 TTS 服务启用。",
                "details": {
                    "enabled": config.TTS_ENABLED,
                    "tts_service": config.TTS_SERVICE,
                    "server_url": config.QWEN3_TTS_SERVER_URL,
                },
            }

        def probe():
            req = urllib.request.Request(
                url=f"{config.QWEN3_TTS_SERVER_URL.rstrip('/')}/health",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))

        try:
            result = await __import__("asyncio").to_thread(probe)
            loaded_models = result.get("loaded_models", [])
            return {
                "status": "healthy",
                "label": "Qwen3-TTS",
                "summary": "Qwen3-TTS 服务在线，可进行语音合成。",
                "details": {
                    "server_url": config.QWEN3_TTS_SERVER_URL,
                    "tts_model": config.TTS_MODEL,
                    "speaker": config.QWEN3_TTS_CUSTOM_SPEAKER,
                    "loaded_models": loaded_models,
                },
            }
        except urllib.error.URLError as exc:
            return {
                "status": "error",
                "label": "Qwen3-TTS",
                "summary": "Qwen3-TTS 服务不可达，请确认 WSL 服务已启动。",
                "details": {
                    "server_url": config.QWEN3_TTS_SERVER_URL,
                    "error": str(exc.reason),
                },
            }
        except Exception as exc:
            return {
                "status": "error",
                "label": "Qwen3-TTS",
                "summary": "Qwen3-TTS 健康检查失败。",
                "details": {
                    "server_url": config.QWEN3_TTS_SERVER_URL,
                    "error": str(exc),
                },
            }

    def _check_asr_status(self):
        if not config.ASR_ENABLED:
            return {
                "status": "warning",
                "label": "ASR",
                "summary": "ASR 未启用，语音输入不可用。",
                "details": {
                    "enabled": False,
                    "service": config.ASR_SERVICE,
                },
            }

        service = self.ws_handler.asr_service
        available = getattr(service, "available", True) if service else False
        service_name = type(service).__name__ if service else "None"
        status = "healthy" if available else "warning"
        summary = "ASR 服务已就绪。" if available else "ASR 服务已加载，但模型或依赖可能未准备完成。"

        return {
            "status": status,
            "label": "ASR",
            "summary": summary,
            "details": {
                "enabled": True,
                "service": config.ASR_SERVICE,
                "implementation": service_name,
                "available": available,
            },
        }

    def _check_live2d_status(self):
        frontend_model = self.project_root / "frontend" / "public" / "live2d_models" / "Mao" / "Mao.model3.json"
        cubism_core = self.project_root / "frontend" / "public" / "vendor" / "live2d" / "live2dcubismcore.min.js"
        backend_enabled = config.LIVE2D_ENABLED and bool(self.ws_handler.live2d_model)
        frontend_ready = frontend_model.exists() and cubism_core.exists()

        if backend_enabled and frontend_ready:
            status = "healthy"
            summary = "Live2D 前后端资源已就绪。"
        elif frontend_ready:
            status = "warning"
            summary = "Live2D 前端资源已就绪，但后端本地 Live2D 模型未启用。"
        else:
            status = "error"
            summary = "Live2D 关键资源缺失。"

        return {
            "status": status,
            "label": "Live2D",
            "summary": summary,
            "details": {
                "backend_enabled": bool(config.LIVE2D_ENABLED),
                "backend_model_loaded": bool(self.ws_handler.live2d_model),
                "frontend_model_exists": frontend_model.exists(),
                "cubism_core_exists": cubism_core.exists(),
                "model_path": str(frontend_model),
            },
        }

    def _check_websocket_status(self):
        return {
            "status": "healthy",
            "label": "WebSocket",
            "summary": "WebSocket 服务已启动。",
            "details": {
                "endpoint": f"ws://127.0.0.1:{config.PORT}/ws",
                "active_connections": len(self.ws_handler.client_connections),
            },
        }
