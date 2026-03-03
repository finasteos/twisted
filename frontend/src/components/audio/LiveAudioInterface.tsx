/**
 * TWISTED Live Audio Interface
 * Real-time voice interaction with the Glass Engine
 */

import { Activity, Mic, MicOff } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import './LiveAudioInterface.css';

interface LiveAudioProps {
  caseId: string;
  caseStatus: string;
  onVoiceQuery: (text: string) => void;
  isActive: boolean;
}

export function LiveAudioInterface({ caseId, caseStatus, onVoiceQuery, isActive }: LiveAudioProps) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);

  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  // Initialize audio visualization
  useEffect(() => {
    if (!isListening) return;

    let animationFrame: number;
    const updateLevel = () => {
      if (analyserRef.current) {
        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average);
      }
      animationFrame = requestAnimationFrame(updateLevel);
    };

    updateLevel();
    return () => cancelAnimationFrame(animationFrame);
  }, [isListening]);

  const startListening = useCallback(async () => {
    try {
      // Initialize Web Audio API
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      mediaStreamRef.current = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 24000
        }
      });

      const source = audioContextRef.current.createMediaStreamSource(mediaStreamRef.current);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      // Connect to backend audio gateway
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/ws/audio/${caseId}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsListening(true);
        setTranscript('Listening...');
        streamAudioToBackend();
      };

      wsRef.current.onmessage = async (event) => {
        if (typeof event.data === 'string') {
          const data = JSON.parse(event.data);

          if (data.type === 'transcript') {
            setTranscript(data.text);
            if (data.speaker === 'user' && data.is_final) {
              onVoiceQuery(data.text);
            }
          }

          if (data.type === 'turn_complete') {
            setIsSpeaking(false);
            setTranscript('Listening...');
          }
        } else {
          // Binary audio data
          setIsSpeaking(true);
          const audioBuffer = await event.data.arrayBuffer();
          playAudio(audioBuffer);
        }
      };

      wsRef.current.onerror = (err) => {
        console.error('WebSocket error:', err);
        setTranscript('Connection error');
        stopListening();
      };

    } catch (err) {
      console.error('Audio initialization failed:', err);
      setTranscript('Microphone access required');
    }
  }, [caseId, onVoiceQuery]);

  const streamAudioToBackend = () => {
    if (!audioContextRef.current || !wsRef.current || !mediaStreamRef.current) return;

    // Create ScriptProcessor for raw PCM access (Legacy but widely supported for simple streaming)
    const bufferSize = 4096;
    processorRef.current = audioContextRef.current.createScriptProcessor(bufferSize, 1, 1);

    processorRef.current.onaudioprocess = (e) => {
      if (!isListening || wsRef.current?.readyState !== WebSocket.OPEN) return;

      const inputData = e.inputBuffer.getChannelData(0);
      // Convert Float32 to Int16 PCM
      const pcmData = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 32767;
      }

      wsRef.current.send(pcmData.buffer);
    };

    const source = audioContextRef.current.createMediaStreamSource(mediaStreamRef.current);
    source.connect(processorRef.current);
    processorRef.current.connect(audioContextRef.current.destination);
  };

  const playAudio = async (arrayBuffer: ArrayBuffer) => {
    if (!audioContextRef.current) return;

    try {
      // Note: Gemini returns raw PCM, we need to wrap it or use a library
      // For simplicity here, assuming backend sends a format decodeAudioData handles
      // If it's pure PCM, we'd manually create a buffer
      const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.start();

      source.onended = () => {
        // Handle end if needed
      };
    } catch (e) {
      console.error('Playback error:', e);
    }
  };

  const stopListening = useCallback(() => {
    mediaStreamRef.current?.getTracks().forEach(track => track.stop());
    wsRef.current?.close();

    if (processorRef.current) {
        processorRef.current.disconnect();
        processorRef.current = null;
    }

    audioContextRef.current?.close();
    audioContextRef.current = null;

    setIsListening(false);
    setIsSpeaking(false);
    setTranscript('');
    setAudioLevel(0);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopListening();
  }, [stopListening]);

  // Draw audio visualization
  useEffect(() => {
    if (!canvasRef.current || !isListening) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d')!;
    const bars = 30;
    const barWidth = canvas.width / bars;

    let animationFrame: number;
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, '#00ff88');
      gradient.addColorStop(1, 'rgba(0, 255, 136, 0.1)');

      ctx.fillStyle = gradient;

      for (let i = 0; i < bars; i++) {
        const height = (audioLevel / 255) * canvas.height * (0.3 + Math.random() * 0.7);
        const x = i * barWidth;
        const y = canvas.height - height;

        ctx.beginPath();
        // Use a standard rect if roundRect isn't supported, though React usually shimmed
        if (ctx.roundRect) {
            ctx.roundRect(x + 2, y, barWidth - 4, height, 4);
        } else {
            ctx.rect(x + 2, y, barWidth - 4, height);
        }
        ctx.fill();
      }

      animationFrame = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animationFrame);
  }, [isListening, audioLevel]);

  return (
    <div className={`live-audio-interface glass-card ${isActive ? 'active' : ''}`}>
      <div className="audio-header">
        <Activity size={16} className={isListening ? 'pulsing' : ''} />
        <span>Voice Interface</span>
        {isSpeaking && <span className="speaking-badge">TWISTED Speaking</span>}
      </div>

      <canvas
        ref={canvasRef}
        width={240}
        height={60}
        className={`audio-visualizer ${isListening ? 'active' : ''}`}
      />

      <div className="transcript-display">
        {transcript && (
          <p className={`transcript-text ${isSpeaking ? 'assistant' : 'user'}`}>
            {transcript}
          </p>
        )}
      </div>

      <div className="audio-controls">
        <button
          onClick={isListening ? stopListening : startListening}
          className={`audio-button ${isListening ? 'active' : ''}`}
          disabled={!isActive}
        >
          {isListening ? <MicOff size={20} /> : <Mic size={20} />}
          {isListening ? 'Stop' : 'Speak'}
        </button>

        {isListening && (
          <div className="listening-indicator">
            <span className="pulse-dot" />
            Listening...
          </div>
        )}
      </div>

      <div className="voice-hints">
        {caseStatus === 'IDLE' && "Try: 'Help Sarah with her insurance claim'"}
        {caseStatus === 'ANALYZING' && "Ask: 'What are the agents finding?'"}
        {caseStatus === 'COMPLETE' && "Ask: 'Walk me through the strategy'"}
      </div>
    </div>
  );
}
