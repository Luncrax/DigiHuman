"""
WebSocket handler for DigiHuman project.
Keeps the runtime message flow on a single unified conversation pipeline.
"""
import asyncio
import base64
import json
import re
import traceback
import uuid
from typing import Any, Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from backend.asr import get_asr_service
from backend.auth import get_current_user_from_authorization
from backend.context_manager import ContextManager
from backend.core.config import config
from backend.emotion import analyze_emotion, get_emotion_analyzer, get_emotion_controller
from backend.history_manager import HistoryManager
from backend.langchain.memory.memory_manager import LangChainMemoryManager
from backend.langchain.models.llm_service import LangChainLLMService
from backend.langchain.services.dialogue_service import LangChainDialogueService
from backend.live2d.live2d_model import Live2DModel, Live2DModelConfig
from backend.request_context import reset_current_owner_uid, set_current_owner_uid
from backend.tts import get_tts_service


class WebSocketHandler:
    """Handles WebSocket connections and message routing."""

    EMOTION_ALIASES = {
        "happy": "joy",
        "joy": "joy",
        "sad": "sadness",
        "sadness": "sadness",
        "angry": "anger",
        "anger": "anger",
        "surprised": "surprise",
        "surprise": "surprise",
        "scared": "fear",
        "fear": "fear",
        "disgust": "disgust",
        "shy": "shy",
        "neutral": "neutral",
    }

    def __init__(self):
        self.client_connections: Dict[str, WebSocket] = {}
        self.client_contexts: Dict[str, ContextManager] = {}
        self.current_tasks: Dict[str, asyncio.Task] = {}
        self.received_data_buffers: Dict[str, Any] = {}

        self.history_manager = HistoryManager()
        self.llm_service = LangChainLLMService()
        self.memory_manager = LangChainMemoryManager()
        self.dialogue_service = LangChainDialogueService()
        self.emotion_analyzer = get_emotion_analyzer()
        self.emotion_controller = get_emotion_controller()
        self.asr_service = get_asr_service() if config.ASR_ENABLED else None
        self.tts_service = get_tts_service() if config.TTS_ENABLED else None

        self.live2d_model: Optional[Live2DModel] = None
        if config.LIVE2D_ENABLED and config.LIVE2D_MODEL_PATH:
            try:
                live2d_config = Live2DModelConfig(
                    model_path=config.LIVE2D_MODEL_PATH,
                    motion_path=config.LIVE2D_MOTION_PATH,
                    expression_path=config.LIVE2D_EXPRESSION_PATH,
                    physics_path=config.LIVE2D_PHYSICS_PATH,
                    pose_path=config.LIVE2D_POSE_PATH,
                )
                self.live2d_model = Live2DModel(live2d_config)
            except Exception as e:
                logger.error(f"Failed to initialize Live2D model: {e}")

    def _get_audio_format(self) -> str:
        if config.TTS_SERVICE == "edge_tts":
            return "audio/mpeg"
        return "audio/wav"

    def _prepare_tts_text(self, text: str) -> str:
        cleaned = str(text or "").strip()
        if not cleaned:
            return ""

        cleaned = re.sub(r"（[^（）]{0,80}）", "", cleaned)
        cleaned = re.sub(r"\([^()]{0,80}\)", "", cleaned)
        cleaned = re.sub(r"【[^【】]{0,80}】", "", cleaned)
        cleaned = re.sub(r"\[[^\[\]]{0,80}\]", "", cleaned)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"(……){2,}", "……", cleaned)
        cleaned = cleaned.strip(" ，,、；;：:")
        return cleaned or str(text or "").strip()

    async def _synthesize_audio(
        self,
        text: str,
        emotion_result=None,
        tts_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if not self.tts_service:
            return None

        try:
            spoken_text = self._prepare_tts_text(text)
            if not spoken_text:
                return None

            synth_kwargs: Dict[str, Any] = {
                "voice": config.TTS_VOICE,
                "model": config.TTS_MODEL,
            }

            if config.TTS_SERVICE == "qwen3_tts":
                synth_kwargs.update({
                    "emotion": getattr(emotion_result, "emotion", None),
                    "intensity": getattr(emotion_result, "intensity", None),
                })

            if tts_params:
                synth_kwargs.update({
                    key: value
                    for key, value in tts_params.items()
                    if value is not None and key != "strategy"
                })

            audio_response = await self.tts_service.async_synthesize(spoken_text, **synth_kwargs)
            return base64.b64encode(audio_response).decode("utf-8")
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None

    def _apply_live2d_command(self, live2d_command: Optional[Dict[str, Any]]) -> None:
        if not self.live2d_model or not live2d_command:
            return

        try:
            expression = live2d_command.get("expression")
            motion = live2d_command.get("motion")
            parameters = live2d_command.get("parameters")

            if expression:
                self.live2d_model.set_live2d_expression(expression)
            if motion:
                self.live2d_model.play_live2d_motion(motion, priority=1)
            if parameters:
                self.live2d_model.update_parameters(parameters)
        except Exception as e:
            logger.error(f"Failed to apply Live2D command: {e}")

    def _normalize_emotion_name(self, emotion: Optional[str]) -> str:
        if not emotion:
            return "neutral"
        return self.EMOTION_ALIASES.get(str(emotion).lower(), "neutral")

    def _normalize_emotion_result(self, emotion_result) -> Dict[str, Any]:
        emotion_name = self._normalize_emotion_name(getattr(emotion_result, "emotion", None))
        raw_details = getattr(emotion_result, "details", {}) or {}
        details = {name: 0.0 for name in ["joy", "sadness", "anger", "surprise", "fear", "disgust", "neutral", "shy"]}

        for raw_name, score in raw_details.items():
            normalized_name = self._normalize_emotion_name(raw_name)
            details[normalized_name] = max(details.get(normalized_name, 0.0), float(score))

        if emotion_name in details and details[emotion_name] == 0.0:
            details[emotion_name] = float(getattr(emotion_result, "confidence", 0.0) or 0.0)

        return {
            "emotion": emotion_name,
            "confidence": max(0.0, min(1.0, float(getattr(emotion_result, "confidence", 0.5) or 0.5))),
            "intensity": getattr(emotion_result, "intensity", "low") or "low",
            "details": details,
        }

    def _split_completed_sentences(self, text: str):
        sentences = []
        buffer = (text or "").strip()

        if not buffer:
            return sentences, ""

        strong_breaks = "。！？!?；;：:.\n"
        start = 0

        for index, char in enumerate(buffer):
            should_split = char in strong_breaks

            if not should_split:
                continue

            sentence = buffer[start:index + 1].strip()
            if sentence:
                sentences.append(sentence)
            start = index + 1

        return sentences, buffer[start:].strip()

    def _merge_short_sentences(self, sentences):
        merged = []
        pending = ""
        min_chars = 22

        for sentence in sentences:
            current = sentence.strip()
            if not current:
                continue

            if not pending:
                pending = current
                continue

            if len(pending) < min_chars:
                pending = f"{pending}{current}"
            else:
                merged.append(pending)
                pending = current

        if pending:
            merged.append(pending)

        return merged

    async def _build_response_payload(
        self,
        client_uid: str,
        response_text: str,
        user_emotion,
        assistant_emotion,
        user_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        control_result = self.emotion_controller.build_from_analysis(response_text, assistant_emotion)
        live2d_command = control_result.live2d_params

        response_data: Dict[str, Any] = {
            "type": "full-response",
            "response_id": str(uuid.uuid4()),
            "client_id": client_uid,
            "text": {
                "original": response_text,
                "enhanced": control_result.enhanced_text,
            },
            "emotion": {
                "user": self._normalize_emotion_result(user_emotion),
                "assistant": self._normalize_emotion_result(assistant_emotion),
            },
            "live2d_command": live2d_command,
            "live2d_params": control_result.live2d_params,
            "tts_params": control_result.tts_params,
            "tts_instruct": control_result.tts_instruct,
            "audio": None,
            "audio_format": None,
            "warnings": [],
        }

        if user_text:
            response_data["user_text"] = user_text

        self._apply_live2d_command(live2d_command)

        if not self.live2d_model:
            response_data["warnings"].append({
                "code": "live2d_backend_disabled",
                "message": "后端 Live2D 本地模型未启用，当前由前端状态机独立驱动表现。",
            })

        return response_data

    async def _send_audio_followup(
        self,
        websocket: WebSocket,
        response_id: str,
        text: str,
        emotion_result,
        tts_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        audio_b64 = await self._synthesize_audio(text, emotion_result, tts_params)
        audio_format = self._get_audio_format()
        payload: Dict[str, Any] = {
            "type": "response-audio",
            "response_id": response_id,
            "audio": audio_b64,
            "audio_format": audio_format if audio_b64 else None,
            "warnings": [],
        }

        if not audio_b64 and config.TTS_ENABLED:
            payload["warnings"].append({
                "code": "tts_unavailable",
                "message": "TTS 当前不可用，已降级为文本回复。",
            })

        try:
            await websocket.send_text(json.dumps(payload))
        except Exception as e:
            logger.warning(f"Failed to send audio follow-up for response {response_id}: {e}")

    async def _stream_sentence_audio_worker(
        self,
        websocket: WebSocket,
        response_id: str,
        sentence_queue: "asyncio.Queue[Optional[Dict[str, Any]]]",
        emotion_hint: Dict[str, Any],
    ) -> None:
        while True:
            item = await sentence_queue.get()
            if item is None:
                sentence_queue.task_done()
                break

            index = item["index"]
            sentence = item["text"]

            try:
                control_result = self.emotion_controller.build_controls(
                    text=sentence,
                    emotion=emotion_hint.get("emotion"),
                    intensity=emotion_hint.get("intensity"),
                    confidence=float(emotion_hint.get("confidence", 0.5) or 0.5),
                    details=emotion_hint.get("details"),
                )
                audio_b64 = await self._synthesize_audio(
                    control_result.enhanced_text,
                    emotion_result=None,
                    tts_params=control_result.tts_params,
                )

                await websocket.send_text(json.dumps({
                    "type": "sentence-audio",
                    "response_id": response_id,
                    "index": index,
                    "text": sentence,
                    "audio": audio_b64,
                    "audio_format": "audio/wav" if audio_b64 else None,
                    "live2d_command": control_result.live2d_params,
                }))
            except Exception as e:
                logger.warning(f"Failed to synthesize sentence audio {index} for {response_id}: {e}")
            finally:
                sentence_queue.task_done()

    async def _send_emotion_update(self, websocket: WebSocket, source: str, emotion_result, text: Optional[str] = None):
        payload: Dict[str, Any] = {
            "type": "emotion_update",
            "source": source,
            "emotion": getattr(emotion_result, "emotion", "neutral"),
            "confidence": getattr(emotion_result, "confidence", 0.5),
            "intensity": getattr(emotion_result, "intensity", "medium"),
            "details": getattr(emotion_result, "details", {}) or {},
        }
        if text is not None:
            payload["text"] = text
        await websocket.send_text(json.dumps(payload))

    async def _ensure_active_history(self, client_uid: str) -> Optional[str]:
        context = self.client_contexts.get(client_uid)
        if not context:
            return None

        if context.history_uid:
            return context.history_uid

        history_uid = self.history_manager.create_new_history(client_uid)
        if history_uid:
            context.history_uid = history_uid
        return history_uid

    async def _process_conversation_turn(
        self,
        websocket: WebSocket,
        client_uid: str,
        user_text: str,
        store_user_text_in_response: bool = False,
    ) -> None:
        owner_token = set_current_owner_uid(client_uid)
        try:
            context = self.client_contexts.get(client_uid)
            history_uid = await self._ensure_active_history(client_uid)

            user_emotion = await analyze_emotion(user_text, self.llm_service)
            logger.info(f"User emotion: {user_emotion.emotion} ({user_emotion.confidence})")
            await self._send_emotion_update(
                websocket,
                "user",
                user_emotion,
                text=user_text if store_user_text_in_response else None,
            )

            response_id = str(uuid.uuid4())
            await websocket.send_text(json.dumps({
                "type": "response-start",
                "response_id": response_id,
                "client_id": client_uid,
                "user_text": user_text if store_user_text_in_response else None,
            }))

            response_parts = []
            async for event in self.dialogue_service.process_message_stream(message=user_text, session_id=client_uid):
                if event.get("type") != "chunk":
                    continue

                chunk = event.get("content", "")
                if not chunk:
                    continue

                response_parts.append(chunk)
                await websocket.send_text(json.dumps({
                    "type": "response-delta",
                    "response_id": response_id,
                    "delta": chunk,
                    "text": "".join(response_parts),
                }))

            response_text = "".join(response_parts).strip() or "Error: No response generated"

            assistant_emotion = await analyze_emotion(response_text, self.llm_service)
            logger.info(f"Assistant emotion: {assistant_emotion.emotion} ({assistant_emotion.confidence})")

            if history_uid:
                self.history_manager.store_message(client_uid, history_uid, "human", user_text)
                self.history_manager.store_message(client_uid, history_uid, "ai", response_text)

            response_data = await self._build_response_payload(
                client_uid=client_uid,
                response_text=response_text,
                user_emotion=user_emotion,
                assistant_emotion=assistant_emotion,
                user_text=user_text if store_user_text_in_response else None,
            )
            response_data["response_id"] = response_id
            response_data["streaming"] = True

            await websocket.send_text(json.dumps(response_data))
            await websocket.send_text(
                json.dumps({
                    "type": "emotion_update",
                    "source": "assistant",
                    "emotion": assistant_emotion.emotion,
                    "confidence": assistant_emotion.confidence,
                    "intensity": assistant_emotion.intensity,
                    "details": assistant_emotion.details,
                    "live2d_command": response_data.get("live2d_command"),
                })
            )
            await self._send_audio_followup(
                websocket=websocket,
                response_id=response_id,
                text=response_data["text"]["enhanced"],
                emotion_result=assistant_emotion,
                tts_params=response_data.get("tts_params"),
            )
            return
        finally:
            reset_current_owner_uid(owner_token)

        sentence_queue: asyncio.Queue = asyncio.Queue()
        sentence_worker = asyncio.create_task(
            self._stream_sentence_audio_worker(
                websocket,
                response_id,
                sentence_queue,
                {
                    "emotion": "neutral",
                    "intensity": "low",
                    "confidence": 0.5,
                    "details": {"neutral": 0.5},
                },
            )
        )

        response_parts = []
        sentence_buffer = ""
        sentence_index = 0

        async for event in self.dialogue_service.process_message_stream(message=user_text, session_id=client_uid):
            if event.get("type") != "chunk":
                continue

            chunk = event.get("content", "")
            if not chunk:
                continue

            response_parts.append(chunk)
            sentence_buffer += chunk

            await websocket.send_text(json.dumps({
                "type": "response-delta",
                "response_id": response_id,
                "delta": chunk,
                "text": "".join(response_parts),
            }))

            completed_sentences, sentence_buffer = self._split_completed_sentences(sentence_buffer)
            for sentence in self._merge_short_sentences(completed_sentences):
                logger.info(f"Queueing sentence-audio chunk {sentence_index} for {response_id}: {sentence}")
                await sentence_queue.put({
                    "index": sentence_index,
                    "text": sentence,
                })
                sentence_index += 1

        if sentence_buffer.strip():
            trailing_sentences = self._merge_short_sentences([sentence_buffer.strip()])
            trailing_text = trailing_sentences[0] if trailing_sentences else sentence_buffer.strip()
            logger.info(f"Queueing trailing sentence-audio chunk {sentence_index} for {response_id}: {trailing_text}")
            await sentence_queue.put({
                "index": sentence_index,
                "text": trailing_text,
            })

        await sentence_queue.put(None)

        response_text = "".join(response_parts).strip() or "Error: No response generated"

        assistant_emotion = await analyze_emotion(response_text, self.llm_service)
        logger.info(f"Assistant emotion: {assistant_emotion.emotion} ({assistant_emotion.confidence})")

        if history_uid:
            self.history_manager.store_message(client_uid, history_uid, "human", user_text)
            self.history_manager.store_message(client_uid, history_uid, "ai", response_text)

        response_data = await self._build_response_payload(
            client_uid=client_uid,
            response_text=response_text,
            user_emotion=user_emotion,
            assistant_emotion=assistant_emotion,
            user_text=user_text if store_user_text_in_response else None,
        )
        response_data["response_id"] = response_id
        response_data["streaming"] = True

        await websocket.send_text(json.dumps(response_data))
        await websocket.send_text(
            json.dumps({
                "type": "emotion_update",
                "source": "assistant",
                "emotion": assistant_emotion.emotion,
                "confidence": assistant_emotion.confidence,
                "intensity": assistant_emotion.intensity,
                "details": assistant_emotion.details,
                "live2d_command": response_data.get("live2d_command"),
            })
        )
        await sentence_worker

    def _decode_audio_payload(self, audio_data: Any) -> bytes:
        if isinstance(audio_data, list):
            try:
                return b"".join(base64.b64decode(chunk) for chunk in audio_data if chunk)
            except Exception:
                return b""
        if isinstance(audio_data, str) and audio_data:
            try:
                return base64.b64decode(audio_data)
            except Exception:
                return b""
        return b""

    async def _transcribe_audio_bytes(self, websocket: WebSocket, client_uid: str, audio_bytes: bytes) -> Optional[str]:
        if not self.asr_service:
            logger.warning("ASR service not available")
            await websocket.send_text(json.dumps({"type": "error", "message": "ASR service not enabled"}))
            return None

        if not audio_bytes:
            await websocket.send_text(json.dumps({"type": "error", "message": "Invalid audio data"}))
            return None

        logger.info(f"Starting ASR transcription for client {client_uid}")
        text = await self.asr_service.async_transcribe(audio_bytes)
        logger.info(f"ASR transcription result for client {client_uid}: '{text}'")
        text_str = str(text or "").strip()
        if "ASR_VOSK_MODEL_PATH" in text_str or "Vosk" in text_str:
            await websocket.send_text(json.dumps({"type": "error", "message": "语音识别失败，请检查本地 Vosk 模型配置"}))
            return None

        if text is None or text == "None" or not text or text == "[语音识别失败]":
            await websocket.send_text(json.dumps({"type": "error", "message": "语音识别失败，请重试"}))
            return None

        return text_str

    async def handle_new_connection(
        self,
        websocket: WebSocket,
        requested_client_uid: Optional[str] = None,
        auth_token: Optional[str] = None,
    ):
        auth_user = get_current_user_from_authorization(f"Bearer {auth_token}" if auth_token else None)
        client_uid = f"user:{auth_user.id}" if auth_user else ((requested_client_uid or "").strip() or str(uuid.uuid4()))
        self.client_connections[client_uid] = websocket
        logger.info(f"New WebSocket connection established: {client_uid}")

        context_manager = ContextManager()
        await context_manager.initialize_context(client_uid)
        self.client_contexts[client_uid] = context_manager
        self.received_data_buffers[client_uid] = []

        await websocket.send_text(
            json.dumps({
                "type": "connection_established",
                "message": "Connected to DigiHuman WebSocket server",
                "client_id": client_uid,
                "user": {
                    "id": auth_user.id,
                    "username": auth_user.username,
                } if auth_user else None,
            })
        )

    async def handle_messages(self, websocket: WebSocket):
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
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except WebSocketDisconnect:
            logger.info(f"Client {client_uid} disconnected")
        finally:
            await self.handle_disconnect(client_uid)

    async def route_message(self, websocket: WebSocket, client_uid: str, data: dict):
        msg_type = data.get("type")
        if not msg_type:
            logger.warning("Message received without type")
            return

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
        message = data.get("message", "")
        if not message:
            return
        await self._process_conversation_turn(websocket, client_uid, message)

    async def handle_text_input(self, websocket: WebSocket, client_uid: str, data: dict):
        text = data.get("text", "")
        if not text:
            return
        await self._process_conversation_turn(websocket, client_uid, text)

    async def handle_audio_data(self, websocket: WebSocket, client_uid: str, data: dict):
        audio_data = data.get("audio", "")
        if not audio_data:
            await websocket.send_text(json.dumps({"type": "error", "message": "No audio data received"}))
            return

        try:
            audio_bytes = self._decode_audio_payload(audio_data)
            text = await self._transcribe_audio_bytes(websocket, client_uid, audio_bytes)
            if not text:
                return
            await self._process_conversation_turn(websocket, client_uid, text, store_user_text_in_response=True)
        except Exception as e:
            logger.error(f"Error processing audio data: {e}")
            traceback.print_exc()
            await websocket.send_text(json.dumps({"type": "error", "message": "Error processing audio data"}))

    async def handle_mic_audio_data(self, websocket: WebSocket, client_uid: str, data: dict):
        audio_data = data.get("audio", "")
        if audio_data:
            self.received_data_buffers[client_uid] = audio_data

    async def handle_mic_audio_end(self, websocket: WebSocket, client_uid: str, data: dict):
        audio_data = self.received_data_buffers.get(client_uid, "")
        if not audio_data:
            await websocket.send_text(json.dumps({"type": "error", "message": "No audio data received"}))
            return

        try:
            audio_bytes = self._decode_audio_payload(audio_data)
            text = await self._transcribe_audio_bytes(websocket, client_uid, audio_bytes)
            if not text:
                self.received_data_buffers[client_uid] = []
                return

            await self._process_conversation_turn(websocket, client_uid, text, store_user_text_in_response=True)
        except Exception as e:
            logger.error(f"Error processing microphone audio: {e}")
            traceback.print_exc()
            await websocket.send_text(json.dumps({"type": "error", "message": "处理语音时出现问题，请稍后再试"}))
        finally:
            self.received_data_buffers[client_uid] = []

    async def handle_status_request(self, websocket: WebSocket, client_uid: str):
        await websocket.send_text(
            json.dumps({
                "type": "status",
                "status": "connected",
                "client_id": client_uid,
                "server_info": {
                    "name": config.APP_NAME,
                    "version": config.APP_VERSION,
                },
            })
        )

    async def handle_live2d_update(self, websocket: WebSocket, client_uid: str, data: dict):
        if not self.live2d_model:
            logger.warning("Live2D service not available")
            await websocket.send_text(json.dumps({"type": "error", "message": "Live2D service not enabled"}))
            return

        try:
            update_type = data.get("update_type")
            if update_type == "expression":
                expression_name = data.get("expression_name")
                success = self.live2d_model.update_expression(expression_name)
                response = {
                    "type": "live2d_update_response",
                    "status": "success" if success else "error",
                    "message": (
                        f"Expression updated to {expression_name}"
                        if success
                        else f"Failed to update expression: {expression_name}"
                    ),
                }
                await websocket.send_text(json.dumps(response))
            elif update_type == "motion":
                motion_name = data.get("motion_name")
                success = self.live2d_model.update_motion(motion_name)
                response = {
                    "type": "live2d_update_response",
                    "status": "success" if success else "error",
                    "message": (
                        f"Motion updated to {motion_name}"
                        if success
                        else f"Failed to update motion: {motion_name}"
                    ),
                }
                await websocket.send_text(json.dumps(response))
            elif update_type == "parameters":
                parameters = data.get("parameters", {})
                success = self.live2d_model.update_parameters(parameters)
                await websocket.send_text(
                    json.dumps({
                        "type": "live2d_update_response",
                        "status": "success" if success else "error",
                        "message": "Parameters updated successfully" if success else "Failed to update parameters",
                    })
                )
            else:
                await websocket.send_text(
                    json.dumps({
                        "type": "live2d_update_response",
                        "status": "error",
                        "message": f"Unknown update type: {update_type}",
                    })
                )
        except Exception as e:
            logger.error(f"Error handling Live2D update: {e}")
            await websocket.send_text(json.dumps({"type": "error", "message": "Error processing Live2D update"}))

    async def handle_tts_request(self, websocket: WebSocket, client_uid: str, data: dict):
        if not self.tts_service:
            logger.warning("TTS service not available")
            await websocket.send_text(json.dumps({"type": "error", "message": "TTS service not enabled"}))
            return

        try:
            text = data.get("text", "")
            if not text:
                await websocket.send_text(json.dumps({"type": "error", "message": "No text provided for TTS synthesis"}))
                return

            control_result = self.emotion_controller.build_controls(
                text=text,
                emotion=data.get("emotion"),
                intensity=data.get("intensity"),
                confidence=float(data.get("confidence", 0.5) or 0.5),
                details=data.get("details"),
            )

            tts_params = dict(control_result.tts_params)
            if data.get("model"):
                tts_params["model"] = data.get("model")
            if data.get("voice"):
                tts_params["voice"] = data.get("voice")
                tts_params["speaker"] = data.get("voice")
            if data.get("voice_prompt_path"):
                tts_params["voice_prompt_path"] = data.get("voice_prompt_path")
            if data.get("instruct"):
                tts_params["instruct"] = data.get("instruct")

            audio_response = await self.tts_service.async_synthesize(
                control_result.enhanced_text,
                **{key: value for key, value in tts_params.items() if key != "strategy"},
            )

            await websocket.send_text(
                json.dumps({
                    "type": "tts_response",
                    "audio": base64.b64encode(audio_response).decode("utf-8") if isinstance(audio_response, bytes) else audio_response,
                    "audio_format": self._get_audio_format(),
                    "text": control_result.enhanced_text,
                    "tts_params": tts_params,
                    "tts_instruct": tts_params.get("instruct"),
                })
            )
        except Exception as e:
            logger.error(f"Error handling TTS request: {e}")
            await websocket.send_text(json.dumps({"type": "error", "message": "Error processing TTS request"}))

    async def handle_fetch_history_list(self, websocket: WebSocket, client_uid: str, data: dict):
        try:
            histories = self.history_manager.get_history_list(client_uid)
            await websocket.send_text(json.dumps({"type": "history-list", "histories": histories}))
        except Exception as e:
            logger.error(f"Error fetching history list: {e}")
            await websocket.send_text(json.dumps({"type": "error", "message": "Error fetching history list"}))

    async def handle_fetch_and_set_history(self, websocket: WebSocket, client_uid: str, data: dict):
        history_uid = data.get("history_uid")
        if not history_uid:
            return

        try:
            context = self.client_contexts[client_uid]
            context.history_uid = history_uid

            messages = self.history_manager.get_history(client_uid, history_uid)

            from backend.langchain.memory.memory_manager import get_memory_manager

            memory_manager = get_memory_manager(client_uid)
            memory_manager.load_from_history_manager(history_uid)
            logger.info(f"Loaded {len(messages)} messages into memory for session {client_uid}")

            await websocket.send_text(json.dumps({"type": "history-data", "messages": messages}))
        except Exception as e:
            logger.error(f"Error fetching and setting history: {e}")
            traceback.print_exc()
            await websocket.send_text(json.dumps({"type": "error", "message": "Error fetching and setting history"}))

    async def handle_create_new_history(self, websocket: WebSocket, client_uid: str, data: dict):
        try:
            history_uid = self.history_manager.create_new_history(client_uid)
            if history_uid:
                context = self.client_contexts[client_uid]
                context.history_uid = history_uid

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
            traceback.print_exc()
            await websocket.send_text(json.dumps({"type": "error", "message": "Error creating new history"}))

    async def handle_delete_history(self, websocket: WebSocket, client_uid: str, data: dict):
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

                from backend.langchain.memory.memory_manager import clear_memory_manager

                clear_memory_manager(client_uid)
                logger.info(f"Cleared memory for session {client_uid} after deleting active history")
        except Exception as e:
            logger.error(f"Error deleting history: {e}")
            traceback.print_exc()
            await websocket.send_text(json.dumps({"type": "error", "message": "Error deleting history"}))

    async def handle_sync_local_messages(self, websocket: WebSocket, client_uid: str, data: dict):
        history_uid = data.get("history_uid")
        messages = data.get("messages", [])

        if not history_uid or not isinstance(messages, list):
            logger.warning("Invalid sync-local-messages request")
            return

        try:
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                if role and content:
                    self.history_manager.store_message(client_uid, history_uid, role, content)

            logger.info(f"Synced {len(messages)} local messages for client {client_uid}, history {history_uid}")
            await websocket.send_text(
                json.dumps({
                    "type": "local-messages-synced",
                    "history_uid": history_uid,
                    "message_count": len(messages),
                })
            )
        except Exception as e:
            logger.error(f"Error syncing local messages: {e}")
            traceback.print_exc()
            await websocket.send_text(json.dumps({"type": "error", "message": "Error syncing local messages"}))

    async def handle_disconnect(self, client_uid: Optional[str] = None):
        if client_uid and client_uid in self.client_connections:
            del self.client_connections[client_uid]

            if client_uid in self.client_contexts:
                context = self.client_contexts[client_uid]
                await context.cleanup_context(client_uid)
                del self.client_contexts[client_uid]

            task = self.current_tasks.get(client_uid)
            if task and not task.done():
                task.cancel()
                self.current_tasks.pop(client_uid, None)

            if client_uid in self.received_data_buffers:
                del self.received_data_buffers[client_uid]

        logger.info(f"Client {client_uid} disconnected and cleaned up")
