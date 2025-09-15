
import base64
import os
from abc import ABC, abstractmethod
from typing import Any, Dict

import aiohttp
import numpy as np
from deepgram import DeepgramClient, LiveOptions
from dotenv import load_dotenv

from logger_config import get_logger
from services.event_emmiter import EventEmitter

load_dotenv()
logger = get_logger("TTS")


class AbstractTTSService(EventEmitter, ABC):
    """
    Abstract base class for Text-to-Speech (TTS) services.
    """
    @abstractmethod
    async def generate(self, llm_reply: Dict[str, Any], interaction_count: int):
        """
        Abstract method to generate audio from text.

        Args:
            llm_reply (Dict[str, Any]): The reply from the LLM, containing the text to synthesize.
            interaction_count (int): The current interaction count.
        """
        pass

    @abstractmethod
    async def set_voice(self, voice_id: str):
        """
        Abstract method to set the voice for the TTS service.

        Args:
            voice_id (str): The ID of the voice to use.
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """
        Abstract method to disconnect from the TTS service.
        """
        pass

class ElevenLabsTTS(AbstractTTSService):
    """
    TTS service implementation using the ElevenLabs API.
    """
    def __init__(self):
        """
        Initializes the ElevenLabsTTS service.
        """
        super().__init__()
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.model_id = os.getenv("ELEVENLABS_MODEL_ID")
        self.speech_buffer = {}


    def set_voice(self, voice_id):
        """
        Sets the voice for the ElevenLabs TTS service.

        Args:
            voice_id (str): The ID of the voice to use.
        """
        self.voice_id = voice_id

    async def disconnect(self):
        """
        Disconnects from the TTS service. For ElevenLabs, this is a no-op.
        """
        # ElevenLabs client doesn't require explicit disconnection
        return


    async def generate(self, llm_reply: Dict[str, Any], interaction_count: int):
        """
        Generates audio from text using the ElevenLabs API.

        Args:
            llm_reply (Dict[str, Any]): The reply from the LLM, containing the text to synthesize.
            interaction_count (int): The current interaction count.
        """
        partial_response_index, partial_response = llm_reply['partialResponseIndex'], llm_reply['partialResponse']

        if not partial_response:
            return

        try:
            output_format = "ulaw_8000"            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/wav"
            }
            params = {
                "output_format": output_format,
                "optimize_streaming_latency": 4
            }
            data = {
                "model_id": self.model_id,
                "text": partial_response
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, params=params, json=data) as response:
                    if response.status == 200:
                        audio_content = await response.read()
                        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
                        await self.emit('speech', partial_response_index, audio_base64, partial_response, interaction_count)
        except Exception as err:
            logger.error("Error occurred in ElevenLabs TTS service", exc_info=True)
            logger.error(str(err))


class DeepgramTTS(AbstractTTSService):
    """
    TTS service implementation using the Deepgram API.
    """
    def __init__(self):
        """
        Initializes the DeepgramTTS service.
        """
        super().__init__()
        self.client = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))

    async def generate(self, llm_reply, interaction_count):
        """
        Generates audio from text using the Deepgram API.

        Args:
            llm_reply (Dict[str, Any]): The reply from the LLM, containing the text to synthesize.
            interaction_count (int): The current interaction count.
        """
        partial_response_index = llm_reply['partialResponseIndex']
        partial_response = llm_reply['partialResponse']

        if not partial_response:
            return

        try:
            source = {
                "text": partial_response
            }

            options = {
                "model": "aura-asteria-en",
                "encoding": "mulaw", 
                "sample_rate": 8000 
            }
            
            response = await self.client.asyncspeak.v("1").stream(
                source={"text": partial_response},
                options=options
            )

            if response.stream:
                audio_content = response.stream.getvalue()
                
                # Convert audio to numpy array
                audio_array = np.frombuffer(audio_content, dtype=np.uint8)
                
                # Trim the first 10ms (80 samples at 8000Hz) to remove the initial noise
                trim_samples = 80
                trimmed_audio = audio_array[trim_samples:]
                
                # Convert back to bytes
                trimmed_audio_bytes = trimmed_audio.tobytes()

                audio_base64 = base64.b64encode(trimmed_audio_bytes).decode('utf-8')
                await self.emit('speech', partial_response_index, audio_base64, partial_response, interaction_count)
            else:
                logger.error("Error in TTS generation: No audio stream returned")

        except Exception as e:
            logger.error(f"Error in TTS generation: {str(e)}")


    async def set_voice(self, voice_id):
        """
        Sets the voice for the Deepgram TTS service.
        Note: Deepgram TTS does not currently support direct voice selection via this method.

        Args:
            voice_id (str): The ID of the voice to use.
        """
        logger.info(f"Attempting to set voice to {voice_id}, but Deepgram TTS doesn't support direct voice selection.")
        # TODO(akiani): Implement voice selection in Deepgram TTS

    async def disconnect(self):
        """
        Disconnects from the TTS service. For Deepgram, this is a no-op.
        """
        # Deepgram client doesn't require explicit disconnection
        logger.info("DeepgramTTS service disconnected")


class TTSFactory:
    """
    Factory class for creating TTS service instances.
    """
    @staticmethod
    def get_tts_service(service_name: str) -> AbstractTTSService:
        """
        Returns an instance of a TTS service based on the service name.

        Args:
            service_name (str): The name of the TTS service to create (e.g., 'elevenlabs', 'deepgram').

        Returns:
            AbstractTTSService: An instance of the requested TTS service.

        Raises:
            ValueError: If the service name is not supported.
        """
        if service_name.lower() == "elevenlabs":
            return ElevenLabsTTS()
        elif service_name.lower() == "deepgram":
            return DeepgramTTS()
        else:
            raise ValueError(f"Unsupported TTS service: {service_name}")

# Usage in your main application
tts_service_name = os.getenv("TTS_SERVICE", "deepgram")  # Default to deepgram if not specified
tts_service = TTSFactory.get_tts_service(tts_service_name)