import { AudioInterface } from './AudioInterface';
import { WebSocketManager } from './WebSocketManager';

export interface ConversationState {
  isConnected: boolean;
  isRecording: boolean;
  isPlaying: boolean;
  currentAmplitude: number;
  error: string | null;
}

export class ConversationManager {
  private websocketUrl: string;
  private audioInterface: AudioInterface;
  private webSocketManager: WebSocketManager;
  private isRunning = false;
  private stateChangeCallback?: (state: ConversationState) => void;
  
  private state: ConversationState = {
    isConnected: false,
    isRecording: false,
    isPlaying: false,
    currentAmplitude: 0,
    error: null,
  };

  constructor(
    websocketUrl: string, 
    stateChangeCallback?: (state: ConversationState) => void
  ) {
    this.websocketUrl = websocketUrl;
    this.stateChangeCallback = stateChangeCallback;

    // Create audio interface with callback to send audio data
    this.audioInterface = new AudioInterface(
      // @ts-ignore
      this.onAudioInput.bind(this),
      this.onAmplitudeChange.bind(this),
      this.onInterrupt.bind(this)
    );

    // Create websocket manager
    this.webSocketManager = new WebSocketManager(
      this.websocketUrl, 
      this.audioInterface
    );
  }

  private onAudioInput(audioData: ArrayBuffer): void {
    this.webSocketManager.sendAudioData(audioData);
  }

  private onAmplitudeChange(amplitude: number): void {
    this.updateState({ currentAmplitude: amplitude });
  }

  private onInterrupt(): void {
    console.log('Audio interrupt detected, sending interrupt signal');
    this.webSocketManager.sendInterrupt();
  }

  private updateState(updates: Partial<ConversationState>): void {
    this.state = { ...this.state, ...updates };
    if (this.stateChangeCallback) {
      this.stateChangeCallback(this.state);
    }
  }

  async startConversation(): Promise<void> {
    if (this.isRunning) {
      console.warn('Conversation already running');
      return;
    }

    try {
      this.updateState({ error: null });
      
      // Connect to WebSocket
      console.log('Connecting to WebSocket...');
      await this.webSocketManager.connect();
      this.updateState({ isConnected: true });
      
      // Start audio interface
      console.log('Starting audio interface...');
      await this.audioInterface.start();
      this.updateState({ isRecording: true });
      
      this.isRunning = true;
      console.log('Conversation started successfully');
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Error starting conversation:', error);
      this.updateState({ 
        error: `Failed to start conversation: ${errorMessage}`,
        isConnected: false,
        isRecording: false 
      });
      
      // Clean up on error
      this.stopConversation();
      throw error;
    }
  }

  stopConversation(): void {
    if (!this.isRunning) {
      console.warn('Conversation not running');
      return;
    }

    console.log('Stopping conversation...');
    this.isRunning = false;

    // Stop audio interface
    this.audioInterface.stop();
    
    // Disconnect WebSocket
    this.webSocketManager.disconnect();
    
    this.updateState({
      isConnected: false,
      isRecording: false,
      isPlaying: false,
      currentAmplitude: 0,
      error: null
    });
    
    console.log('Conversation stopped');
  }

  sendMessage(message: object): void {
    if (!this.isRunning || !this.webSocketManager.isConnected()) {
      console.warn('Cannot send message: conversation not active');
      return;
    }
    
    this.webSocketManager.sendMessage(message);
  }


  cleanup(): void {
    this.stopConversation();
    this.audioInterface.cleanup();
  }

  getState(): ConversationState {
    return { ...this.state };
  }

  isActive(): boolean {
    return this.isRunning;
  }

  isConnected(): boolean {
    return this.webSocketManager.isConnected();
  }

  // Utility method to update WebSocket URL
  updateWebSocketUrl(newUrl: string): void {
    if (this.isRunning) {
      throw new Error('Cannot update WebSocket URL while conversation is active');
    }
    
    this.websocketUrl = newUrl;
    this.webSocketManager = new WebSocketManager(newUrl, this.audioInterface);
  }
}