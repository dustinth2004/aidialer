import os

from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

from logger_config import get_logger
from services.event_emmiter import EventEmitter

logger = get_logger("Transcription")

class TranscriptionService(EventEmitter):
    """
    Manages the real-time transcription of audio using the Deepgram API.
    """
    def __init__(self):
        """
        Initializes the TranscriptionService.
        """
        super().__init__()
        self.client = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
        self.deepgram_live = None
        self.final_result = ""
        self.speech_final = False
        self.stream_sid = None

    def set_stream_sid(self, stream_id):
        """
        Sets the stream SID for the current transcription.

        Args:
            stream_id (str): The stream SID.
        """
        self.stream_sid = stream_id

    def get_stream_sid(self):
        """
        Gets the current stream SID.

        Returns:
            str: The current stream SID.
        """
        return self.stream_sid

    async def connect(self):
        """
        Connects to the Deepgram live transcription service.
        """
        self.deepgram_live = self.client.listen.asynclive.v("1")
        await self.deepgram_live.start(LiveOptions(
            model="nova-2", 
            language="en-US", 
            encoding="mulaw",
            sample_rate=8000,
            channels=1,
            punctuate=True,
            interim_results=True,
            endpointing=200,
            utterance_end_ms=1000
        ))

        self.deepgram_live.on(LiveTranscriptionEvents.Transcript, self.handle_transcription)
        self.deepgram_live.on(LiveTranscriptionEvents.Error, self.handle_error)
        self.deepgram_live.on(LiveTranscriptionEvents.Close, self.handle_close)
        self.deepgram_live.on(LiveTranscriptionEvents.Warning, self.handle_warning)
        self.deepgram_live.on(LiveTranscriptionEvents.Metadata, self.handle_metadata)
        self.deepgram_live.on(LiveTranscriptionEvents.UtteranceEnd, self.handle_utterance_end)

    async def handle_utterance_end(self, self_obj, utterance_end):
        """
        Handles the utterance end event from Deepgram.

        Args:
            self_obj: The object that triggered the event.
            utterance_end: The utterance end event data.
        """
        try:
            if not self.speech_final:
                logger.info(f"UtteranceEnd received before speech was final, emit the text collected so far: {self.final_result}")
                await self.emit('transcription', self.final_result)
                self.final_result = ''
                self.speech_final = True
                return
            else:
                return
        except Exception as e:
            logger.error(f"Error while handling utterance end: {e}")
            e.print_stack()

    async def handle_transcription(self, self_obj, result):
        """
        Handles transcription results from Deepgram.

        This method processes both interim and final transcription results,
        and emits 'utterance' and 'transcription' events accordingly.

        Args:
            self_obj: The object that triggered the event.
            result: The transcription result data.
        """
        try:
            alternatives = result.channel.alternatives if hasattr(result, 'channel') else []
            text = alternatives[0].transcript if alternatives else ""

            if result.is_final and text.strip():
                self.final_result += f" {text}"
                if result.speech_final:
                    self.speech_final = True
                    await self.emit('transcription', self.final_result)
                    self.final_result = ''
                else:
                    self.speech_final = False
            else:
                if text.strip():
                    stream_sid = self.stream_sid
                    await self.emit('utterance', text, stream_sid)
        except Exception as e:
            logger.error(f"Error while handling transcription: {e}")
            e.print_stack()

            
    async def handle_error(self, self_obj, error):
        """
        Handles errors from the Deepgram connection.

        Args:
            self_obj: The object that triggered the event.
            error: The error data.
        """
        logger.error(f"Deepgram error: {error}")
        self.is_connected = False
    
    async def handle_warning(self, self_obj, warning):
        """
        Handles warnings from the Deepgram connection.

        Args:
            self_obj: The object that triggered the event.
            warning: The warning data.
        """
        logger.info('Deepgram warning:', warning)

    async def handle_metadata(self, self_obj, metadata):
        """
        Handles metadata from the Deepgram connection.

        Args:
            self_obj: The object that triggered the event.
            metadata: The metadata.
        """
        logger.info('Deepgram metadata:', metadata)

    async def handle_close(self, self_obj, close):
        """
        Handles the close event from the Deepgram connection.

        Args:
            self_obj: The object that triggered the event.
            close: The close event data.
        """
        logger.info("Deepgram connection closed")
        self.is_connected = False

    async def send(self, payload: bytes):
        """
        Sends audio data to the Deepgram service.

        Args:
            payload (bytes): The audio data to send.
        """
        if self.deepgram_live:            
            await self.deepgram_live.send(payload)
    
    async def disconnect(self):
        """
        Disconnects from the Deepgram service.
        """
        if self.deepgram_live:
            await self.deepgram_live.finish()
            self.deepgram_live = None
        self.is_connected = False
        logger.info("Disconnected from Deepgram")