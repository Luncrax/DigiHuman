"""
WebSocket handler for DigiHuman project
Based on open-llm-vtuber's websocket_handler.py
"""
import asyncio
import json
import uuid
from typing import Dict, Callable, Optional
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from backend.langchain.models.llm_service import LangChainLLMService
from backend.langchain.memory.memory_manager import LangChainMemoryManager
from backend.langchain.services.dialogue_service import LangChainDialogueService
from backend.core.config import config
from backend.asr.openai_whisper_asr import OpenAIWhisperASR
from backend.tts.openai_tts import OpenAITTS
from backend.live2d.live2d_model import Live2DModel, Live2DModelConfig
from backend.history_manager import HistoryManager
from backend.context_manager import ContextManager


class WebSocketHandler:
    """Handles WebSocket connections and message routing"""
    
    def __init__(self):
        """Initialize the WebSocket handler"""
        self.client_connections: Dict[str, WebSocket] = {}
        self.client_contexts: Dict[str, ContextManager] = {}
        self.history_manager = HistoryManager()
        self.current_tasks: Dict[str, asyncio.Task] = {}
        self.received_data_buffers: Dict[str, list] = {}
        
        # Initialize services
        self.llm_service = LangChainLLMService()
        self.memory_manager = LangChainMemoryManager()
        self.dialogue_service = LangChainDialogueService()
        self.asr_service = OpenAIWhisperASR() if config.ASR_ENABLED else None
        self.tts_service = OpenAITTS() if config.TTS_ENABLED else None
        self.live2d_model = None
        if config.LIVE2D_ENABLED and config.LIVE2D_MODEL_PATH:
            try:
                live2d_config = Live2DModelConfig(
                    model_path=config.LIVE2D_MODEL_PATH,
                    motion_path=config.LIVE2D_MOTION_PATH,
                    expression_path=config.LIVE2D_EXPRESSION_PATH,
                    physics_path=config.LIVE2D_PHYSICS_PATH,
                    pose_path=config.LIVE2D_POSE_PATH
                )
                self.live2d_model = Live2DModel(live2d_config)
            except Exception as e:
                logger.error(f"Failed to initialize Live2D model: {e}")
    
    async def handle_new_connection(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        client_uid = str(uuid.uuid4())
        self.client_connections[client_uid] = websocket
        logger.info(f"New WebSocket connection established: {client_uid}")
        
        # Initialize client context
        context_manager = ContextManager()
        await context_manager.initialize_context(client_uid)
        self.client_contexts[client_uid] = context_manager
        
        # Initialize audio buffer for this client
        self.received_data_buffers[client_uid] = []
        
        # Send welcome message
        await websocket.send_text(
            json.dumps({
                "type": "connection_established",
                "message": "Connected to DigiHuman WebSocket server",
                "client_id": client_uid
            })
        )
    
    async def handle_messages(self, websocket: WebSocket):
        """Handle ongoing WebSocket communication"""
        # Find the client_uid for this websocket
        client_uid = None
        for uid, ws in self.client_connections.items():
            if ws == websocket:
                client_uid = uid
                break
        
        if not client_uid:
            logger.error("Could not find client UID for websocket")
            return

        try:
            while True:
                try:
                    data = await websocket.receive_json()
                    await self.route_message(websocket, client_uid, data)
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": str(e)})
                    )
                    continue
        except WebSocketDisconnect:
            logger.info(f"Client {client_uid} disconnected")
        finally:
            await self.handle_disconnect(client_uid)
    
    async def route_message(self, websocket: WebSocket, client_uid: str, data: dict):
        """Route incoming message to appropriate handler"""
        msg_type = data.get("type")
        if not msg_type:
            logger.warning("Message received without type")
            return
        
        # Route based on message type
        if msg_type == "chat_message":
            await self.handle_chat_message(websocket, client_uid, data)
        elif msg_type == "audio_data":
            await self.handle_audio_data(websocket, client_uid, data)
        elif msg_type == "request_status":
            await self.handle_status_request(websocket, client_uid)
        elif msg_type == "live2d_update":
            await self.handle_live2d_update(websocket, client_uid, data)
        elif msg_type == "tts_request":
            await self.handle_tts_request(websocket, client_uid, data)
        elif msg_type == "text-input":
            await self.handle_text_input(websocket, client_uid, data)
        elif msg_type == "mic-audio-data":
            await self.handle_mic_audio_data(websocket, client_uid, data)
        elif msg_type == "mic-audio-end":
            await self.handle_mic_audio_end(websocket, client_uid, data)
        elif msg_type == "fetch-history-list":
            await self.handle_fetch_history_list(websocket, client_uid, data)
        elif msg_type == "fetch-and-set-history":
            await self.handle_fetch_and_set_history(websocket, client_uid, data)
        elif msg_type == "create-new-history":
            await self.handle_create_new_history(websocket, client_uid, data)
        elif msg_type == "delete-history":
            await self.handle_delete_history(websocket, client_uid, data)
        elif msg_type == "sync-local-messages":
            await self.handle_sync_local_messages(websocket, client_uid, data)
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    async def handle_chat_message(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle incoming chat messages"""
        message = data.get("message", "")
        if not message:
            return
        
        try:
            # Get context to check for active history
            context = self.client_contexts.get(client_uid)
            history_uid = context.history_uid if context else None
            
            # Process the message using dialogue service
            result = await self.dialogue_service.process_message(
                message=message,
                session_id=client_uid
            )
            
            # Extract response from the result
            response = result.get("response", "Error: No response generated")
            
            # Save conversation to history manager if history is active
            if history_uid:
                self.history_manager.store_message(client_uid, history_uid, "human", message)
                self.history_manager.store_message(client_uid, history_uid, "ai", response)
            
            # Send response back to client
            await websocket.send_text(
                json.dumps({
                    "type": "chat_response",
                    "message": response,
                    "client_id": client_uid
                })
            )
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            import traceback
            traceback.print_exc()
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error processing your message"
                })
            )
    
    async def handle_text_input(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle text input from frontend"""
        text = data.get("text", "")
        if not text:
            return

        try:
            # Get context to check for active history
            context = self.client_contexts.get(client_uid)
            history_uid = context.history_uid if context else None
            
            # Process the text using dialogue service
            result = await self.dialogue_service.process_message(
                message=text,
                session_id=client_uid
            )
            
            # Extract response from the result
            response = result.get("response", "Error: No response generated")
            
            # Save conversation to history manager if history is active
            if history_uid:
                self.history_manager.store_message(client_uid, history_uid, "human", text)
                self.history_manager.store_message(client_uid, history_uid, "ai", response)
            
            # Send response back to client
            await websocket.send_text(
                json.dumps({
                    "type": "full-text",
                    "text": response,
                    "client_id": client_uid
                })
            )
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            import traceback
            traceback.print_exc()
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error processing your message"
                })
            )
    
    async def handle_audio_data(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle incoming audio data"""
        if not self.asr_service:
            logger.warning("ASR service not available")
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "ASR service not enabled"
                })
            )
            return

        audio_data = data.get("audio", "")
        if audio_data:
            logger.info(f"Received audio data from {client_uid}")
            try:
                # Get context to check for active history
                context = self.client_contexts.get(client_uid)
                history_uid = context.history_uid if context else None
                
                # Transcribe audio to text using ASR
                text = await self.asr_service.async_transcribe(audio_data)
                logger.info(f"ASR transcription: {text}")

                # Process the transcribed text using dialogue service
                result = await self.dialogue_service.process_message(
                    message=text,
                    session_id=client_uid
                )
                
                # Extract response from the result
                response_text = result.get("response", "Error: No response generated")

                # Save conversation to history manager if history is active
                if history_uid:
                    self.history_manager.store_message(client_uid, history_uid, "human", text)
                    self.history_manager.store_message(client_uid, history_uid, "ai", response_text)

                # If TTS is enabled, convert response to audio
                if self.tts_service:
                    try:
                        audio_response = await self.tts_service.async_synthesize(
                            response_text, 
                            voice=config.TTS_VOICE, 
                            model=config.TTS_MODEL
                        )
                        
                        # Send both text and audio response
                        await websocket.send_text(
                            json.dumps({
                                "type": "chat_response",
                                "message": response_text,
                                "audio": audio_response.decode('latin1') if isinstance(audio_response, bytes) else audio_response,
                                "client_id": client_uid
                            })
                        )
                    except Exception as e:
                        logger.error(f"Error in TTS synthesis: {e}")
                        import traceback
                        traceback.print_exc()
                        # Send text response only
                        await websocket.send_text(
                            json.dumps({
                                "type": "chat_response",
                                "message": response_text,
                                "client_id": client_uid
                            })
                        )
                else:
                    # Send text response only
                    await websocket.send_text(
                        json.dumps({
                            "type": "chat_response",
                            "message": response_text,
                            "client_id": client_uid
                        })
                    )
            except Exception as e:
                logger.error(f"Error processing audio data: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "message": "Error processing audio data"
                    })
                )
        else:
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "No audio data received"
                })
            )
    
    async def handle_mic_audio_data(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle microphone audio data"""
        audio_data = data.get("audio", [])
        if audio_data:
            # Append audio data to buffer for this client
            self.received_data_buffers[client_uid].extend(audio_data)
    
    async def handle_mic_audio_end(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle end of microphone audio input"""
        # Get the accumulated audio data for this client
        audio_buffer = self.received_data_buffers[client_uid]
        if not audio_buffer:
            logger.warning(f"No audio data in buffer for client {client_uid}")
            return

        if not self.asr_service:
            logger.warning("ASR service not available")
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "ASR service not enabled"
                })
            )
            return

        try:
            # Get context to check for active history
            context = self.client_contexts.get(client_uid)
            history_uid = context.history_uid if context else None
            
            # Convert audio buffer to bytes for ASR processing
            audio_bytes = bytes(audio_buffer)
            text = await self.asr_service.async_transcribe(audio_bytes)
            logger.info(f"ASR transcription: {text}")

            # Process the transcribed text using dialogue service
            result = await self.dialogue_service.process_message(
                message=text,
                session_id=client_uid
            )
            
            # Extract response from the result
            response_text = result.get("response", "Error: No response generated")

            # Save conversation to history manager if history is active
            if history_uid:
                self.history_manager.store_message(client_uid, history_uid, "human", text)
                self.history_manager.store_message(client_uid, history_uid, "ai", response_text)

            # Send response back to client
            await websocket.send_text(
                json.dumps({
                    "type": "full-text",
                    "text": response_text,
                    "client_id": client_uid
                })
            )

            # Clear the audio buffer
            self.received_data_buffers[client_uid] = []
        except Exception as e:
            logger.error(f"Error processing microphone audio: {e}")
            import traceback
            traceback.print_exc()
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error processing microphone audio"
                })
            )
            # Clear the audio buffer even if there was an error
            self.received_data_buffers[client_uid] = []
    
    async def handle_status_request(self, websocket: WebSocket, client_uid: str):
        """Handle status request"""
        await websocket.send_text(
            json.dumps({
                "type": "status",
                "status": "connected",
                "client_id": client_uid,
                "server_info": {
                    "name": config.APP_NAME,
                    "version": config.APP_VERSION
                }
            })
        )
    
    async def handle_live2d_update(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle Live2D model updates"""
        if not self.live2d_model:
            logger.warning("Live2D service not available")
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Live2D service not enabled"
                })
            )
            return

        try:
            # Get the update type and parameters
            update_type = data.get("update_type")
            if update_type == "expression":
                expression_name = data.get("expression_name")
                success = self.live2d_model.update_expression(expression_name)
                if success:
                    await websocket.send_text(
                        json.dumps({
                            "type": "live2d_update_response",
                            "status": "success",
                            "message": f"Expression updated to {expression_name}"
                        })
                    )
                else:
                    await websocket.send_text(
                        json.dumps({
                            "type": "live2d_update_response",
                            "status": "error",
                            "message": f"Failed to update expression: {expression_name}"
                        })
                    )
            elif update_type == "motion":
                motion_name = data.get("motion_name")
                success = self.live2d_model.update_motion(motion_name)
                if success:
                    await websocket.send_text(
                        json.dumps({
                            "type": "live2d_update_response",
                            "status": "success",
                            "message": f"Motion updated to {motion_name}"
                        })
                    )
                else:
                    await websocket.send_text(
                        json.dumps({
                            "type": "live2d_update_response",
                            "status": "error",
                            "message": f"Failed to update motion: {motion_name}"
                        })
                    )
            elif update_type == "parameters":
                parameters = data.get("parameters", {})
                success = self.live2d_model.update_parameters(parameters)
                if success:
                    await websocket.send_text(
                        json.dumps({
                            "type": "live2d_update_response",
                            "status": "success",
                            "message": "Parameters updated successfully"
                        })
                    )
                else:
                    await websocket.send_text(
                        json.dumps({
                            "type": "live2d_update_response",
                            "status": "error",
                            "message": "Failed to update parameters"
                        })
                    )
            else:
                await websocket.send_text(
                    json.dumps({
                        "type": "live2d_update_response",
                        "status": "error",
                        "message": f"Unknown update type: {update_type}"
                    })
                )
        except Exception as e:
            logger.error(f"Error handling Live2D update: {e}")
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error processing Live2D update"
                })
            )

    async def handle_tts_request(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle TTS synthesis request"""
        if not self.tts_service:
            logger.warning("TTS service not available")
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "TTS service not enabled"
                })
            )
            return

        try:
            text = data.get("text", "")
            if not text:
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "message": "No text provided for TTS synthesis"
                    })
                )
                return

            # Synthesize audio from text
            audio_response = await self.tts_service.async_synthesize(
                text, 
                voice=config.TTS_VOICE, 
                model=config.TTS_MODEL
            )

            # Send audio response
            await websocket.send_text(
                json.dumps({
                    "type": "tts_response",
                    "audio": audio_response.decode('latin1') if isinstance(audio_response, bytes) else audio_response,
                    "text": text
                })
            )
        except Exception as e:
            logger.error(f"Error handling TTS request: {e}")
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error processing TTS request"
                })
            )
    
    async def handle_fetch_history_list(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle request for chat history list"""
        try:
            histories = self.history_manager.get_history_list(client_uid)
            await websocket.send_text(
                json.dumps({
                    "type": "history-list", 
                    "histories": histories
                })
            )
        except Exception as e:
            logger.error(f"Error fetching history list: {e}")
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error fetching history list"
                })
            )
    
    async def handle_fetch_and_set_history(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle fetching and setting specific chat history"""
        history_uid = data.get("history_uid")
        if not history_uid:
            return

        try:
            # Update history UID in context
            context = self.client_contexts[client_uid]
            context.history_uid = history_uid

            # Get history from file
            messages = self.history_manager.get_history(client_uid, history_uid)
            
            # Get memory manager and load the history from history manager
            from backend.langchain.memory.memory_manager import get_memory_manager
            memory_manager = get_memory_manager(client_uid)
            memory_manager.load_from_history_manager(history_uid)
            logger.info(f"Loaded {len(messages)} messages into memory for session {client_uid}")

            await websocket.send_text(
                json.dumps({
                    "type": "history-data", 
                    "messages": messages
                })
            )
        except Exception as e:
            logger.error(f"Error fetching and setting history: {e}")
            import traceback
            traceback.print_exc()
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error fetching and setting history"
                })
            )
    
    async def handle_create_new_history(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle creation of new chat history"""
        try:
            history_uid = self.history_manager.create_new_history(client_uid)
            if history_uid:
                # Update context with new history UID
                context = self.client_contexts[client_uid]
                context.history_uid = history_uid

                # Clear LangChain memory manager for this session to start fresh
                from backend.langchain.memory.memory_manager import clear_memory_manager
                clear_memory_manager(client_uid)

                await websocket.send_text(
                    json.dumps({
                        "type": "new-history-created",
                        "history_uid": history_uid,
                    })
                )
                logger.info(f"Created new history for client {client_uid}: {history_uid}")
        except Exception as e:
            logger.error(f"Error creating new history: {e}")
            import traceback
            traceback.print_exc()
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error creating new history"
                })
            )
    
    async def handle_delete_history(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle deletion of chat history"""
        history_uid = data.get("history_uid")
        if not history_uid:
            return

        try:
            success = self.history_manager.delete_history(client_uid, history_uid)
            await websocket.send_text(
                json.dumps({
                    "type": "history-deleted",
                    "success": success,
                    "history_uid": history_uid,
                })
            )
            if history_uid == self.client_contexts[client_uid].history_uid:
                self.client_contexts[client_uid].history_uid = None
                # Clear memory manager since the active history was deleted
                from backend.langchain.memory.memory_manager import clear_memory_manager
                clear_memory_manager(client_uid)
                logger.info(f"Cleared memory for session {client_uid} after deleting active history")
        except Exception as e:
            logger.error(f"Error deleting history: {e}")
            import traceback
            traceback.print_exc()
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error deleting history"
                })
            )
    
    async def handle_sync_local_messages(self, websocket: WebSocket, client_uid: str, data: dict):
        """Handle sync local messages request"""
        history_uid = data.get("history_uid")
        messages = data.get("messages", [])
        
        if not history_uid or not isinstance(messages, list):
            logger.warning("Invalid sync-local-messages request")
            return
        
        try:
            # Store each message
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                if role and content:
                    self.history_manager.store_message(client_uid, history_uid, role, content)
            
            logger.info(f"Synced {len(messages)} local messages for client {client_uid}, history {history_uid}")
            
            # Send confirmation
            await websocket.send_text(
                json.dumps({
                    "type": "local-messages-synced",
                    "history_uid": history_uid,
                    "message_count": len(messages)
                })
            )
        except Exception as e:
            logger.error(f"Error syncing local messages: {e}")
            import traceback
            traceback.print_exc()
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Error syncing local messages"
                })
            )

    async def handle_disconnect(self, client_uid: str = None):
        """Handle client disconnection"""
        if client_uid and client_uid in self.client_connections:
            # Remove client connection
            del self.client_connections[client_uid]
            
            # Remove client context
            if client_uid in self.client_contexts:
                context = self.client_contexts[client_uid]
                await context.cleanup_context(client_uid)
                del self.client_contexts[client_uid]
            
            # Cancel any running tasks
            task = self.current_tasks.get(client_uid)
            if task and not task.done():
                task.cancel()
                self.current_tasks.pop(client_uid, None)
            
            # Clear audio buffer
            if client_uid in self.received_data_buffers:
                del self.received_data_buffers[client_uid]
        
        logger.info(f"Client {client_uid} disconnected and cleaned up")
