import logging
from .baml_client import b
from .baml_client.types import ConversationalAgentInput, ConversationHistory
from austack.core.base import AbstractLLMBase
from typing_extensions import Protocol

logger = logging.getLogger(__name__)

class OnGenerateResponseProtocol(Protocol):
    def __call__(self, text: str) -> None:
        ...

class BamlLLMManager(AbstractLLMBase):
    STOP_CHARS = [".", "?", "!"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prompt = "Only answer in one short coherent sentence."
        self.conversation_history: list[ConversationHistory] = []

    def add_to_conversation_history(self, text: str, role: str):
        self.conversation_history.append(ConversationHistory(role=role, content=text))

    async def generate_response(self, prompt: str):
        logger.debug("LLM generate_response override handler called", extra={"handler": "generate_response", "prompt_length": len(prompt), "prompt": prompt})
        self.add_to_conversation_history(prompt, "user")
        
        stream = b.stream.GenerateResponse(
            input=ConversationalAgentInput(
                conversation_history=self.conversation_history,
                system_prompt=self.prompt,
                user_message=prompt,
            )
        )
        current_index = 0
        current_sentence = ""
        for chunk in stream:
            end = len(chunk)
            if current_index == end:
                continue
            
            current_sentence += chunk[current_index:]
            if current_sentence.strip().endswith(tuple(self.STOP_CHARS)):
                if self.on_sentence:
                    logger.debug("LLM on_sentence callback invoked", extra={"sentence_length": len(current_sentence)})
                    await self.on_sentence(current_sentence)
                current_sentence = ""
            current_index = end
            

        final = stream.get_final_response()
        self.add_to_conversation_history(final, "assistant")
        if self.on_full_response:
            logger.debug("LLM on_full_response callback invoked", extra={"response_length": len(final)})
            await self.on_full_response(final)