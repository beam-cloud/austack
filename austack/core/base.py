from abc import ABC, abstractmethod
from typing import Protocol, Coroutine, Any


class OnTranscriptProtocol(Protocol):
    def __call__(self, transcript: str) -> Coroutine[Any, Any, None]: ...


class OnGenerateResponseProtocol(Protocol):
    def __call__(self, text: str) -> Coroutine[Any, Any, None]: ...


class OnAudioDataProtocol(Protocol):
    def __call__(self, audio: bytes) -> Coroutine[Any, Any, None]: ...


class AbstractBackgroundTask(ABC):
    @abstractmethod
    async def start(self):
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        raise NotImplementedError


class AsyncSpeechToTextBase(AbstractBackgroundTask):
    def __init__(self, **kwargs):
        self.on_partial = None
        self.on_final = None

    def setup(self, on_partial: OnTranscriptProtocol | None = None, on_final: OnTranscriptProtocol | None = None):
        self.on_partial = on_partial
        self.on_final = on_final
        return self

    @abstractmethod
    async def start(self):
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        raise NotImplementedError

    @abstractmethod
    async def add_audio_chunk(self, audio: bytes):
        raise NotImplementedError


class AbstractLLMBase(ABC):
    def __init__(self, **kwargs):
        self.on_sentence = None
        self.on_full_response = None

    def setup(self, on_sentence: OnGenerateResponseProtocol | None = None, on_full_response: OnGenerateResponseProtocol | None = None):
        self.on_sentence = on_sentence
        self.on_full_response = on_full_response
        return self

    @abstractmethod
    async def generate_response(self, prompt: str):
        raise NotImplementedError


class AsyncTextToSpeechBase(AbstractBackgroundTask):
    def __init__(self, **kwargs):
        self.on_partial = None
        self.on_final = None

    def setup(self, on_partial: OnAudioDataProtocol | None = None, on_final: OnAudioDataProtocol | None = None):
        self.on_partial = on_partial
        self.on_final = on_final
        return self

    @abstractmethod
    async def synthesize(self, text: str):
        raise NotImplementedError
