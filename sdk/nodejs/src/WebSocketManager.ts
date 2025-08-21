import { AudioInterface } from './AudioInterface';

export class WebSocketManager {
  private websocket: WebSocket | null = null;
  private websocketUrl: string;
  private audioInterface: AudioInterface | null = null;
  private isRunning = false;

  constructor(websocketUrl: string, audioInterface?: AudioInterface) {
    this.websocketUrl = websocketUrl;
    this.audioInterface = audioInterface || null;
  }

  connect(): Promise<void> {
    if (this.websocket) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        this.websocket = new WebSocket(this.websocketUrl);
        this.websocket.binaryType = 'arraybuffer';
        
        this.websocket.onopen = () => {
          console.log('WebSocket connection opened');
          this.isRunning = true;
          resolve();
        };

        this.websocket.onmessage = (event) => {
          this.handleWebSocketMessage(event);
        };

        this.websocket.onclose = (event) => {
          console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
          this.isRunning = false;
        };

        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isRunning = false;
          reject(error);
        };

      } catch (error) {
        console.error('Error creating WebSocket connection:', error);
        reject(error);
      }
    });
  }

  private handleWebSocketMessage(event: MessageEvent): void {
    try {
      // Check if this is binary audio data - play immediately
      if (event.data instanceof ArrayBuffer) {
        if (this.audioInterface) {
          this.audioInterface.play(event.data);
        }
      } else if (typeof event.data === 'string') {
        // Handle JSON messages
        try {
          const data = JSON.parse(event.data);
          
          // Handle different message types if needed
          switch (data.type) {
            case 'status':
              break;
            case 'error':
              break;
            default:
          }
        } catch (parseError) {
        }
      }
    } catch (error) {
    }
  }

  sendAudioData(audioData: ArrayBuffer): void {
    if (this.websocket && this.isRunning && this.websocket.readyState === WebSocket.OPEN) {
      try {
        this.websocket.send(audioData);
      } catch (error) {
        console.error('Error sending audio data:', error);
        // @ts-ignore
        if (this.websocket.readyState === WebSocket.CLOSED) { 
          this.isRunning = false;
        }
      }
    } else {
      console.warn('Cannot send audio: WebSocket not connected');
    }
  }


  sendMessage(message: object): void {
    if (this.websocket && this.isRunning && this.websocket.readyState === WebSocket.OPEN) {
      try {
        this.websocket.send(JSON.stringify(message));
      } catch (error) {
        console.error('Error sending message:', error);
        // @ts-ignore
        if (this.websocket.readyState === WebSocket.CLOSED) {
          this.isRunning = false;
        }
      }
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }

  sendInterrupt(): void {
    if (this.websocket && this.isRunning && this.websocket.readyState === WebSocket.OPEN) {
      try {
        this.websocket.send('interrupt');
        console.log('Sent interrupt signal to server');
      } catch (error) {
        console.error('Error sending interrupt:', error);
      }
    } else {
      console.warn('Cannot send interrupt: WebSocket not connected');
    }
  }

  disconnect(): void {
    this.isRunning = false;
    
    if (this.websocket) {
      try {
        if (this.websocket.readyState === WebSocket.OPEN) {
          this.websocket.close();
        }
      } catch (error) {
        console.error('Error closing WebSocket:', error);
      }
      this.websocket = null;
    }
    
    console.log('Disconnected from WebSocket');
  }

  isConnected(): boolean {
    return this.websocket !== null && 
           this.websocket.readyState === WebSocket.OPEN && 
           this.isRunning;
  }

  getReadyState(): number | null {
    return this.websocket ? this.websocket.readyState : null;
  }
}