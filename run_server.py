"""
DigiHuman Server Startup Script
===============================

This script starts the DigiHuman WebSocket server with proper configuration
based on open-llm-vtuber architecture.
"""

import uvicorn
import sys
import os
from backend.core.config import config

def main():
    """Main function to start the DigiHuman server."""
    print("Starting DigiHuman WebSocket Server...")
    print(f"App Version: {config.APP_VERSION}")
    print(f"Project Name: {config.PROJECT_NAME}")
    print(f"API Version: {config.API_V1_STR}")
    print(f"Backend CORS Origins: {config.backend_cors_origins_list}")
    print("-" * 50)
    
    # Start the server using uvicorn
    uvicorn.run(
        "backend.main:app",  # Use the app from backend/main.py
        host=config.HOST,    # Use configured host
        port=config.PORT,    # Use configured port
        reload=True,         # Enable auto-reload for development
        log_level="info"     # Set log level
    )

if __name__ == "__main__":
    main()
