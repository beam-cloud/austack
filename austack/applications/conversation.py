import logging
from typing import Optional
from fastapi import WebSocket, WebSocketException
from austack.core.base import (
    AsyncSpeechToTextBase,
    AsyncTextToSpeechBase,
    AbstractLLMBase,
    OnTranscriptProtocol,
    OnAudioDataProtocol,
    OnGenerateResponseProtocol,
)
from austack.core.stt.Deepgram import DeepgramSpeechToTextManager
from austack.core.tts.Deepgram import DeepgramTextToSpeechManager
from austack.core.llm.Baml import BamlLLMManager
from austack.core.turn_taking import TurnTakingManager

logger = logging.getLogger(__name__)


class ConversationApp:
    def __init__(
        self,
        websocket: WebSocket,
        stt: AsyncSpeechToTextBase | None = None,
        llm: AbstractLLMBase | None = None,
        tts: AsyncTextToSpeechBase | None = None,
        on_llm_sentence: Optional[OnGenerateResponseProtocol] = None,
        on_stt_full_transcript: Optional[OnTranscriptProtocol] = None,
        on_tts_partial_audio: Optional[OnAudioDataProtocol] = None,
    ):
        self.websocket = websocket
        self.is_running = False

        # Initialize components
        self.stt = stt or DeepgramSpeechToTextManager()
        self.tts = tts or DeepgramTextToSpeechManager()
        self.llm = llm or BamlLLMManager()

        # Initialize turn taking manager
        self.turn_taking_manager = TurnTakingManager()

        # Setup callbacks
        self.stt.setup(on_final=self.on_stt_full_transcript, on_partial=self.on_stt_partial_transcript)
        self.tts.setup(on_partial=self.on_tts_partial_audio)
        self.llm.setup(on_sentence=on_llm_sentence or self.on_llm_sentence)

    async def on_stt_full_transcript(self, transcript: str):
        # logger.debug(f"STT final transcript: {transcript}")
        logger.info(f"STT final transcript: {transcript}")
        self.turn_taking_manager.start_agent_turn()
        await self.llm.generate_response(transcript)

    async def on_stt_partial_transcript(self, transcript: str):
        # logger.debug(f"STT partial transcript: {transcript}")
        logger.info(f"STT partial transcript: {transcript}")
        await self.turn_taking_manager.start_user_turn(self.llm)

    async def on_llm_sentence(self, text: str):
        # logger.debug(f"LLM sentence: {text}")
        logger.info(f"LLM sentence: {text}")
        if self.turn_taking_manager.is_agent_turn:
            await self.tts.synthesize(text)
        else:
            # logger.debug("Blocked LLM sentence - not agent turn")
            logger.info("Blocked LLM sentence - not agent turn")

    async def on_tts_partial_audio(self, audio: bytes):
        if self.turn_taking_manager.is_agent_turn:
            # logger.debug(f"Sending audio to websocket: {len(audio)} bytes")
            logger.info(f"Sending audio to websocket: {len(audio)} bytes")
            await self.websocket.send_bytes(audio)
        else:
            # logger.debug("Blocked TTS audio - not agent turn")
            logger.info("Blocked TTS audio - not agent turn")

    async def start(self):
        self.is_running = True

        await self.stt.start()
        await self.tts.start()

        while self.is_running:
            try:
                data = await self.websocket.receive()

                if "bytes" in data:
                    await self.stt.add_audio_chunk(data["bytes"])
                    continue
                elif "text" in data:
                    pass
                else:
                    logger.error(f"Unknown message type: {data}")
            except WebSocketException:
                logger.info("Client disconnected")
                break
            except BaseException as e:
                logger.error(f"Error receiving data: {e}")
                break

        await self.stop()

    async def stop(self):
        self.is_running = False
        await self.turn_taking_manager.reset()
        await self.stt.stop()
        await self.tts.stop()
