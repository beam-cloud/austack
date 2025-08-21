# Austack Client SDK for Node.js/TypeScript

A TypeScript/JavaScript client SDK for Austack conversational AI, providing WebSocket-based audio communication with built-in audio processing and conversation management.

## Installation

```bash
npm install austack
```

## Features

- 🎙️ **Audio Input/Output**: Browser-compatible audio capture and playback
- 🔊 **Real-time Communication**: WebSocket-based bidirectional audio streaming
- 🎯 **Voice Activity Detection**: Intelligent speech detection and silence handling
- 🛠️ **TypeScript Support**: Full type definitions included
- 🔄 **Interrupt Handling**: Smart audio interruption for natural conversations
- 📦 **Dual Module Support**: Works with both CommonJS and ES modules

## Quick Start

```typescript
import { ConversationManager } from 'austack';

const conversation = new ConversationManager(
  'ws://localhost:8000/ws',
  (state) => {
    console.log('Conversation state:', state);
  }
);

// Start the conversation
await conversation.startConversation();

// Stop the conversation
conversation.stopConversation();

// Clean up resources
conversation.cleanup();
```

## API Reference

### ConversationManager

The main class for managing audio conversations.

```typescript
class ConversationManager {
  constructor(
    websocketUrl: string,
    stateChangeCallback?: (state: ConversationState) => void
  )

  async startConversation(): Promise<void>
  stopConversation(): void
  sendMessage(message: object): void
  cleanup(): void
  getState(): ConversationState
  isActive(): boolean
  isConnected(): boolean
}
```

### Basic Usage

```typescript
import { ConversationManager, ConversationState } from 'austack';

const conversation = new ConversationManager(
  'ws://localhost:8000/ws',
  (state: ConversationState) => {
    if (state.error) {
      console.error('Conversation error:', state.error);
    }
    
    if (state.isConnected) {
      console.log('Connected to server');
    }
    
    if (state.isRecording) {
      console.log('Recording audio...');
    }
    
    if (state.currentAmplitude > 0.1) {
      console.log('Voice detected');
    }
  }
);

try {
  await conversation.startConversation();
  console.log('Conversation started successfully');
} catch (error) {
  console.error('Failed to start conversation:', error);
}

## Audio Configuration

The SDK uses the following default audio settings:

- **Sample Rate**: 16kHz (input and output)
- **Channels**: Mono (1 channel)
- **Format**: 16-bit PCM
- **Chunk Size**: 1024 samples
- **Silence Threshold**: 0.01
- **Silence Timeout**: 2 seconds
- **Send Interval**: 0.5 seconds

These settings are optimized for speech recognition and conversation applications.

## Browser Compatibility

This SDK is designed for modern browsers with support for:

- WebSocket API
- Web Audio API
- MediaDevices API (getUserMedia)

## License

MIT