from __future__ import annotations

import base64
import random
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

from backend.core.config import config
from backend.utils.logger import get_logger
from .importer import KNOWLEDGE_ROOT, list_knowledge_files
from .milvus_store import KnowledgeItem, MilvusKnowledgeStore

logger = get_logger(__name__)

MUSIC_ROOT = Path("study_assets/music")
MUSIC_CATEGORIES = ["focus", "relax", "ambient"]
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}


@dataclass
class PomodoroSession:
    session_id: str
    owner_uid: str
    title: str
    focus_minutes: int
    break_minutes: int
    rounds: int
    started_at: datetime
    ends_at: datetime
    status: str = "focus"
    total_seconds: int = 0
    paused_remaining_seconds: int | None = None

    def to_dict(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        remaining_seconds = (
            max(0, int(self.paused_remaining_seconds))
            if self.status == "paused" and self.paused_remaining_seconds is not None
            else max(0, int((self.ends_at - now).total_seconds()))
        )
        total_seconds = max(1, int(self.total_seconds or (self.ends_at - self.started_at).total_seconds()))
        return {
            "session_id": self.session_id,
            "owner_uid": self.owner_uid,
            "title": self.title,
            "focus_minutes": self.focus_minutes,
            "break_minutes": self.break_minutes,
            "rounds": self.rounds,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "started_at_ms": int(self.started_at.timestamp() * 1000),
            "ends_at_ms": int(self.ends_at.timestamp() * 1000),
            "total_seconds": total_seconds,
            "remaining_seconds": remaining_seconds,
        }


class StudyAssistantService:
    def __init__(self, tts_getter: Callable[[], Any] | None = None):
        self.tts_getter = tts_getter or (lambda: None)
        self.knowledge_store = MilvusKnowledgeStore()
        self.pomodoro_sessions: dict[str, PomodoroSession] = {}
        self._ensure_music_folders()
        self.bootstrap_result = self.knowledge_store.bootstrap(self._default_knowledge_items())

    def _ensure_music_folders(self) -> None:
        for category in MUSIC_CATEGORIES:
            target = MUSIC_ROOT / category
            target.mkdir(parents=True, exist_ok=True)
            keep_file = target / ".gitkeep"
            if not keep_file.exists():
                keep_file.write_text("", encoding="utf-8")

    def _default_knowledge_items(self) -> list[KnowledgeItem]:
        return [
            KnowledgeItem(
                id=1001,
                owner_uid="system",
                item_type="template",
                title="数学学习计划模板",
                description="适合 60 到 90 分钟的数学学习。先热身复习，再做题，最后错题整理。",
                category="study_plan",
                tool_command="start_pomodoro",
                payload={"subject": "math", "focus_minutes": 25, "break_minutes": 5, "rounds": 2},
            ),
            KnowledgeItem(
                id=1002,
                owner_uid="system",
                item_type="template",
                title="编程学习计划模板",
                description="先阅读目标任务，再编码实践，最后做总结复盘。",
                category="study_plan",
                tool_command="start_pomodoro",
                payload={"subject": "programming", "focus_minutes": 30, "break_minutes": 5, "rounds": 2},
            ),
            KnowledgeItem(
                id=1003,
                owner_uid="system",
                item_type="template",
                title="英语口语学习计划模板",
                description="包含听力输入、跟读模仿、自由表达三个阶段，适合 45 到 60 分钟练习。",
                category="study_plan",
                tool_command="play_music",
                payload={"subject": "english", "music_category": "focus", "focus_minutes": 20, "break_minutes": 5, "rounds": 2},
            ),
            KnowledgeItem(
                id=2001,
                owner_uid="system",
                item_type="tool",
                title="番茄钟工具",
                description="适用于需要专注学习的任务。默认 25 分钟专注，5 分钟休息。",
                category="tool",
                tool_command="start_pomodoro",
                payload={"focus_minutes": 25, "break_minutes": 5, "rounds": 1},
            ),
            KnowledgeItem(
                id=2002,
                owner_uid="system",
                item_type="tool",
                title="专注音乐工具",
                description="从 focus 文件夹中播放专注音乐，用于编程、数学、阅读等深度学习任务。",
                category="tool",
                tool_command="play_music",
                payload={"music_category": "focus"},
            ),
            KnowledgeItem(
                id=2003,
                owner_uid="system",
                item_type="tool",
                title="放松音乐工具",
                description="从 relax 文件夹中播放轻音乐，用于休息和恢复注意力。",
                category="tool",
                tool_command="play_music",
                payload={"music_category": "relax"},
            ),
            KnowledgeItem(
                id=2004,
                owner_uid="system",
                item_type="tool",
                title="语音提醒工具",
                description="使用 TTS 朗读当前任务提示，例如提醒开始下一轮学习或休息。",
                category="tool",
                tool_command="tts_reminder",
                payload={"voice_style": "calm"},
            ),
        ]

    def _infer_subject(self, goal: str) -> str:
        mapping = {
            "\u6570\u5b66": "math",
            "\u7f16\u7a0b": "programming",
            "\u4ee3\u7801": "programming",
            "\u82f1\u8bed": "english",
            "\u53e3\u8bed": "english",
            "\u9605\u8bfb": "reading",
        }
        for keyword, subject in mapping.items():
            if keyword in goal:
                return subject
        return "general"

    def _parse_total_minutes(self, goal: str) -> int:
        match = re.search(r"(\d{1,3})\s*(\u5206\u949f|min)", goal)
        if match:
            return max(20, min(240, int(match.group(1))))
        return 60

    def _choose_music_category(self, goal: str) -> str:
        if any(word in goal for word in ["\u4f11\u606f", "\u653e\u677e", "\u8212\u7f13"]):
            return "relax"
        return "focus"

    def _build_plan_steps(self, subject: str, total_minutes: int) -> list[dict[str, Any]]:
        warmup = max(10, min(20, total_minutes // 4))
        practice = max(20, min(40, total_minutes // 2))
        review = max(10, total_minutes - warmup - practice)
        titles = {
            "math": ["公式回顾", "做题训练", "错题总结"],
            "programming": ["需求拆解", "编码实践", "复盘记录"],
            "english": ["输入模仿", "开口练习", "总结复述"],
            "reading": ["预习目录", "专注阅读", "摘记整理"],
            "general": ["任务拆解", "专注执行", "结果复盘"],
        }
        current = titles.get(subject, titles["general"])
        return [
            {
                "title": current[0],
                "duration_minutes": warmup,
                "tool_command": "start_pomodoro",
                "notes": "先用最小阻力进入状态。",
            },
            {
                "title": current[1],
                "duration_minutes": practice,
                "tool_command": "play_music",
                "notes": "在主任务阶段保持专注输出。",
            },
            {
                "title": current[2],
                "duration_minutes": review,
                "tool_command": "tts_reminder",
                "notes": "用总结巩固本轮学习成果。",
            },
        ]

    def plan_study(self, owner_uid: str, goal: str) -> dict[str, Any]:
        normalized_goal = (goal or "").strip()
        if not normalized_goal:
            raise ValueError("学习目标不能为空。")

        total_minutes = self._parse_total_minutes(normalized_goal)
        subject = self._infer_subject(normalized_goal)
        knowledge_hits = self.knowledge_store.search(owner_uid, normalized_goal, top_k=5)
        plan_steps = self._build_plan_steps(subject, total_minutes)
        music_category = self._choose_music_category(normalized_goal)

        suggested_tools = [
            {
                "command": "start_pomodoro",
                "label": "启动番茄钟",
                "payload": {
                    "title": normalized_goal,
                    "focus_minutes": 25,
                    "break_minutes": 5,
                    "rounds": 2,
                },
            },
            {
                "command": "play_music",
                "label": "播放专注音乐",
                "payload": {"category": music_category},
            },
            {
                "command": "tts_reminder",
                "label": "语音提醒",
                "payload": {"message": f"现在开始：{normalized_goal}"},
            },
        ]

        return {
            "goal": normalized_goal,
            "subject": subject,
            "estimated_total_minutes": total_minutes,
            "overview": f"建议先拆解任务，再进入两轮专注学习，最后用总结收尾，整体约 {total_minutes} 分钟。",
            "plan_steps": plan_steps,
            "knowledge_hits": knowledge_hits,
            "suggested_tools": suggested_tools,
            "music_category": music_category,
            "milvus_status": self.knowledge_store.get_status(),
        }

    def list_music(self) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        for category in MUSIC_CATEGORIES:
            items = []
            for path in sorted((MUSIC_ROOT / category).glob("*")):
                if path.suffix.lower() not in AUDIO_EXTENSIONS:
                    continue
                items.append(
                    {
                        "name": path.name,
                        "category": category,
                        "url": f"/study-music/{quote(category)}/{quote(path.name)}",
                    }
                )
            result[category] = items
        return result

    async def execute_tool(self, owner_uid: str, command: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        if command == "start_pomodoro":
            return self._start_pomodoro(owner_uid, payload)
        if command == "pause_pomodoro":
            return self._pause_pomodoro(payload.get("session_id"))
        if command == "resume_pomodoro":
            return self._resume_pomodoro(payload.get("session_id"))
        if command == "play_music":
            return self._play_music(payload)
        if command == "tts_reminder":
            return await self._tts_reminder(payload)
        if command == "stop_pomodoro":
            return self._stop_pomodoro(payload.get("session_id"))
        raise ValueError(f"Unsupported tool command: {command}")

    def _start_pomodoro(self, owner_uid: str, payload: dict[str, Any]) -> dict[str, Any]:
        focus_minutes = max(1, min(120, int(payload.get("focus_minutes", 25))))
        break_minutes = max(1, min(60, int(payload.get("break_minutes", 5))))
        rounds = max(1, min(8, int(payload.get("rounds", 1))))
        title = str(payload.get("title") or "学习任务").strip() or "学习任务"
        session_id = uuid.uuid4().hex
        started_at = datetime.now(timezone.utc)
        ends_at = started_at + timedelta(minutes=focus_minutes)
        session = PomodoroSession(
            session_id=session_id,
            owner_uid=owner_uid,
            title=title,
            focus_minutes=focus_minutes,
            break_minutes=break_minutes,
            rounds=rounds,
            started_at=started_at,
            ends_at=ends_at,
            total_seconds=focus_minutes * 60,
        )
        self.pomodoro_sessions[session_id] = session
        return {
            "command": "start_pomodoro",
            "message": f"番茄钟已开始：{title}，先专注 {focus_minutes} 分钟。",
            "session": session.to_dict(),
        }

    def _pause_pomodoro(self, session_id: str | None) -> dict[str, Any]:
        if not session_id or session_id not in self.pomodoro_sessions:
            return {"command": "pause_pomodoro", "status": "error", "message": "未找到对应的番茄钟会话。"}
        session = self.pomodoro_sessions[session_id]
        if session.status == "paused":
            return {
                "command": "pause_pomodoro",
                "status": "ok",
                "message": f"番茄钟已经处于暂停状态：{session.title}",
                "session": session.to_dict(),
            }
        remaining_seconds = max(0, int((session.ends_at - datetime.now(timezone.utc)).total_seconds()))
        session.paused_remaining_seconds = remaining_seconds
        session.status = "paused"
        return {
            "command": "pause_pomodoro",
            "status": "ok",
            "message": f"已暂停番茄钟：{session.title}",
            "session": session.to_dict(),
        }

    def _resume_pomodoro(self, session_id: str | None) -> dict[str, Any]:
        if not session_id or session_id not in self.pomodoro_sessions:
            return {"command": "resume_pomodoro", "status": "error", "message": "未找到对应的番茄钟会话。"}
        session = self.pomodoro_sessions[session_id]
        if session.status != "paused":
            return {
                "command": "resume_pomodoro",
                "status": "ok",
                "message": f"番茄钟当前无需继续：{session.title}",
                "session": session.to_dict(),
            }
        remaining_seconds = max(1, int(session.paused_remaining_seconds or 1))
        session.ends_at = datetime.now(timezone.utc) + timedelta(seconds=remaining_seconds)
        session.paused_remaining_seconds = None
        session.status = "focus"
        return {
            "command": "resume_pomodoro",
            "status": "ok",
            "message": f"已继续番茄钟：{session.title}",
            "session": session.to_dict(),
        }

    def _stop_pomodoro(self, session_id: str | None) -> dict[str, Any]:
        if not session_id or session_id not in self.pomodoro_sessions:
            return {"command": "stop_pomodoro", "status": "error", "message": "未找到对应的番茄钟会话。"}
        session = self.pomodoro_sessions.pop(session_id)
        return {
            "command": "stop_pomodoro",
            "status": "ok",
            "message": f"已停止番茄钟：{session.title}",
            "session_id": session_id,
        }

    def _play_music(self, payload: dict[str, Any]) -> dict[str, Any]:
        category = str(payload.get("category") or payload.get("music_category") or "focus").strip().lower()
        if category not in MUSIC_CATEGORIES:
            category = "focus"
        library = self.list_music()
        tracks = library.get(category, [])
        if not tracks:
            return {
                "command": "play_music",
                "status": "empty",
                "message": f"{category} 文件夹里还没有音乐文件，请先把音频放到 study_assets/music/{category}/ 下。",
                "category": category,
                "tracks": [],
            }

        track = random.choice(tracks)
        return {
            "command": "play_music",
            "status": "ok",
            "message": f"准备播放 {category} 音乐：{track['name']}",
            "category": category,
            "track": track,
            "tracks": tracks,
        }

    async def _tts_reminder(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = str(payload.get("message") or "请开始下一步学习任务。").strip()
        tts_service = self.tts_getter() if self.tts_getter else None
        if not tts_service or not config.TTS_ENABLED:
            return {
                "command": "tts_reminder",
                "status": "text_only",
                "message": message,
            }

        try:
            audio_bytes = await tts_service.async_synthesize(
                message,
                voice=config.TTS_VOICE,
                rate=config.EDGE_TTS_RATE,
                pitch=config.EDGE_TTS_PITCH,
                volume=config.EDGE_TTS_VOLUME,
            )
            return {
                "command": "tts_reminder",
                "status": "ok",
                "message": message,
                "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
                "audio_format": "audio/mpeg",
            }
        except Exception as exc:
            logger.warning("TTS reminder failed: %s", exc)
            return {
                "command": "tts_reminder",
                "status": "error",
                "message": message,
                "error": str(exc),
            }

    def get_status(self) -> dict[str, Any]:
        active_sessions = [session.to_dict() for session in self.pomodoro_sessions.values()]
        return {
            "milvus": self.knowledge_store.get_status(),
            "bootstrap": self.bootstrap_result,
            "music_library": self.list_music(),
            "music_root": str(MUSIC_ROOT.resolve()),
            "knowledge_root": str(KNOWLEDGE_ROOT.resolve()),
            "knowledge_files": list_knowledge_files(KNOWLEDGE_ROOT),
            "active_pomodoro_sessions": active_sessions,
        }


_study_service: StudyAssistantService | None = None


def get_study_assistant_service(tts_getter: Callable[[], Any] | None = None) -> StudyAssistantService:
    global _study_service
    if _study_service is None:
        _study_service = StudyAssistantService(tts_getter=tts_getter)
    return _study_service
