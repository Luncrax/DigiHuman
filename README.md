# DigiHuman - AI Virtual Human Project

DigiHuman is an AI-powered virtual human project based on the open-llm-vtuber architecture. It combines LLM (Large Language Model), ASR (Automatic Speech Recognition), TTS (Text-to-Speech), and Live2D technologies to create an interactive virtual character that can chat, speak, and display emotions.

## Features

- Real-time chat with AI assistant
- Voice input via ASR (Automatic Speech Recognition)
- Voice output via TTS (Text-to-Speech)
- Live2D character animation
- Chat history management
- WebSocket-based real-time communication
- Memory-enhanced conversations

## Architecture

The project follows the open-llm-vtuber architecture with the following components:

- **Backend**: FastAPI server with WebSocket support
- **LLM**: OpenAI-compatible interface for language models
- **ASR**: OpenAI Whisper for speech recognition
- **TTS**: OpenAI TTS for text-to-speech synthesis
- **Live2D**: Interactive 2D character models
- **Memory**: Redis-based conversation memory
- **Frontend**: HTML/CSS/JavaScript interface

## Requirements

- Python 3.8+
- Redis server
- OpenAI API key (or compatible API endpoint)
- Live2D model files (optional)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd digihuman
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env` file:
```env
LLM_API_KEY=your_openai_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo
TTS_VOICE=alloy
TTS_MODEL=tts-1
ASR_ENABLED=true
TTS_ENABLED=true
LIVE2D_ENABLED=false
LIVE2D_MODEL_PATH=live2d-models/your-model/
REDIS_URL=redis://localhost:6379
```

4. Start Redis server:
```bash
redis-server
```

## Usage

### Running the Server

Start the DigiHuman server:

```bash
python run_server.py
```

The server will start on `http://localhost:8000` by default.

### Frontend Interface

Access the frontend through the following URLs:

- Main interface: `http://localhost:8000/`
- Chat interface: `http://localhost:8000/chat.html`
- ASR demo: `http://localhost:8000/asr-demo.html`
- TTS demo: `http://localhost:8000/tts-demo.html`
- Live2D demo: `http://localhost:8000/live2d-demo.html`
- Memory interface: `http://localhost:8000/memory.html`
- Dashboard: `http://localhost:8000/dashboard.html`

## Configuration

The system can be configured through the `.env` file or environment variables:

- `LLM_API_KEY`: API key for LLM service
- `LLM_BASE_URL`: Base URL for LLM API
- `LLM_MODEL`: Default LLM model to use
- `TTS_VOICE`: Voice to use for TTS
- `TTS_MODEL`: TTS model to use
- `ASR_ENABLED`: Enable/disable ASR functionality
- `TTS_ENABLED`: Enable/disable TTS functionality
- `LIVE2D_ENABLED`: Enable/disable Live2D functionality
- `LIVE2D_MODEL_PATH`: Path to Live2D model files
- `REDIS_URL`: Redis connection URL

## Project Structure

```
digihuman/
├── backend/                 # Backend services
│   ├── api/                 # API endpoints
│   ├── asr/                 # ASR services
│   ├── core/                # Core configurations
│   ├── llm/                 # LLM services
│   ├── live2d/              # Live2D services
│   ├── memory/              # Memory services
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   ├── tts/                 # TTS services
│   ├── utils/               # Utility functions
│   ├── context_manager.py   # Context management
│   ├── history_manager.py   # Chat history management
│   ├── main.py             # Main FastAPI app
│   ├── server.py           # Server configuration
│   └── ws_handler.py       # WebSocket handler
├── frontend/               # Frontend files
├── cache/                  # Cache directory
├── live2d-models/          # Live2D model files
├── avatars/                # Avatar images
├── backgrounds/            # Background images
├── web_tool/               # Web tool files
├── run_server.py           # Server startup script
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## API Endpoints

- `GET /health`: Health check endpoint
- `WS /ws`: WebSocket endpoint for real-time communication
- `GET /`: Main frontend
- `GET /chat.html`: Chat interface
- Static file serving for all other routes

## WebSocket Messages

The WebSocket interface supports the following message types:

- `chat_message`: Text chat message
- `audio_data`: Audio data for ASR
- `text-input`: Text input from frontend
- `mic-audio-data`: Microphone audio data
- `mic-audio-end`: End of microphone audio
- `fetch-history-list`: Fetch chat history list
- `fetch-and-set-history`: Fetch and set specific history
- `create-new-history`: Create new chat history
- `delete-history`: Delete chat history
- `request_status`: Request connection status
- `live2d_update`: Live2D model updates
- `tts_request`: TTS synthesis request

## Development

To run in development mode with auto-reload:

```bash
python run_server.py
```

## License

This project is licensed under the MIT License.
