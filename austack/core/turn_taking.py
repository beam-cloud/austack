import logging
from .base import AbstractLLMBase

logger = logging.getLogger(__name__)


class TurnTakingManager:
    def __init__(self):
        self.is_agent_turn = False

    async def reset(self):
        self.is_agent_turn = False

    def start_agent_turn(self):
        self.is_agent_turn = True
        logger.info("Agent turn started")
        logger.debug("Agent turn started")

    async def start_user_turn(self, llm_manager: AbstractLLMBase):
        if self.is_agent_turn:
            # Interrupt the agent if it was speaking
            await llm_manager.interrupt(save_in_conversation=True)
        logger.info("User turn started")
        self.is_agent_turn = False
        logger.debug("User turn started")
