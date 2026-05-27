"""WebSocket Voice Streaming - Real-time voice communication support.

This module provides:
- WebSocket server for real-time voice streaming
- Audio chunk handling for continuous speech recognition
- Real-time response streaming
"""

import json
import queue
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field


# ─── Voice Stream Configuration ────────────────────────────────────────────────

@dataclass
class VoiceStreamConfig:
    """Configuration for voice streaming."""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 4096
    format: str = "pcm"  # pcm, wav, mp3
    language: str = "en-US"
    interim_results: bool = True
    continuous: bool = True
    max_silence_ms: int = 2000
    vad_enabled: bool = True  # Voice Activity Detection


# ─── Voice Session ─────────────────────────────────────────────────────────────

@dataclass
class VoiceSession:
    """Represents an active voice streaming session."""
    session_id: str
    config: VoiceStreamConfig = field(default_factory=VoiceStreamConfig)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True
    is_speaking: bool = False
    transcript_buffer: str = ""
    audio_buffer: bytes = b""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "config": {
                "sample_rate": self.config.sample_rate,
                "channels": self.config.channels,
                "format": self.config.format,
                "language": self.config.language,
            },
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "is_active": self.is_active,
            "is_speaking": self.is_speaking,
            "transcript_buffer": self.transcript_buffer,
        }


# ─── Voice Stream Events ───────────────────────────────────────────────────────

class VoiceStreamEvent:
    """Base class for voice stream events."""
    
    def __init__(self, session_id: str, event_type: str, data: Any = None):
        self.session_id = session_id
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class TranscriptEvent(VoiceStreamEvent):
    """Event for speech transcription results."""
    
    def __init__(
        self,
        session_id: str,
        transcript: str,
        is_final: bool = False,
        confidence: float = 0.0,
    ):
        super().__init__(session_id, "transcript", {
            "transcript": transcript,
            "is_final": is_final,
            "confidence": confidence,
        })
        self.transcript = transcript
        self.is_final = is_final
        self.confidence = confidence


class ResponseEvent(VoiceStreamEvent):
    """Event for assistant response."""
    
    def __init__(
        self,
        session_id: str,
        response: str,
        audio_url: str = None,
        is_streaming: bool = False,
    ):
        super().__init__(session_id, "response", {
            "response": response,
            "audio_url": audio_url,
            "is_streaming": is_streaming,
        })


class ErrorEvent(VoiceStreamEvent):
    """Event for errors."""
    
    def __init__(self, session_id: str, error: str, code: str = "error"):
        super().__init__(session_id, "error", {
            "error": error,
            "code": code,
        })


class StatusEvent(VoiceStreamEvent):
    """Event for status updates."""
    
    def __init__(self, session_id: str, status: str, details: Dict = None):
        super().__init__(session_id, "status", {
            "status": status,
            "details": details or {},
        })


# ─── Voice Stream Manager ──────────────────────────────────────────────────────

