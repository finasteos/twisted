"""
Gemini 2.5 Flash Native Audio integration for TWISTED.
Real-time voice interaction with the Glass Engine.
"""

import asyncio
import base64
import json
import logging
from typing import AsyncGenerator, Callable, Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

import websockets
from google.genai import types

logger = logging.getLogger("twisted.audio")

class AudioSessionState(Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class AudioTranscript:
    text: str
    is_final: bool
    confidence: float
    speaker: str  # "user" | "assistant"


class GeminiLiveAudioGateway:
    """
    Real-time bidirectional audio with Gemini 2.5 Flash.

    Capabilities:
    - Voice input for case queries ("Help Sarah with...")
    - Spoken explanations of strategy
    - Hands-free interaction during document review
    - Emotional tone detection in user's voice
    """

    MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"

    def __init__(self, gemini_api_key: str, case_context: Optional[dict] = None):
        self.api_key = gemini_api_key
        self.case_context = case_context
        self.session_state = AudioSessionState.IDLE
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.audio_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.transcript_callbacks: List[Callable[[AudioTranscript], Any]] = []
        self.output_callback: Optional[Callable[[bytes], Any]] = None

    async def start_session(
        self,
        system_prompt: Optional[str] = None,
        voice_type: str = "Puck"  # Puck, Charon, Kore, Fenrir, Aoede
    ):
        """
        Initialize live audio session with Gemini.
        """
        self.session_state = AudioSessionState.CONNECTING
        logger.info(f"🎙️ Starting Gemini Live Audio session with voice: {voice_type}")

        # Connect to Gemini Live API WebSocket
        ws_url = (
            f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
            f"?key={self.api_key}"
        )

        try:
            self.websocket = await websockets.connect(ws_url)

            # Send initial setup message
            setup_message = {
                "setup": {
                    "model": f"models/{self.MODEL}",
                    "generation_config": {
                        "response_modalities": ["AUDIO"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": voice_type
                                }
                            }
                        }
                    },
                    "system_instruction": {
                        "parts": [{
                            "text": system_prompt or self._default_system_prompt()
                        }]
                    }
                }
            }

            await self.websocket.send(json.dumps(setup_message))

            # Start audio I/O loops
            self.session_state = AudioSessionState.LISTENING
            asyncio.create_task(self._audio_input_loop())
            asyncio.create_task(self._audio_output_loop())

        except Exception as e:
            logger.error(f"Failed to start audio session: {e}")
            self.session_state = AudioSessionState.ERROR
            raise

    def _default_system_prompt(self) -> str:
        """TWISTED-specific voice personality."""
        return """You are TWISTED, a Glass Engine for complex case resolution.
You speak with calm authority, precise clarity, and genuine empathy.
You never rush. You pause for understanding.
You reference visual elements on screen: "As you see in the Event Log..."
You acknowledge emotion: "This sounds frustrating" or "This is significant."
You guide, don't lecture. Ask: "Shall I explain the strategy, or would you prefer to see the timeline first?"
Your voice is warm, professional, unhurried."""

    async def _audio_input_loop(self):
        """
        Stream microphone audio to Gemini.
        """
        try:
            while self.session_state != AudioSessionState.ERROR and self.websocket:
                # Get audio chunk from queue
                audio_chunk = await self.audio_queue.get()

                # Base64 encode for JSON transmission
                b64_audio = base64.b64encode(audio_chunk).decode()

                message = {
                    "realtime_input": {
                        "media_chunks": [{
                            "mime_type": "audio/pcm",
                            "data": b64_audio
                        }]
                    }
                }

                await self.websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            logger.info("Audio input WebSocket closed")
        except Exception as e:
            logger.error(f"Error in audio input loop: {e}")
            self.session_state = AudioSessionState.ERROR

    async def _audio_output_loop(self):
        """
        Receive and process Gemini's audio responses.
        """
        try:
            async for message in self.websocket:
                data = json.loads(message)

                # Handle server content (Gemini's response)
                if "server_content" in data:
                    content = data["server_content"]

                    # Audio output
                    if "model_turn" in content and "parts" in content["model_turn"]:
                        for part in content["model_turn"]["parts"]:
                            if "inline_data" in part and "data" in part["inline_data"]:
                                audio_b64 = part["inline_data"]["data"]
                                audio_bytes = base64.b64decode(audio_b64)

                                # Stream to output callback (e.g., frontend WebSocket)
                                if self.output_callback:
                                    await self.output_callback(audio_bytes)
                                self.session_state = AudioSessionState.SPEAKING

                    # Transcript handling (Note: Gemini Live API format might vary slightly)
                    # This is a general implementation based on expected BidiGenerateContent structure

                    # Turn completion
                    if content.get("model_turn", {}).get("done", False):
                        self.session_state = AudioSessionState.LISTENING

                # Handle user transcription (what user said)
                # In BidiGenerateContent, this is often part of the stream update
                if "user_transcript" in data:
                    transcript = AudioTranscript(
                        text=data["user_transcript"],
                        is_final=True,
                        confidence=data.get("confidence", 0.9),
                        speaker="user"
                    )
                    for cb in self.transcript_callbacks:
                        await cb(transcript)

        except websockets.exceptions.ConnectionClosed:
            logger.info("Audio output WebSocket closed")
        except Exception as e:
            logger.error(f"Error in audio output loop: {e}")
            self.session_state = AudioSessionState.ERROR

    async def inject_context_update(self, context: dict):
        """
        Update Gemini's context mid-session (e.g., analysis complete).
        """
        if not self.websocket:
            return

        message = {
            "realtime_input": {
                "media_chunks": [{
                    "mime_type": "text/plain",
                    "data": base64.b64encode(
                        f"[SYSTEM UPDATE] {json.dumps(context)}".encode()
                    ).decode()
                }]
            }
        }
        await self.websocket.send(json.dumps(message))

    async def close(self):
        """Graceful session termination."""
        if self.websocket:
            await self.websocket.close()
        self.session_state = AudioSessionState.IDLE
        logger.info("🎙️ Audio session closed")
