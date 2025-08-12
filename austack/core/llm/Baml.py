import asyncio
import logging
from .baml_client import b
from .baml_client.types import ConversationalAgentInput, ConversationHistory
from austack.core.base import AbstractLLMBase
from typing_extensions import Protocol

logger = logging.getLogger(__name__)


class OnGenerateResponseProtocol(Protocol):
    def __call__(self, text: str) -> None: ...


class BamlLLMManager(AbstractLLMBase):
    STOP_CHARS = [".", "?", "!"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prompt = "Only answer in one short coherent sentence."
        self.conversation_history: list[ConversationHistory] = []
        self.current_stream = None
        self.generated_sentences = []
        self.generating = False

    def add_to_conversation_history(self, text: str, role: str):
        self.conversation_history.append(ConversationHistory(role=role, content=text))

    async def generate_response(self, prompt: str):
        logger.debug(
            "LLM generate_response override handler called",
            extra={"handler": "generate_response", "prompt_length": len(prompt), "prompt": prompt},
        )
        self.add_to_conversation_history(prompt, "user")

        logger.info("Current conversation history:")
        for message in self.conversation_history:
            logger.info(f"{message.role}: {message.content}")

        self.generated_sentences = []
        self.generating = True
        self.current_stream = b.stream.GenerateResponse(
            input=ConversationalAgentInput(
                conversation_history=self.conversation_history,
                system_prompt=self.prompt,
                user_message=prompt,
            )
        )
        current_index = 0
        current_sentence = ""

        for chunk in self.current_stream:
            if not self.generating:
                return

            end = len(chunk)
            if current_index == end:
                continue

            current_sentence += chunk[current_index:]
            if current_sentence.strip().endswith(tuple(self.STOP_CHARS)):
                self.generated_sentences.append(current_sentence)
                if self.on_sentence:
                    logger.debug(
                        "LLM on_sentence callback invoked",
                        extra={"sentence_length": len(current_sentence)},
                    )
                    await self.on_sentence(current_sentence)
                current_sentence = ""
            current_index = end

        final = self.current_stream.get_final_response()
        self.add_to_conversation_history(final, "assistant")
        if self.on_full_response:
            logger.debug("LLM on_full_response callback invoked", extra={"response_length": len(final)})
            await self.on_full_response(final)

    async def interrupt(self, save_in_conversation: bool = True):
        logger.debug(f"LLM interrupted, save_in_conversation={save_in_conversation}")
        self.generating = False

        if save_in_conversation and self.generated_sentences:
            # Save partial response to conversation history
            partial_response = " ".join(self.generated_sentences) + " (interrupted)"
            self.add_to_conversation_history(partial_response, "assistant")
            logger.debug(f"Saved interrupted response: {partial_response}")

        # Clear state
        self.generated_sentences = []
