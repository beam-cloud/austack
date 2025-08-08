import queue
import threading
import time
from typing import Optional, Callable

import numpy as np
import pyaudio
import webrtcvad

from .config import AudioConfig, AudioStreamConfig


class AudioInterface:
    """Generalized audio interface for handling input/output streams with voice activity detection."""

    def __init__(
        self,
        input_callback: Callable[[bytes], None],
        audio_config: Optional[AudioConfig] = None,
    ):
        """
        Initialize the audio interface.

        Args:
            input_callback: Function to call when audio input is detected
            audio_config: Audio configuration settings. If None, uses defaults.
        """
        self.input_callback = input_callback
        self.config = audio_config or AudioConfig.create_default()
        self.stream_config = self.config.stream

        # Audio components
        self.audio = pyaudio.PyAudio()
        self.input_stream: Optional[pyaudio.Stream] = None
        self.output_stream: Optional[pyaudio.Stream] = None

        # Threading components
        self.input_queue: queue.Queue[bytes] = queue.Queue()
        self.output_queue: queue.Queue[bytes] = queue.Queue()
        self.is_running = False
        self.input_thread: Optional[threading.Thread] = None
        self.output_thread: Optional[threading.Thread] = None

        # Voice activity detection
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(1)

        # State tracking
        self.last_speech_time = None
        self.audio_buffer: list[bytes] = []
        self.last_send_time = time.time()
        self.was_sending_audio = False

    def calculate_rms(self, audio_data: bytes) -> float:
        """Calculate RMS (Root Mean Square) of audio data."""
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
            rms = np.sqrt(np.mean(audio_float**2))
            return rms
        except Exception:
            return 0.0

    def is_speech(self, frame: bytes, sample_rate: int) -> bool:
        """Check if frame contains speech using both RMS and WebRTC VAD."""
        # First check RMS - if too quiet, definitely not speech
        rms = self.calculate_rms(frame)
        if rms < self.stream_config.silence_threshold:
            return False

        # If loud enough, use WebRTC VAD for better detection
        try:
            # WebRTC VAD requires specific frame lengths
            frame_size = 480 * 2  # 30ms at 16kHz, 16-bit
            if len(frame) >= frame_size:
                chunk = frame[:frame_size]
                return self.vad.is_speech(chunk, sample_rate)
            else:
                # If frame too small, pad it
                padded_frame = frame + b"\x00" * (frame_size - len(frame))
                return self.vad.is_speech(padded_frame[:frame_size], sample_rate)
        except Exception:
            # Fallback to RMS-based detection
            return rms > self.stream_config.silence_threshold * 2

    def should_send_audio(self) -> bool:
        """Determine if audio should be sent based on recent speech activity."""
        if self.last_speech_time is None:
            return False

        time_since_speech = time.time() - self.last_speech_time
        return time_since_speech < self.stream_config.silence_timeout

    def _input_callback(self, in_data: bytes, *_, **__):
        """PyAudio input stream callback."""
        if not self.is_running:
            return (None, pyaudio.paContinue)

        current_time = time.time()

        # Check for speech
        if self.is_speech(in_data, self.stream_config.input_sample_rate):
            self.last_speech_time = current_time

        # Always buffer audio if we've heard speech recently
        if self.should_send_audio():
            self.audio_buffer.append(in_data)

        # Send batched audio periodically
        if current_time - self.last_send_time >= self.stream_config.send_interval and self.audio_buffer and self.should_send_audio():
            # Combine buffered audio and send
            combined_audio = b"".join(self.audio_buffer)
            self.input_queue.put_nowait(combined_audio)

            # Reset buffer and timer
            self.audio_buffer = []
            self.last_send_time = current_time

        # Track audio state
        current_should_send = self.should_send_audio()
        self.was_sending_audio = current_should_send

        return (None, pyaudio.paContinue)

    def _process_input_queue(self):
        """Process audio input queue in separate thread."""
        while self.is_running:
            try:
                audio_data = self.input_queue.get(timeout=0.1)

                # Send audio data via callback
                print(f"Sending {len(audio_data)} bytes of audio")
                self.input_callback(audio_data)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing input audio: {e}")
                continue

    def _process_output_queue(self):
        """Process audio output queue in separate thread."""
        while self.is_running:
            try:
                audio_data = self.output_queue.get(timeout=0.1)
                if self.output_stream:
                    self.output_stream.write(audio_data)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error playing audio: {e}")
                continue

    def start(self):
        """Start the audio interface streams and processing threads."""
        try:
            # Start input stream
            self.input_stream = self.audio.open(
                format=self.stream_config.format,
                channels=self.stream_config.input_channels,
                rate=self.stream_config.input_sample_rate,
                input=True,
                input_device_index=self.stream_config.input_device_index,
                frames_per_buffer=self.stream_config.input_chunk_size,
                stream_callback=self._input_callback,  # type: ignore
                start=True,
            )

            # Start output stream
            self.output_stream = self.audio.open(
                format=self.stream_config.format,
                channels=self.stream_config.output_channels,
                rate=self.stream_config.output_sample_rate,
                output=True,
                output_device_index=self.stream_config.output_device_index,
                start=True,
            )

            self.is_running = True

            # Start processing threads
            self.input_thread = threading.Thread(target=self._process_input_queue, daemon=True)
            self.output_thread = threading.Thread(target=self._process_output_queue, daemon=True)

            self.input_thread.start()
            self.output_thread.start()

        except Exception:
            raise

    def play(self, audio_data: bytes):
        """Queue audio data for playback."""
        if self.is_running:
            self.output_queue.put(audio_data)

    def stop(self):
        """Stop the audio interface and clean up resources."""
        self.is_running = False

        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None

        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.output_stream = None

        # Wait for threads to finish
        if self.input_thread:
            self.input_thread.join(timeout=1.0)
        if self.output_thread:
            self.output_thread.join(timeout=1.0)

    def cleanup(self):
        """Clean up all resources."""
        self.stop()
        self.audio.terminate()

    def update_config(self, audio_config: AudioConfig):
        """Update audio configuration. Note: requires restart to take effect."""
        self.config = audio_config
        self.stream_config = self.config.stream
