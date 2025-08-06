import os
import asyncio
import logging
from typing import Any
import time

import dotenv
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveOptions,
    LiveTranscriptionEvents,
)

from typing_extensions import Protocol
from austack.core.base import AsyncSpeechToTextBase

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

class OnTranscriptProtocol(Protocol):
    def __call__(self, transcript: str) -> None:
        ...

class DeepgramSpeechToTextManager(AsyncSpeechToTextBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audio_queue = asyncio.Queue()
        self.is_running = False
        self.current_sentence = ""
        self.process_audio_task = None

    async def start(self):
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram: DeepgramClient = DeepgramClient(os.getenv("DEEPGRAM_API_KEY", ""), config)
        self.dg_connection = deepgram.listen.asyncwebsocket.v("1")
        self.last_speech_start_time = time.time()
    
        async def on_message(*_, result: Any, **__):
            logger.debug("STT on_message handler called", extra={"handler": "on_message"})
            sentence = result.channel.alternatives[0].transcript
            if result.speech_final:
                self.current_sentence += sentence
                if not self.current_sentence:
                    self.last_speech_start_time = time.time()
                
        async def on_speech_started(result: Any, *_, **__):
            logger.debug("STT on_speech_started handler called", extra={"handler": "on_speech_started"})
            logger.info(f"Speech started: {result}")

        async def on_utterance_end(result: Any, *_, **__):
            logger.debug("STT on_utterance_end handler called", extra={"handler": "on_utterance_end", "transcript_length": len(self.current_sentence)})
            logger.info(f"Utterance end: {result}")
            if self.on_final:
                await self.on_final(self.current_sentence)
            self.current_sentence = ""
            logger.info(f"Speech end: {time.time() - self.last_speech_start_time}")

        self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)  # type: ignore
        self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)  # type: ignore
        self.dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)  # type: ignore

        if not await self.dg_connection.start(  # type: ignore
            LiveOptions(
                model="nova-3",
                smart_format=True,
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="1000",
            )
        ):  # type: ignore
            logger.error("Failed to start Deepgram connection")

        while not await self.dg_connection.is_connected():  # type: ignore
            await asyncio.sleep(0.1)

        self.is_running = True
        self.process_audio_task = asyncio.create_task(self.process_audio())
        logger.debug("STT start handler called", extra={"handler": "start"})

    async def process_audio(self):
        while self.is_running:
            try:
                audio = await asyncio.wait_for(self.audio_queue.get(), timeout=0.5)
                if audio:
                    await self.dg_connection.send(audio)  # type: ignore
                    await self.dg_connection.flush()  # type: ignore
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("STT process_audio handler error", extra={"handler": "process_audio", "error": e})
                continue

    async def add_audio_chunk(self, audio: bytes):
        logger.debug("STT add_audio_chunk handler called", extra={"handler": "add_audio_chunk", "audio_size": len(audio)})
        await self.audio_queue.put(audio)
    
    async def stop(self):
        self.is_running = False
        if self.process_audio_task:
            self.process_audio_task.cancel()
        await self.dg_connection.finish()  # type: ignore 
