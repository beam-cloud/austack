#!/usr/bin/env python3
"""
Test client for the AuStack conversation system.

This script demonstrates how to use the ConversationClient to connect
to an AuStack server and participate in audio conversations.
"""

from austack.client import ConversationClient, AudioConfig


def main():
    """Main function to run the conversation client."""
    # WebSocket server URL (replace with your server)
    websocket_url = "ws://localhost:8000/ws/conversation"

    print("=== AuStack Conversation Client Test ===")
    print(f"Connecting to: {websocket_url}")

    # Create conversation client with default settings
    client = ConversationClient(websocket_url=websocket_url)

    # Alternatively, create with custom audio configuration:
    # client = ConversationClient.create_with_custom_audio(
    #     websocket_url=websocket_url,
    #     input_sample_rate=16000,
    #     output_sample_rate=16000,
    #     silence_threshold=0.01,
    #     silence_timeout=2.0,
    # )

    try:
        # Start the conversation (this will block until stopped)
        client.start_conversation()
        print("Conversation ended")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure cleanup
        client.cleanup()
        print("Client cleaned up successfully")


def demo_custom_audio_config():
    """Demonstrate creating a client with custom audio configuration."""
    websocket_url = "ws://localhost:8000/ws/conversation"

    # Create custom audio configuration
    audio_config = AudioConfig.create_custom(
        input_sample_rate=16000,
        output_sample_rate=22000,  # Higher quality output
        input_channels=1,
        output_channels=2,  # Stereo output
        chunk_size=2048,  # Larger chunks
        silence_threshold=0.005,  # More sensitive
        silence_timeout=1.5,  # Shorter timeout
        send_interval=0.3,  # More frequent sending
    )

    # Create client with custom config
    client = ConversationClient(
        websocket_url=websocket_url,
        audio_config=audio_config,
        connection_timeout=15,  # Longer connection timeout
    )

    print("=== Custom Audio Config Demo ===")
    print("Audio Configuration:")
    print(f"  Input: {audio_config.stream.input_sample_rate}Hz, {audio_config.stream.input_channels} channel(s)")
    print(f"  Output: {audio_config.stream.output_sample_rate}Hz, {audio_config.stream.output_channels} channel(s)")
    print(f"  Chunk size: {audio_config.stream.input_chunk_size}")
    print(f"  Silence threshold: {audio_config.stream.silence_threshold}")

    try:
        client.start_conversation()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.cleanup()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--custom":
        demo_custom_audio_config()
    else:
        main()
