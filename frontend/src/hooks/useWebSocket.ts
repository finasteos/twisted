import { useCallback, useEffect, useRef, useState } from 'react';
import type { AgentThought, EventLogEntry, ProgressUpdate } from '../types/websocket';

interface UseWebSocketOptions {
  onProgress: (update: ProgressUpdate) => void;
  onAgentThought: (thought: AgentThought) => void;
  onEventLog: (entry: EventLogEntry) => void;
  onComplete: (deliverables: unknown) => void;
  onError: (error: Error) => void;
}

/**
 * WebSocket hook for real-time Glass Engine communication.
 * Handles reconnection, heartbeat, and message routing.
 */

export function useWebSocket(options: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const heartbeatIntervalRef = useRef<NodeJS.Timeout>();

  const connect = useCallback((url: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('🔌 WebSocket connected');

      // Start heartbeat
      heartbeatIntervalRef.current = setInterval(() => {
        ws.send(JSON.stringify({ type: 'ping' }));
      }, 30000);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'connection_established':
          console.log('✅ Connection established:', message.case_id);
          break;

        case 'progress':
          options.onProgress({
            stage: message.stage,
            percent: message.percent,
            message: message.message,
            etaSeconds: message.eta_seconds
          });
          break;

        case 'agent_thought':
          options.onAgentThought({
            agentId: message.agent_id,
            state: message.state,
            query: message.query,
            evidence: message.evidence,
            conclusion: message.conclusion,
            confidence: message.confidence,
            timestamp: message.timestamp
          });
          break;

        case 'event_log':
          options.onEventLog({
            id: `${message.timestamp}-${Math.random()}`,
            timestamp: message.timestamp,
            level: message.level,
            agent: message.agent,
            message: message.message,
            metadata: message.metadata
          });
          break;

        case 'case_complete':
          options.onComplete(message.deliverables);
          break;

        case 'pong':
          // Heartbeat response
          break;

        case 'error':
          options.onError(new Error(message.message));
          break;
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      clearInterval(heartbeatIntervalRef.current);
      console.log('🔌 WebSocket disconnected');

      // Attempt reconnection
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('🔄 Attempting reconnection...');
        connect(url);
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      options.onError(new Error('Connection error'));
    };

    wsRef.current = ws;
  }, [options]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimeoutRef.current);
    clearInterval(heartbeatIntervalRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message queued');
      // Could implement message queue here
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    sendMessage,
    isConnected
  };
}
