from dataclasses import dataclass
from typing import Optional
import pyaudio


@dataclass
class AudioStreamConfig:
    """Configuration for audio input/output streams."""
    
    # Input stream configuration
    input_chunk_size: int = 1024
    input_sample_rate: int = 16000
    input_channels: int = 1
    input_device_index: Optional[int] = None
    
    # Output stream configuration  
    output_sample_rate: int = 16000
    output_channels: int = 1
    output_device_index: Optional[int] = None
    
    # Audio format
    format: int = pyaudio.paInt16
    
    # Voice activity detection parameters
    silence_threshold: float = 0.01
    silence_timeout: float = 2.0
    send_interval: float = 0.5


@dataclass
class AudioConfig:
    """Main audio configuration container."""
    
    stream: AudioStreamConfig = None
    
    def __post_init__(self):
        if self.stream is None:
            self.stream = AudioStreamConfig()
    
    @classmethod
    def create_default(cls) -> "AudioConfig":
        """Create default audio configuration."""
        return cls(stream=AudioStreamConfig())
    
    @classmethod
    def create_custom(
        cls,
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
    ) -> "AudioConfig":
        """Create custom audio configuration with specified parameters."""
        stream_config = AudioStreamConfig(
            input_chunk_size=chunk_size,
            input_sample_rate=input_sample_rate,
            input_channels=input_channels,
            input_device_index=input_device_index,
            output_sample_rate=output_sample_rate,
            output_channels=output_channels,
            output_device_index=output_device_index,
            silence_threshold=silence_threshold,
            silence_timeout=silence_timeout,
            send_interval=send_interval,
        )
        return cls(stream=stream_config)