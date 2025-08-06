import json
import time
from typing import Optional

import websocket

from .audio.interface import AudioInterface
from .audio.config import AudioConfig


class ConversationClient:
    """
    Main client for handling audio conversations via WebSocket.
    
    Integrates audio input/output with WebSocket communication for real-time
    conversational AI interactions.
    """
    
    def __init__(
        self, 
        websocket_url: str,
        audio_config: Optional[AudioConfig] = None,
        connection_timeout: int = 10,
    ):
        """
        Initialize the conversation client.
        
        Args:
            websocket_url: WebSocket server URL for conversation
            audio_config: Audio configuration settings. If None, uses defaults.
            connection_timeout: WebSocket connection timeout in seconds
        """
        self.websocket_url = websocket_url
        self.running = False
        self.connection_timeout = connection_timeout
        self.audio_config = audio_config or AudioConfig.create_default()
        self.websocket = None
        
        self.audio_interface = AudioInterface(
            input_callback=self._on_audio_input,
            audio_config=self.audio_config,
        )

    def _on_audio_input(self, audio_data: bytes):
        if self.websocket:
            self.send_audio_data(audio_data)

    def _on_audio_received(self, audio_data: bytes):
        self.audio_interface.play(audio_data)

    def connect(self):
        if self.websocket:
            return

        try:
            self.websocket = websocket.create_connection(
                self.websocket_url,
                timeout=self.connection_timeout,
                enable_multithread=True
            )
            # Set a shorter timeout for recv() operations
            self.websocket.settimeout(0.1)
            
            print(f"Connected to WebSocket: {self.websocket_url}")
        except Exception as e:
            print(f"Error connecting to websocket: {e}")
            raise

    def send_audio_data(self, audio_data: bytes):
        """Send audio data over WebSocket."""
        if not self.websocket or not self.running:
            print("Cannot send audio: WebSocket not connected")
            return
            
        try:
            self.websocket.send(audio_data, opcode=websocket.ABNF.OPCODE_BINARY)
        except websocket.WebSocketConnectionClosedException:
            print("Cannot send audio: WebSocket connection closed")
        except Exception as e:
            print(f"Error sending audio data: {e}")

    def send_message(self, message: dict):
        if not self.websocket or not self.running:
            print("Cannot send message: WebSocket not connected")
            return
            
        try:
            message_str = json.dumps(message)
            self.websocket.send(message_str)
        except websocket.WebSocketConnectionClosedException:
            print("Cannot send message: WebSocket connection closed")
        except Exception as e:
            print(f"Error sending message: {e}")

    def send_stop_speaking_signal(self):
        self.send_message({"type": "on_user_stop_speaking"})

    def disconnect(self):
        self.running = False
            
        if self.websocket:
            try:
                self.websocket.close()
            except Exception:
                pass
            self.websocket = None

    def start_conversation(self):
        try:
            self.connect()
            self.audio_interface.start()
            
            self.running = True
            print(f"Conversation started with {self.websocket_url}")
            print("Press Ctrl+C to stop the conversation")
            
            while self.running:
                try:
                    message = self.websocket.recv()
                    if isinstance(message, bytes):
                        self._on_audio_received(message)
                    elif isinstance(message, str):
                        try:
                            data = json.loads(message)
                            print(f"Received message: {data}")
                        except json.JSONDecodeError:
                            print(f"Received non-JSON text message: {message}")
                except websocket.WebSocketTimeoutException:
                    break
                except websocket.WebSocketConnectionClosedException:
                    self.running = False
                except ConnectionResetError:
                    self.running = False
                except Exception as e:
                    print(f"Error during conversation: {e}")
                
        except KeyboardInterrupt:
            print("\nKeyboard interrupt - stopping conversation")
        except Exception as e:
            print(f"Error during conversation: {e}")  
        finally:
            self.stop_conversation()

    def stop_conversation(self):
        self.audio_interface.stop()
        self.disconnect()

    def cleanup(self):
        self.stop_conversation()
        self.audio_interface.cleanup()

    @classmethod
    def create_with_custom_audio(
        cls,
        websocket_url: str,
        input_sample_rate: int = 16000,
        output_sample_rate: int = 16000,
        input_channels: int = 1,
        output_channels: int = 1,
        chunk_size: int = 1024,
        silence_threshold: float = 0.01,
        silence_timeout: float = 2.0,
        send_interval: float = 0.5,
        input_device_index: Optional[int] = None,
        output_device_index: Optional[int] = None,
        connection_timeout: int = 10,
    ) -> "ConversationClient":
        audio_config = AudioConfig.create_custom(
            input_sample_rate=input_sample_rate,
            output_sample_rate=output_sample_rate,
            input_channels=input_channels,
            output_channels=output_channels,
            chunk_size=chunk_size,
            silence_threshold=silence_threshold,
            silence_timeout=silence_timeout,
            send_interval=send_interval,
            input_device_index=input_device_index,
            output_device_index=output_device_index,
        )
        
        return cls(
            websocket_url=websocket_url,
            audio_config=audio_config,
            connection_timeout=connection_timeout,
        )