import { Handle, Position } from '@xyflow/react';
import React from 'react';

interface AgentTaskItem {
  name: string;
  status: 'pending' | 'running' | 'done' | 'error' | 'skipped';
  duration_ms?: number;
  detail?: string;
}

interface AgentNodeProps {
  data: {
    name: string;
    role: string;
    state: 'idle' | 'thinking' | 'active' | 'complete' | 'error';
    confidence: number;
    lastThought?: string;
    isActive: boolean;
    tasks?: AgentTaskItem[];
    overallTaskStatus?: string;
  };
}

function getTaskStatusIcon(status: string): string {
  switch (status) {
    case 'done': return '\u2713';
    case 'running': return '\u25B6';
    case 'error': return '\u2717';
    case 'skipped': return '\u2014';
    case 'pending':
    default: return '\u25CB';
  }
}

function getTaskStatusColor(status: string): string {
  switch (status) {
    case 'done': return 'text-green-400';
    case 'running': return 'text-blue-400 animate-pulse';
    case 'error': return 'text-red-400';
    case 'skipped': return 'text-zinc-500';
    case 'pending':
    default: return 'text-zinc-600';
  }
}

export const AgentNode: React.FC<AgentNodeProps> = ({ data }) => {
  const hasTasks = data.tasks && data.tasks.length > 0;

  return (
    <div className={`agent-node glass-card p-4 min-w-[200px] max-w-[280px] transition-all duration-500 ${data.isActive ? 'isActive ring-2 ring-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.3)]' : 'opacity-80'}`}>
      <Handle type="target" position={Position.Top} className="!bg-white/20 !border-white/10" />

      <div className="agent-node-header flex justify-between items-center mb-2">
        <span className="agent-name font-bold text-sm tracking-wider uppercase">{data.name}</span>
        <div className={`status-dot w-2 h-2 rounded-full ${data.state === 'active' || data.state === 'thinking' ? 'bg-green-400 animate-pulse' : 'bg-white/20'}`} />
      </div>

      <div className="agent-role text-[10px] text-white/40 uppercase mb-3 tracking-widest">{data.role}</div>

      <div className="confidence-meter w-full bg-white/5 h-1 rounded-full mb-2 overflow-hidden">
        <div
          className="confidence-level h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-1000"
          style={{ width: `${data.confidence * 100}%` }}
        />
      </div>

      {/* Verbose Task List */}
      {hasTasks && (
        <div className="task-list mt-2 space-y-1 max-h-[160px] overflow-y-auto border-t border-white/5 pt-2">
          {data.tasks!.map((task, idx) => (
            <div key={idx} className="flex items-start gap-1.5 text-[11px]">
              <span className={`font-mono flex-shrink-0 ${getTaskStatusColor(task.status)}`}>
                {getTaskStatusIcon(task.status)}
              </span>
              <div className="flex-1 min-w-0">
                <span className={`${task.status === 'done' ? 'text-white/40' : 'text-white/70'}`}>
                  {task.name}
                </span>
                {task.detail && (
                  <span className="text-white/30 ml-1 text-[9px]">({task.detail})</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Last Thought (only show if no tasks) */}
      {!hasTasks && data.lastThought && (
        <div className="agent-thought text-[11px] leading-relaxed text-white/70 mt-3 border-t border-white/5 pt-2 animate-fade-in line-clamp-3">
          &quot;{data.lastThought}&quot;
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-white/20 !border-white/10" />

      {data.state === 'thinking' && (
        <div className="scan-line absolute inset-0 rounded-xl overflow-hidden pointer-events-none" />
      )}
    </div>
  );
};
