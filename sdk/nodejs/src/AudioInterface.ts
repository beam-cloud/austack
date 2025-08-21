export class AudioInterface {
  private inputAudioContext: AudioContext | null = null;
  private outputAudioContext: AudioContext | null = null;
  private inputStream: MediaStream | null = null;
  // These were unused; remove to satisfy TypeScript
  private isRunning = false;
  private inputCallback: (audioData: ArrayBuffer | ArrayBufferView) => void;
  
  // Simplified output playback queue/state (sequential chunk playback)
  private outputQueue: Uint8Array[] = [];
  private isOutputPlaying = false;
  private currentOutputSource: AudioBufferSourceNode | null = null;
  
  // Configuration matching Python client
  private readonly inputSampleRate = 16000;
  private readonly outputSampleRate = 16000;
  private readonly inputChannels = 1;
  // removed unused outputChannels
  private readonly chunkSize = 1024;
  private readonly silenceThreshold = 0.01;
  private readonly silenceTimeout = 2000; // 2 seconds in ms
  private readonly sendInterval = 500; // 0.5 seconds in ms
  
  // Interrupt detection configuration
  private readonly interruptThreshold = 0.05; // Higher threshold for interrupt detection
  private isAudioPlaying = false;
  
  // State tracking
  private lastSpeechTime: number | null = null;
  private audioBufferParts: Uint8Array[] = [];
  private lastSendTime = Date.now();
  private amplitudeCallback?: (amplitude: number) => void;

  constructor(
    inputCallback: (audioData: ArrayBuffer | ArrayBufferView) => void,
    amplitudeCallback?: (amplitude: number) => void,
    private onInterrupt?: () => void
  ) {
    this.inputCallback = inputCallback;
    this.amplitudeCallback = amplitudeCallback;
  }

  private calculateRMS(audioData: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < audioData.length; i++) {
      sum += audioData[i] * audioData[i];
    }

    const rms = Math.sqrt(sum / audioData.length);
    if (rms < 0.02) {
      return 0;
    }

    return rms;
  }

  private isSpeech(audioData: Float32Array): boolean {
    const rms = this.calculateRMS(audioData);
    return rms > this.silenceThreshold;
  }

  private shouldSendAudio(): boolean {
    if (this.lastSpeechTime === null) {
      return false;
    }
    const timeSinceSpeech = Date.now() - this.lastSpeechTime;
    return timeSinceSpeech < this.silenceTimeout;
  }

  private float32ArrayToInt16Array(float32Array: Float32Array): Int16Array {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      // Clamp and convert to 16-bit signed integer
      const val = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = val * 32767;
    }
    return int16Array;
  }

  private processAudioData = (audioData: Float32Array) => {
    const currentTime = Date.now();
    
    // Calculate amplitude for pulsing effect
    const rms = this.calculateRMS(audioData);
    if (this.amplitudeCallback) {
      this.amplitudeCallback(rms);
    }

    // Check for speech
    const isSpeaking = this.isSpeech(audioData);
    if (isSpeaking) {
      this.lastSpeechTime = currentTime;
      
      // Check if we should interrupt due to speaking during playback
      if (this.isAudioPlaying && rms > this.interruptThreshold && this.onInterrupt) {
        console.log('User speaking during playback, sending interrupt');
        this.onInterrupt();
        this.isAudioPlaying = false; // Stop interrupt detection until next playback
      }
    }

    // Buffer audio if we should send it
    if (this.shouldSendAudio()) {
      const int16Data = this.float32ArrayToInt16Array(audioData);
      this.audioBufferParts.push(new Uint8Array(int16Data.buffer));
    }

    // Send batched audio periodically
    if (
      currentTime - this.lastSendTime >= this.sendInterval &&
      this.audioBufferParts.length > 0 &&
      this.shouldSendAudio()
    ) {
      // Combine buffered audio
      const totalLength = this.audioBufferParts.reduce((sum, part) => sum + part.byteLength, 0);
      const combinedArray = new Uint8Array(totalLength);
      let offset = 0;
      
      for (const part of this.audioBufferParts) {
        combinedArray.set(part, offset);
        offset += part.byteLength;
      }

      console.log(`Sending ${combinedArray.byteLength} bytes of audio`);
      this.inputCallback(combinedArray);

      // Reset buffer and timer
      this.audioBufferParts = [];
      this.lastSendTime = currentTime;
    }
  };

  async start(): Promise<void> {
    try {
      // Request microphone access with WebRTC constraints including echo cancellation
      this.inputStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.inputSampleRate,
          channelCount: this.inputChannels,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Create audio context
      this.inputAudioContext = new AudioContext({
        sampleRate: this.inputSampleRate,
      });

      this.outputAudioContext = new AudioContext({
        sampleRate: this.outputSampleRate,
      });

      // Create media stream source
      const source = this.inputAudioContext.createMediaStreamSource(this.inputStream);

      // Create script processor for audio analysis
      const scriptProcessor = this.inputAudioContext.createScriptProcessor(this.chunkSize, 1, 1);
      
      scriptProcessor.onaudioprocess = (event) => {
        if (!this.isRunning) return;
        
        const inputBuffer = event.inputBuffer;
        const audioData = inputBuffer.getChannelData(0);
        this.processAudioData(audioData);
      };

      // Connect audio graph
      source.connect(scriptProcessor);
      scriptProcessor.connect(this.inputAudioContext.destination);

      this.isRunning = true;
      console.log('Audio interface started');

    } catch (error) {
      console.error('Error starting audio interface:', error);
      throw error;
    }
  }

  play(audioData: ArrayBuffer): void {
    if (!this.outputAudioContext) {
      console.warn('Audio interface not initialized for playback');
      return;
    }

    // Mark that audio is now playing for interrupt detection
    this.isAudioPlaying = true;

    // Queue raw PCM chunk; playback will convert to AudioBuffer per chunk
    this.outputQueue.push(new Uint8Array(audioData));

    if (!this.isOutputPlaying) {
      this.playNextOutputChunk();
    }
  }

  setAudioPlaybackState(isPlaying: boolean): void {
    this.isAudioPlaying = isPlaying;
  }

  isAudioPlaybackActive(): boolean {
    return this.isAudioPlaying;
  }

  interruptPlayback(): void {
    // Clear any queued audio and reset playback state without stopping input capture
    this.outputQueue = [];
    this.isOutputPlaying = false;
    this.isAudioPlaying = false;
    if (this.currentOutputSource) {
      try { this.currentOutputSource.stop(); } catch {}
      this.currentOutputSource.disconnect();
      this.currentOutputSource = null;
    }
    console.log('Audio playback interrupted');
  }

  private convertPCMToFloat32(pcmData: Uint8Array): Float32Array {
    // Create a new ArrayBuffer copy to avoid SharedArrayBuffer issues
    const buffer = new ArrayBuffer(pcmData.byteLength);
    new Uint8Array(buffer).set(pcmData);
    
    // Convert to Int16Array (linear16 format)
    const int16Data = new Int16Array(buffer);
    const float32Data = new Float32Array(int16Data.length);
    
    // Convert from int16 to float32 [-1, 1]
    for (let i = 0; i < int16Data.length; i++) {
      float32Data[i] = int16Data[i] / 32768.0;
    }
    
    return float32Data;
  }

  private playNextOutputChunk = (): void => {
    if (!this.outputAudioContext) {
      this.isOutputPlaying = false;
      return;
    }

    if (this.outputQueue.length === 0) {
      this.isOutputPlaying = false;
      // Playback completed
      this.isAudioPlaying = false;
      this.currentOutputSource = null;
      return;
    }

    this.isOutputPlaying = true;
    const nextChunk = this.outputQueue.shift()!;

    // Convert linear16 PCM to Float32 and play via AudioBufferSourceNode
    const float32 = this.convertPCMToFloat32(nextChunk);
    const audioBuffer = this.outputAudioContext.createBuffer(1, float32.length, this.outputSampleRate);
    audioBuffer.copyToChannel(float32 as any, 0);

    const source = this.outputAudioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.outputAudioContext.destination);
    source.onended = this.playNextOutputChunk;
    this.currentOutputSource = source;
    try {
      source.start();
    } catch (error) {
      console.error('Error starting audio playback', error);
      this.isOutputPlaying = false;
      this.currentOutputSource = null;
    }
  };


  stop(): void {
    this.isRunning = false;
    this.outputQueue = [];
    this.isOutputPlaying = false;
    if (this.currentOutputSource) {
      try { this.currentOutputSource.stop(); } catch {}
      this.currentOutputSource.disconnect();
      this.currentOutputSource = null;
    }

    if (this.inputStream) {
      this.inputStream.getTracks().forEach(track => track.stop());
      this.inputStream = null;
    }

    if (this.inputAudioContext) {
      this.inputAudioContext.close();
      this.inputAudioContext = null;
    }

    if (this.outputAudioContext) {
      this.outputAudioContext.close();
      this.outputAudioContext = null;
    }

    console.log('Audio interface stopped');
  }

  cleanup(): void {
    this.stop();
  }
}