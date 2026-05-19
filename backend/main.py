import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.server import DigiHumanWebSocketServer

# Initialize the DigiHuman WebSocket Server
server = DigiHumanWebSocketServer()
app = server.app

# Clean cache on startup
server.clean_cache()



if __name__ == "__main__":
    import uvicorn
    from backend.core.config import config
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=True,
        log_level="info"
    )
