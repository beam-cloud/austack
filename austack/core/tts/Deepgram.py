import asyncio
import logging
import os
from typing import Any
from typing_extensions import Protocol


import dotenv
from deepgram import (
    DeepgramClient,
    SpeakWebSocketEvents,
)
from austack.core.base import AsyncTextToSpeechBase

dotenv.load_dotenv()

logger = logging.getLogger(__name__)


class OnAudioDataProtocol(Protocol):
    def __call__(self, audio: bytes) -> None: ...


class DeepgramTextToSpeechManager(AsyncTextToSpeechBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_running = False
        self.dg_connection = None
        self.text_buffer = ""

    async def start(self):
        deepgram: DeepgramClient = DeepgramClient(
            os.getenv("DEEPGRAM_API_KEY", ""),
        )
        self.dg_connection = deepgram.speak.asyncwebsocket.v("1")

        async def on_binary_data(cls, data: Any, **kwargs):
            # logger.debug("TTS on_binary_data handler called", extra={"handler": "on_binary_data", "data_size": len(data)})
            if self.on_partial:
                await self.on_partial(data)

        async def on_error(cls, error: Any, **kwargs):
            logger.debug("TTS on_error handler called", extra={"handler": "on_error"})
            logger.error(f"Deepgram TTS Error: {error}")

        self.dg_connection.on(SpeakWebSocketEvents.AudioData, on_binary_data)
        self.dg_connection.on(SpeakWebSocketEvents.Error, on_error)

        if not await self.dg_connection.start(
            {
                "model": "aura-2-thalia-en",
                "encoding": "linear16",
                "sample_rate": 16000,
            }
        ):
            raise Exception("Failed to start Deepgram TTS connection")

        while not await self.dg_connection.is_connected():
            await asyncio.sleep(0.1)

        self.is_running = True

    async def synthesize(self, text: str):
        try:
            logger.info(f"Sending text to Deepgram TTS: {text}")
            if self.dg_connection and await self.dg_connection.is_connected():
                await self.dg_connection.send_text(text)
                await self.dg_connection.flush()
        except Exception as e:
            logger.error(f"Error in synthesize: {e}")

    async def stop(self):
        self.is_running = False
        if self.dg_connection:
            await self.dg_connection.finish()  # type: ignore
