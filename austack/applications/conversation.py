import logging
from typing import Optional
from fastapi import WebSocket, WebSocketException
from austack.core.base import AsyncSpeechToTextBase, AsyncTextToSpeechBase, AbstractLLMBase, OnTranscriptProtocol, OnAudioDataProtocol, OnGenerateResponseProtocol
from austack.core.stt.Deepgram import DeepgramSpeechToTextManager
from austack.core.tts.Deepgram import DeepgramTextToSpeechManager
from austack.core.llm.Baml import BamlLLMManager

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
        on_tts_partial_audio: Optional[OnAudioDataProtocol] = None
    ):
        self.websocket = websocket
        self.is_running = False
        
        self.stt = (stt or DeepgramSpeechToTextManager()).setup(on_final=on_stt_full_transcript or self.on_stt_full_transcript)
        self.tts = (tts or DeepgramTextToSpeechManager()).setup(on_partial=on_tts_partial_audio or self.on_tts_partial_audio)
        self.llm = (llm or BamlLLMManager()).setup(on_sentence=on_llm_sentence or self.on_llm_sentence)
    
    async def on_llm_sentence(self, text: str):
        logger.debug("Conversation on_llm_sentence override handler called", extra={"handler": "on_llm_sentence", "text_length": len(text)})
        await self.tts.synthesize(text)
    
    async def on_stt_full_transcript(self, transcript: str):
        logger.debug("Conversation on_stt_full_transcript override handler called", extra={"handler": "on_stt_full_transcript", "transcript_length": len(transcript)})
        await self.llm.generate_response(transcript)
    
    async def on_tts_partial_audio(self, audio: bytes):
        logger.debug("Conversation on_tts_partial_audio override handler called", extra={"handler": "on_tts_partial_audio", "audio_size": len(audio)})
        await self.websocket.send_bytes(audio)
    
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
                else:
                    logger.error(f"Unknown message type: {data}")
            except WebSocketException:
                logger.info("Client disconnected")
                self.is_running = False
                break
            except BaseException as e:
                logger.error(f"Error receiving data: {e}")
                self.is_running = False
                break

    async def stop(self):
        self.is_running = False
        await self.stt.stop()
        await self.tts.stop()