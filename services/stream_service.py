import uuid
from typing import Dict

from fastapi import WebSocket

from logger_config import get_logger
from services.event_emmiter import EventEmitter

logger = get_logger("Stream")

class StreamService(EventEmitter):
    """
    Manages the audio stream to and from the WebSocket.

    This service buffers incoming audio and sends it in the correct order,
    and also sends outgoing audio to the WebSocket.
    """
    def __init__(self, websocket: WebSocket):
        """
        Initializes the StreamService.

        Args:
            websocket (WebSocket): The WebSocket connection object.
        """
        super().__init__()
        self.ws = websocket
        self.expected_audio_index = 0
        self.audio_buffer: Dict[int, str] = {}
        self.stream_sid = ''

    def set_stream_sid(self, stream_sid: str):
        """
        Sets the stream SID for the current stream.

        Args:
            stream_sid (str): The stream SID.
        """
        self.stream_sid = stream_sid

    async def buffer(self, index: int, audio: str):
        """
        Buffers incoming audio and sends it in order.

        If the audio chunk is the expected one, it's sent immediately.
        Otherwise, it's buffered until the expected chunk arrives.

        Args:
            index (int): The index of the audio chunk.
            audio (str): The base64-encoded audio data.
        """
        if index is None:
            await self.send_audio(audio)
        elif index == self.expected_audio_index:
            await self.send_audio(audio)
            self.expected_audio_index += 1

            while self.expected_audio_index in self.audio_buffer:
                buffered_audio = self.audio_buffer[self.expected_audio_index]
                await self.send_audio(buffered_audio)
                del self.audio_buffer[self.expected_audio_index]
                self.expected_audio_index += 1
        else:
            self.audio_buffer[index] = audio

    def reset(self):
        """Resets the audio buffer and expected index."""
        self.expected_audio_index = 0
        self.audio_buffer = {}

    async def send_audio(self, audio: str):
        """
        Sends an audio chunk to the WebSocket.

        Args:
            audio (str): The base64-encoded audio data to send.
        """
        await self.ws.send_json({
            "streamSid": self.stream_sid,
            "event": "media",
            "media": {
                "payload": audio
            }
        })

        mark_label = str(uuid.uuid4())

        await self.ws.send_json({
            "streamSid": self.stream_sid,
            "event": "mark",
            "mark": {
                "name": mark_label
            }
        })

        await self.emit('audiosent', mark_label)