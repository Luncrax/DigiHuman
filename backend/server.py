"""
DigiHuman WebSocket Server
Based on open-llm-vtuber's server.py
"""
import os
import shutil
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.staticfiles import StaticFiles as StarletteStaticFiles

from backend.ws_handler import WebSocketHandler
from backend.core.config import config
from backend.utils.logger import get_logger

logger = get_logger(__name__)


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
        
        # Add global CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add WebSocket route FIRST (before any static files)
        async def websocket_endpoint(websocket):
            try:
                logger.info("WebSocket connection attempt received")
                # 检查 Origin 头
                origin = websocket.headers.get("origin")
                logger.info(f"WebSocket connection attempt from origin: {origin}")
                # 接受所有 WebSocket 连接
                await websocket.accept()
                logger.info("WebSocket connection accepted")
                # 调用 WebSocket 处理器
                await self.ws_handler.handle_new_connection(websocket)
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
        
        # Register WebSocket route
        self.app.add_websocket_route("/ws", websocket_endpoint)

        # Add health check endpoint SECOND (before any static files)
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "message": "DigiHuman WebSocket Server is running"}

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

        # Mount main frontend last (as catch-all)
        self.app.mount(
            "/",
            CORSStaticFiles(directory="frontend/dist", html=True),
            name="frontend",
        )

    @staticmethod
    def clean_cache():
        """Clean the cache directory by removing and recreating it."""
        cache_dir = "cache"
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
        os.makedirs(cache_dir, exist_ok=True)
