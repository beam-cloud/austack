import React, { useEffect, useRef } from 'react';

interface PulsingBubbleProps {
  amplitude: number;
  isActive: boolean;
  size?: number;
  color?: string;
  minScale?: number;
  maxScale?: number;
}

export const PulsingBubble: React.FC<PulsingBubbleProps> = ({
  amplitude,
  isActive,
  size = 120,
  color = '#3b82f6',
  minScale = 0.8,
  maxScale = 1.4,
}) => {
  const bubbleRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();

  useEffect(() => {
    if (!bubbleRef.current) return;

    const animate = () => {
      if (bubbleRef.current && isActive) {
        // Calculate scale based on amplitude
        const normalizedAmplitude = Math.min(Math.max(amplitude, 0), 1);
        const scale = minScale + (normalizedAmplitude * (maxScale - minScale));
        
        // Apply transform with smooth transitions
        bubbleRef.current.style.transform = `scale(${scale})`;
        bubbleRef.current.style.opacity = isActive ? '1' : '0.5';
      }
      
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [amplitude, isActive, minScale, maxScale]);

  const bubbleStyle: React.CSSProperties = {
    width: size,
    height: size,
    borderRadius: '50%',
    backgroundColor: color,
    transition: 'transform 0.1s ease-out, opacity 0.3s ease',
    transformOrigin: 'center',
    position: 'relative',
    boxShadow: `0 0 20px ${color}40`,
  };

  const pulseRingStyle: React.CSSProperties = {
    position: 'absolute',
    width: '100%',
    height: '100%',
    borderRadius: '50%',
    border: `2px solid ${color}60`,
    animation: isActive ? 'pulse-ring 2s infinite' : 'none',
    top: 0,
    left: 0,
  };

  return (
    <div 
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
      }}
    >
      <style>
        {`
          @keyframes pulse-ring {
            0% {
              transform: scale(1);
              opacity: 0.8;
            }
            50% {
              transform: scale(1.2);
              opacity: 0.4;
            }
            100% {
              transform: scale(1.4);
              opacity: 0;
            }
          }
          
          @keyframes gentle-pulse {
            0%, 100% {
              transform: scale(1);
            }
            50% {
              transform: scale(1.05);
            }
          }
        `}
      </style>
      
      {/* Outer pulse ring */}
      {isActive && <div style={pulseRingStyle} />}
      
      {/* Main bubble */}
      <div
        ref={bubbleRef}
        style={{
          ...bubbleStyle,
          animation: !isActive ? 'gentle-pulse 3s infinite' : 'none',
        }}
      >
        {/* Inner highlight */}
        <div
          style={{
            position: 'absolute',
            top: '20%',
            left: '30%',
            width: '30%',
            height: '30%',
            borderRadius: '50%',
            backgroundColor: 'rgba(255, 255, 255, 0.3)',
            filter: 'blur(8px)',
          }}
        />
      </div>
      
      {/* Additional amplitude-based rings */}
      {isActive && amplitude > 0.3 && (
        <div
          style={{
            ...pulseRingStyle,
            animation: 'pulse-ring 1.5s infinite',
            animationDelay: '0.3s',
            borderColor: `${color}40`,
          }}
        />
      )}
      
      {isActive && amplitude > 0.6 && (
        <div
          style={{
            ...pulseRingStyle,
            animation: 'pulse-ring 1s infinite',
            animationDelay: '0.6s',
            borderColor: `${color}20`,
          }}
        />
      )}
    </div>
  );
};