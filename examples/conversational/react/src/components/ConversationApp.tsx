import React, { useState, useEffect, useRef } from "react";
import { ConversationManager, ConversationState } from "austack";
import { PulsingBubble } from "./PulsingBubble";

export const ConversationApp: React.FC = () => {
  const [websocketUrl, setWebsocketUrl] = useState(
    "wss://austack-example-conversational-86b8dbb-v2.app.beam.cloud"
  );
  const [conversationState, setConversationState] = useState<ConversationState>(
    {
      isConnected: false,
      isRecording: false,
      isPlaying: false,
      currentAmplitude: 0,
      error: null,
    }
  );

  const conversationManagerRef = useRef<ConversationManager>();
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize conversation manager
  useEffect(() => {
    if (!conversationManagerRef.current) {
      conversationManagerRef.current = new ConversationManager(
        websocketUrl,
        setConversationState
      );
      setIsInitialized(true);
    }

    // Cleanup on unmount
    return () => {
      if (conversationManagerRef.current) {
        conversationManagerRef.current.cleanup();
      }
    };
  }, [websocketUrl]);

  const handleStartConversation = async () => {
    if (!conversationManagerRef.current) return;

    try {
      await conversationManagerRef.current.startConversation();
    } catch (error) {
      console.error("Failed to start conversation:", error);
    }
  };

  const handleStopConversation = () => {
    if (conversationManagerRef.current) {
      conversationManagerRef.current.stopConversation();
    }
  };

  const handleUrlChange = (newUrl: string) => {
    if (
      conversationManagerRef.current &&
      !conversationManagerRef.current.isActive()
    ) {
      try {
        conversationManagerRef.current.updateWebSocketUrl(newUrl);
        setWebsocketUrl(newUrl);
      } catch (error) {
        console.error("Failed to update WebSocket URL:", error);
        setConversationState((prev) => ({
          ...prev,
          error: "Cannot update URL while conversation is active",
        }));
      }
    }
  };

  const getStatusText = () => {
    if (conversationState.error) return "Error";
    if (!conversationState.isConnected) return "Disconnected";
    if (conversationState.isRecording) return "Listening";
    return "Connected";
  };

  const getStatusColor = () => {
    if (conversationState.error) return "#ef4444";
    if (!conversationState.isConnected) return "#6b7280";
    if (conversationState.isRecording) return "#10b981";
    return "#3b82f6";
  };

  if (!isInitialized) {
    return <div>Initializing...</div>;
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "20px",
        backgroundColor: "#f8fafc",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "600px",
          width: "100%",
          backgroundColor: "white",
          borderRadius: "16px",
          padding: "32px",
          boxShadow: "0 10px 25px rgba(0, 0, 0, 0.1)",
        }}
      >
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <h1
            style={{
              fontSize: "28px",
              fontWeight: "bold",
              color: "#1f2937",
              marginBottom: "8px",
            }}
          >
            Conversational AI
          </h1>
          <p
            style={{
              color: "#6b7280",
              fontSize: "16px",
            }}
          >
            Real-time voice conversation with WebRTC audio processing
          </p>
        </div>

        {/* WebSocket URL Input */}
        <div style={{ marginBottom: "24px" }}>
          <label
            style={{
              display: "block",
              fontSize: "14px",
              fontWeight: "500",
              color: "#374151",
              marginBottom: "8px",
            }}
          >
            WebSocket URL
          </label>
          <input
            type="text"
            value={websocketUrl}
            onChange={(e) => handleUrlChange(e.target.value)}
            disabled={conversationState.isConnected}
            style={{
              width: "100%",
              padding: "12px",
              border: "1px solid #d1d5db",
              borderRadius: "8px",
              fontSize: "14px",
              backgroundColor: conversationState.isConnected
                ? "#f9fafb"
                : "white",
            }}
            placeholder="ws://localhost:8000/chat/conversation/start"
          />
        </div>

        {/* Status and Pulsing Bubble */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            marginBottom: "32px",
          }}
        >
          <div
            style={{
              marginBottom: "24px",
            }}
          >
            <PulsingBubble
              amplitude={conversationState.currentAmplitude}
              isActive={conversationState.isRecording}
              size={150}
              color={getStatusColor()}
            />
          </div>

          {/* Status Text */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              marginBottom: "16px",
            }}
          >
            <div
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: getStatusColor(),
              }}
            />
            <span
              style={{
                fontSize: "16px",
                fontWeight: "500",
                color: "#374151",
              }}
            >
              {getStatusText()}
            </span>
          </div>

          {/* Amplitude Display */}
          {conversationState.isRecording && (
            <div
              style={{
                fontSize: "12px",
                color: "#6b7280",
                textAlign: "center",
              }}
            >
              Audio Level:{" "}
              {(conversationState.currentAmplitude * 100).toFixed(1)}%
            </div>
          )}
        </div>

        {/* Controls */}
        <div
          style={{
            display: "flex",
            gap: "12px",
            justifyContent: "center",
            marginBottom: "24px",
          }}
        >
          {!conversationState.isConnected ? (
            <button
              onClick={handleStartConversation}
              style={{
                padding: "12px 24px",
                backgroundColor: "#10b981",
                color: "white",
                border: "none",
                borderRadius: "8px",
                fontSize: "16px",
                fontWeight: "500",
                cursor: "pointer",
                transition: "background-color 0.2s",
              }}
              onMouseOver={(e) =>
                (e.currentTarget.style.backgroundColor = "#059669")
              }
              onMouseOut={(e) =>
                (e.currentTarget.style.backgroundColor = "#10b981")
              }
            >
              Start Conversation
            </button>
          ) : (
            <button
              onClick={handleStopConversation}
              style={{
                padding: "12px 24px",
                backgroundColor: "#ef4444",
                color: "white",
                border: "none",
                borderRadius: "8px",
                fontSize: "16px",
                fontWeight: "500",
                cursor: "pointer",
                transition: "background-color 0.2s",
              }}
              onMouseOver={(e) =>
                (e.currentTarget.style.backgroundColor = "#dc2626")
              }
              onMouseOut={(e) =>
                (e.currentTarget.style.backgroundColor = "#ef4444")
              }
            >
              Stop Conversation
            </button>
          )}
        </div>

        {/* Error Display */}
        {conversationState.error && (
          <div
            style={{
              padding: "12px",
              backgroundColor: "#fee2e2",
              border: "1px solid #fecaca",
              borderRadius: "8px",
              color: "#dc2626",
              fontSize: "14px",
              textAlign: "center",
            }}
          >
            {conversationState.error}
          </div>
        )}

        {/* Instructions */}
        {!conversationState.isConnected && (
          <div
            style={{
              marginTop: "24px",
              padding: "16px",
              backgroundColor: "#f0f9ff",
              border: "1px solid #bae6fd",
              borderRadius: "8px",
              fontSize: "14px",
              color: "#0369a1",
            }}
          >
            <strong>Instructions:</strong>
            <ul style={{ margin: "8px 0", paddingLeft: "20px" }}>
              <li>Make sure your WebSocket server is running</li>
              <li>Click "Start Conversation" to begin</li>
              <li>The bubble will pulse based on your voice amplitude</li>
              <li>Audio uses WebRTC with echo cancellation</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
