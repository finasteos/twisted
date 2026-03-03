import {
    AlertTriangle,
    Brain,
    CheckCircle,
    Info,
    MessageSquare,
    Zap
} from 'lucide-react';
import { useEffect, useRef } from 'react';
import { CaseStatus } from '../../types/case';

interface LogEntry {
  id: string;
  timestamp: number;
  level: 'INFO' | 'THINK' | 'DEBATE' | 'SUCCESS' | 'WARNING' | 'ERROR';
  agent: string;
  message: string;
  metadata?: Record<string, unknown>;
}

interface EventLogProps {
  entries: LogEntry[];
  status: CaseStatus;
  progress: number;
  stage: string;
}

/**
 * The Event Log is NOT a debug console.
 * It is a core user-facing pillar of TWISTED.
 *
 * Users watch this to build trust in the engine's reasoning.
 * Every agent thought, every query, every debate round is visible.
 */

const levelConfig = {
  INFO: { icon: Info, color: '#00d4ff' },
  THINK: { icon: Brain, color: '#a855f7' },
  DEBATE: { icon: MessageSquare, color: '#f59e0b' },
  SUCCESS: { icon: CheckCircle, color: '#00ff88' },
  WARNING: { icon: AlertTriangle, color: '#f59e0b' },
  ERROR: { icon: AlertTriangle, color: '#ef4444' }
};

export function EventLog({ entries, status, progress, stage }: EventLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries]);

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="event-log-container glass-card">
      {/* Header with live progress */}
      <div className="log-header">
        <div className="log-status">
          <Zap size={16} className="status-icon" />
          <span className="status-text">{stage}</span>
        </div>
        <div className="log-progress">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="progress-text">{Math.round(progress)}%</span>
        </div>
      </div>

      {/* Scrolling log entries */}
      <div className="log-entries" ref={scrollRef}>
        {entries.length === 0 ? (
          <div className="log-empty">
            <p>Waiting for files...</p>
            <span className="empty-hint">
              Drop documents to activate the swarm
            </span>
          </div>
        ) : (
          entries.map((entry) => {
            const config = levelConfig[entry.level];
            const Icon = config.icon;

            return (
              <div
                key={entry.id}
                className={`log-entry ${entry.level.toLowerCase()}`}
              >
                <div className="entry-timestamp">
                  {formatTime(entry.timestamp)}
                </div>
                <div
                  className="entry-icon"
                  style={{ color: config.color }}
                >
                  <Icon size={14} />
                </div>
                <div className="entry-content">
                  <div className="entry-header">
                    <span
                      className="entry-agent"
                      style={{ color: config.color }}
                    >
                      {entry.agent}
                    </span>
                    <span className="entry-level">{entry.level}</span>
                  </div>
                  <p className="entry-message">{entry.message}</p>
                  {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                    <details className="entry-metadata">
                      <summary>Details</summary>
                      <pre>{JSON.stringify(entry.metadata, null, 2)}</pre>
                    </details>
                  )}
                </div>
              </div>
            );
          })
        )}

        {/* Live indicator */}
        {status !== CaseStatus.COMPLETE && status !== CaseStatus.IDLE && (
          <div className="log-live-indicator">
            <span className="live-dot" />
            <span>Live processing...</span>
          </div>
        )}
      </div>
    </div>
  );
}