class VoiceStreamManager:
    """Manages voice streaming sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, VoiceSession] = {}
        self.event_handlers: Dict[str, List[Callable]] = {
            "transcript": [],
            "response": [],
            "error": [],
            "status": [],
            "audio": [],
        }
        self.message_queues: Dict[str, queue.Queue] = {}
        self._lock = threading.Lock()
    
    def create_session(
        self,
        session_id: str = None,
        config: VoiceStreamConfig = None,
    ) -> VoiceSession:
        """Create a new voice streaming session."""
        if session_id is None:
            import secrets
            session_id = secrets.token_urlsafe(12)
        
        with self._lock:
            session = VoiceSession(
                session_id=session_id,
                config=config or VoiceStreamConfig(),
            )
            self.sessions[session_id] = session
            self.message_queues[session_id] = queue.Queue()
        
        self._emit_event(StatusEvent(session_id, "session_created"))
        return session
    
    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id: str) -> bool:
        """Close a voice streaming session."""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.is_active = False
                del self.sessions[session_id]
                
                if session_id in self.message_queues:
                    del self.message_queues[session_id]
                
                self._emit_event(StatusEvent(session_id, "session_closed"))
                return True
        return False
    
    def process_audio_chunk(
        self,
        session_id: str,
        audio_data: bytes,
    ) -> Optional[TranscriptEvent]:
        """Process an audio chunk from the client."""
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return None
        
        session.update_activity()
        session.audio_buffer += audio_data
        
        # Here we would integrate with a speech recognition service
        # For now, we'll simulate with a placeholder
        
        # Check for Voice Activity Detection (VAD)
        if session.config.vad_enabled:
            # Placeholder: In real implementation, analyze audio for speech
            pass
        
        self._emit_event(StatusEvent(session_id, "audio_received", {
            "chunk_size": len(audio_data),
            "buffer_size": len(session.audio_buffer),
        }))
        
        return None
    
    def set_transcript(
        self,
        session_id: str,
        transcript: str,
        is_final: bool = False,
        confidence: float = 0.0,
    ) -> TranscriptEvent:
        """Set transcript for a session (called by speech recognition service)."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        session.transcript_buffer = transcript
        
        event = TranscriptEvent(session_id, transcript, is_final, confidence)
        self._emit_event(event)
        
        if is_final:
            # Clear buffer after final transcript
            session.transcript_buffer = ""
            session.audio_buffer = b""
        
        return event
    
    def send_response(
        self,
        session_id: str,
        response: str,
        audio_url: str = None,
    ) -> ResponseEvent:
        """Send a response to the client."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        event = ResponseEvent(session_id, response, audio_url)
        self._emit_event(event)
        
        # Add to message queue for WebSocket delivery
        if session_id in self.message_queues:
            self.message_queues[session_id].put(event.to_dict())
        
        return event
    
    def get_pending_messages(self, session_id: str) -> List[dict]:
        """Get pending messages for a session."""
        messages = []
        msg_queue = self.message_queues.get(session_id)
        
        if msg_queue:
            while not msg_queue.empty():
                try:
                    messages.append(msg_queue.get_nowait())
                except queue.Empty:
                    break
        
        return messages
    
    def on(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable):
        """Unregister an event handler."""
        if event_type in self.event_handlers:
            if handler in self.event_handlers[event_type]:
                self.event_handlers[event_type].remove(handler)
    
    def _emit_event(self, event: VoiceStreamEvent):
        """Emit an event to all registered handlers."""
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # Don't let handler errors break the flow
    
    def list_sessions(self) -> List[dict]:
        """List all active sessions."""
        return [session.to_dict() for session in self.sessions.values()]


# ─── WebSocket Protocol Messages ───────────────────────────────────────────────

class WebSocketMessage:
    """WebSocket message format for voice streaming."""
    
    @staticmethod
    def create_start_message(session_id: str, config: dict = None) -> dict:
        """Create a session start message."""
        return {
            "type": "start",
            "session_id": session_id,
            "config": config or {},
        }
    
    @staticmethod
    def create_audio_message(session_id: str, audio_base64: str) -> dict:
        """Create an audio chunk message."""
        return {
            "type": "audio",
            "session_id": session_id,
            "audio": audio_base64,
        }
    
    @staticmethod
    def create_text_message(session_id: str, text: str) -> dict:
        """Create a text input message."""
        return {
            "type": "text",
            "session_id": session_id,
            "text": text,
        }
    
    @staticmethod
    def create_stop_message(session_id: str) -> dict:
        """Create a session stop message."""
        return {
            "type": "stop",
            "session_id": session_id,
        }
    
    @staticmethod
    def create_response_message(
        session_id: str,
        response: str,
        audio_url: str = None,
        metadata: dict = None,
    ) -> dict:
        """Create a response message."""
        return {
            "type": "response",
            "session_id": session_id,
            "response": response,
            "audio_url": audio_url,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    @staticmethod
    def create_transcript_message(
        session_id: str,
        transcript: str,
        is_final: bool = False,
    ) -> dict:
        """Create a transcript message."""
        return {
            "type": "transcript",
            "session_id": session_id,
            "transcript": transcript,
            "is_final": is_final,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    @staticmethod
    def create_error_message(session_id: str, error: str, code: str = "error") -> dict:
        """Create an error message."""
        return {
            "type": "error",
            "session_id": session_id,
            "error": error,
            "code": code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ─── Voice Stream Handler ──────────────────────────────────────────────────────

class VoiceStreamHandler:
    """Handler for processing voice stream messages."""
    
    def __init__(self, manager: VoiceStreamManager, chat_callback: Callable = None):
        self.manager = manager
        self.chat_callback = chat_callback
    
    def handle_message(self, message: dict) -> dict:
        """Handle an incoming WebSocket message."""
        msg_type = message.get("type")
        session_id = message.get("session_id")
        
        if msg_type == "start":
            return self._handle_start(message)
        elif msg_type == "audio":
            return self._handle_audio(session_id, message)
        elif msg_type == "text":
            return self._handle_text(session_id, message)
        elif msg_type == "stop":
            return self._handle_stop(session_id)
        else:
            return WebSocketMessage.create_error_message(
                session_id or "unknown",
                f"Unknown message type: {msg_type}",
                "invalid_type"
            )
    
    def _handle_start(self, message: dict) -> dict:
        """Handle session start message."""
        config_data = message.get("config", {})
        config = VoiceStreamConfig(
            sample_rate=config_data.get("sample_rate", 16000),
            channels=config_data.get("channels", 1),
            format=config_data.get("format", "pcm"),
            language=config_data.get("language", "en-US"),
        )
        
        session = self.manager.create_session(config=config)
        
        return {
            "type": "started",
            "session_id": session.session_id,
            "config": config_data,
        }
    
    def _handle_audio(self, session_id: str, message: dict) -> Optional[dict]:
        """Handle audio chunk message."""
        import base64
        
        session = self.manager.get_session(session_id)
        if not session:
            return WebSocketMessage.create_error_message(
                session_id,
                "Session not found",
                "session_not_found"
            )
        
        audio_base64 = message.get("audio", "")
        try:
            audio_data = base64.b64decode(audio_base64)
            self.manager.process_audio_chunk(session_id, audio_data)
        except Exception as e:
            return WebSocketMessage.create_error_message(
                session_id,
                f"Invalid audio data: {str(e)}",
                "invalid_audio"
            )
        
        return None  # No response needed for audio chunks
    
    def _handle_text(self, session_id: str, message: dict) -> dict:
        """Handle text input message."""
        session = self.manager.get_session(session_id)
        if not session:
            return WebSocketMessage.create_error_message(
                session_id,
                "Session not found",
                "session_not_found"
            )
        
        text = message.get("text", "")
        
        # Process through chat callback if available
        if self.chat_callback:
            try:
                result = self.chat_callback(text)
                response = result.get("response", "") if isinstance(result, dict) else str(result)
                
                return WebSocketMessage.create_response_message(
                    session_id,
                    response,
                    metadata=result if isinstance(result, dict) else {"response": response}
                )
            except Exception as e:
                return WebSocketMessage.create_error_message(
                    session_id,
                    f"Chat processing error: {str(e)}",
                    "chat_error"
                )
        
        return WebSocketMessage.create_response_message(
            session_id,
            f"Received: {text}"
        )
    
    def _handle_stop(self, session_id: str) -> dict:
        """Handle session stop message."""
        if self.manager.close_session(session_id):
            return {
                "type": "stopped",
                "session_id": session_id,
            }
        else:
            return WebSocketMessage.create_error_message(
                session_id,
                "Session not found",
                "session_not_found"
            )


# ─── Global Instance ───────────────────────────────────────────────────────────

voice_stream_manager = VoiceStreamManager()


def get_voice_stream_manager() -> VoiceStreamManager:
    """Get the global voice stream manager instance."""
    return voice_stream_manager


def create_voice_handler(chat_callback: Callable = None) -> VoiceStreamHandler:
    """Create a voice stream handler with the global manager."""
    return VoiceStreamHandler(voice_stream_manager, chat_callback)
