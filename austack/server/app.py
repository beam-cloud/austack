import logging
from typing import Optional
from fastapi import FastAPI, WebSocket
from austack.applications.conversation import ConversationApp

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AuStackApp:
    def __init__(
        self,
        app: Optional[FastAPI] = None,
        websocket_endpoint: str = "/ws/conversation",
        include_health_endpoint: bool = True,
        include_root_endpoint: bool = True,
    ):
        self.app = app or FastAPI(title="AuStack Conversation API", version="1.0.0")
        self.websocket_endpoint = websocket_endpoint

        self._add_routes(include_health_endpoint, include_root_endpoint)

    def _add_routes(self, include_health: bool, include_root: bool):
        if include_root:

            @self.app.get("/")
            async def root():  # type: ignore
                return {
                    "message": "AuStack Conversation API",
                    "endpoints": {
                        "conversation": self.websocket_endpoint,
                        "health": "/health" if include_health else None,
                    },
                }

        if include_health:

            @self.app.get("/health")
            async def health():  # type: ignore
                return {
                    "status": "healthy",
                }

        @self.app.websocket(self.websocket_endpoint)
        async def websocket_endpoint(websocket: WebSocket):  # type: ignore
            await websocket.accept()
            conversation = ConversationApp(websocket=websocket)
            try:
                await conversation.start()
            except Exception as e:
                logger.error(f"Error in websocket connection: {e}")

    def get_app(self) -> FastAPI:
        return self.app


# Default app instance for backward compatibility
austack_app = AuStackApp()
app = austack_app.get_app()

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
