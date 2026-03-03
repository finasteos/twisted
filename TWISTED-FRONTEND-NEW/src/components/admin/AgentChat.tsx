import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Bot, User, Loader2, Sparkles, Shield, Flame, Activity, GripVertical, X, Minimize2, Maximize2 } from 'lucide-react';
import { agentChat } from '../../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AgentChatProps {
  isOpen: boolean;
  onClose: () => void;
  initialAgent?: string;
}

type Agent = 'orchestrator' | 'sunny' | 'devils_advocate' | 'architect' | 'omega';

const AGENTS: Record<Agent, { name: string; color: string; bgGradient: string; icon: React.ReactNode; greeting: string }> = {
  orchestrator: {
    name: 'The Orchestrator',
    color: '#7B68EE',
    bgGradient: 'linear-gradient(135deg, rgba(123, 104, 238, 0.15) 0%, rgba(75, 0, 130, 0.15) 100%)',
    icon: <Shield size={16} />,
    greeting: "I'm The Orchestrator - I coordinate the TWISTED agent swarm. How can I help you today?"
  },
  sunny: {
    name: 'Sunny',
    color: '#FFD700',
    bgGradient: 'linear-gradient(135deg, rgba(255, 215, 0, 0.15) 0%, rgba(144, 238, 144, 0.15) 100%)',
    icon: <Sparkles size={16} />,
    greeting: "Hey there! I'm Sunny - always looking on the bright side! What's on your mind?"
  },
  devils_advocate: {
    name: "Devil's Advocate",
    color: '#DC143C',
    bgGradient: 'linear-gradient(135deg, rgba(220, 20, 60, 0.15) 0%, rgba(139, 0, 0, 0.15) 100%)',
    icon: <Flame size={16} />,
    greeting: "I'm the Devil's Advocate. I question everything. What supposedly brilliant idea do you want me to pick apart?"
  },
  architect: {
    name: 'The Architect',
    color: '#00ff88',
    bgGradient: 'linear-gradient(135deg, rgba(0, 255, 136, 0.15) 0%, rgba(0, 100, 50, 0.15) 100%)',
    icon: <Bot size={16} />,
    greeting: "I am The Architect - your system observer. I can analyze your agent swarm and suggest improvements."
  },
  omega: {
    name: 'Omega',
    color: '#00D4FF',
    bgGradient: 'linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 50, 100, 0.15) 100%)',
    icon: <Activity size={16} />,
    greeting: "I'm Omega. The Caretaker. I watch the watchers. I've seen every error. Want me to check the system? 😉"
  }
};

export const AgentChat: React.FC<AgentChatProps> = ({ isOpen, onClose, initialAgent = 'orchestrator' }) => {
  const [activeAgent, setActiveAgent] = useState<Agent>(initialAgent as Agent);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  
  // Position and size state
  const [position, setPosition] = useState({ x: 20, y: 20 });
  const [size, setSize] = useState({ width: 380, height: 520 });
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const dragOffset = useRef({ x: 0, y: 0 });
  const resizeStart = useRef({ x: 0, y: 0, width: 0, height: 0 });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const [sessionId] = useState(`session_${Date.now()}`);

  const agent = AGENTS[activeAgent];

  // Drag handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.resize-handle') || (e.target as HTMLElement).closest('button') || (e.target as HTMLElement).closest('input')) return;
    setIsDragging(true);
    dragOffset.current = { x: e.clientX - position.x, y: e.clientY - position.y };
  }, [position]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      setPosition({ x: e.clientX - dragOffset.current.x, y: e.clientY - dragOffset.current.y });
    }
    if (isResizing) {
      const newWidth = Math.max(300, Math.min(600, resizeStart.current.width + (e.clientX - resizeStart.current.x)));
      const newHeight = Math.max(300, Math.min(800, resizeStart.current.height + (e.clientY - resizeStart.current.y)));
      setSize({ width: newWidth, height: newHeight });
    }
  }, [isDragging, isResizing]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setIsResizing(false);
  }, []);

  useEffect(() => {
    if (isDragging || isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, isResizing, handleMouseMove, handleMouseUp]);

  // Resize handler
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsResizing(true);
    resizeStart.current = { x: e.clientX, y: e.clientY, width: size.width, height: size.height };
  }, [size]);

  useEffect(() => {
    if (isOpen) {
      setMessages([{
        id: '1',
        role: 'assistant',
        content: agent.greeting,
        timestamp: new Date()
      }]);
    }
  }, [isOpen, activeAgent]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const apiAgent = activeAgent === 'architect' ? 'architect' : activeAgent;
      const response = await agentChat(apiAgent, input.trim(), sessionId);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      ref={chatRef}
      className="fixed flex flex-col rounded-xl overflow-visible"
      style={{
        left: position.x,
        top: position.y,
        width: size.width,
        height: isMinimized ? 'auto' : size.height,
        zIndex: 99999,
        background: 'rgba(10, 10, 15, 0.95)',
        backdropFilter: 'blur(20px)',
        border: `1px solid ${agent.color}40`,
        boxShadow: `0 20px 60px rgba(0, 0, 0, 0.5), 0 0 30px ${agent.color}20`,
      }}
    >
      {/* Drag Handle / Header */}
      <div
        onMouseDown={handleMouseDown}
        className="flex items-center gap-2 px-3 py-2 cursor-move rounded-t-xl"
        style={{
          background: agent.bgGradient,
          borderBottom: `1px solid ${agent.color}30`,
        }}
      >
        <GripVertical size={14} className="text-gray-500" />
        
        {/* Agent Tabs */}
        <div className="flex gap-0.5 flex-1 overflow-x-auto">
          {(Object.keys(AGENTS) as Agent[]).map((a) => (
            <button
              key={a}
              onClick={() => { setActiveAgent(a); setMessages([{ id: '1', role: 'assistant', content: AGENTS[a].greeting, timestamp: new Date() }]); }}
              className={`px-2 py-1 text-[10px] font-semibold uppercase tracking-wide rounded transition-all flex items-center gap-1 whitespace-nowrap ${
                activeAgent === a
                  ? 'text-black'
                  : 'text-gray-400 hover:text-white'
              }`}
              style={activeAgent === a ? { 
                backgroundColor: AGENTS[a].color,
              } : {}}
            >
              {AGENTS[a].icon}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1">
          <button 
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-white/10 rounded transition-colors"
            title={isMinimized ? "Expand" : "Minimize"}
          >
            {isMinimized ? <Maximize2 size={12} style={{ color: agent.color }} /> : <Minimize2 size={12} style={{ color: agent.color }} />}
          </button>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            <X size={14} className="text-gray-500 hover:text-white" />
          </button>
        </div>
      </div>

      {/* Chat Content */}
      {!isMinimized && (
        <>
          {/* Agent Info Bar */}
          <div 
            className="flex items-center justify-between px-4 py-2"
            style={{ borderBottom: `1px solid ${agent.color}20` }}
          >
            <div className="flex items-center gap-2">
              <span style={{ color: agent.color }}>{agent.icon}</span>
              <span className="text-sm font-medium text-white">{agent.name}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: agent.color }} />
              <span className="text-[10px] text-gray-500">Online</span>
            </div>
          </div>

          {/* Messages */}
          <div 
            className="flex-1 overflow-y-auto p-4 space-y-3"
            style={{ 
              height: size.height - 140,
              scrollbarWidth: 'thin',
              scrollbarColor: `${agent.color}40 #222`,
              overflowY: 'auto'
            }}
          >
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-[85%] rounded-lg p-3 text-sm ${
                    msg.role === 'user' 
                      ? 'bg-gradient-to-r from-[#333] to-[#2a2a2a] text-white border border-gray-600' 
                      : 'bg-gradient-to-r from-[#0a0a0a] to-[#111] text-gray-200 border'
                  }`}
                  style={msg.role === 'assistant' ? { borderColor: `${agent.color}30` } : {}}
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    {msg.role === 'user' ? (
                      <User size={11} className="text-gray-500" />
                    ) : (
                      <span style={{ color: agent.color }}>{agent.icon}</span>
                    )}
                    <span className="text-[9px] text-gray-500 uppercase tracking-wider">
                      {msg.role === 'user' ? 'You' : agent.name}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div 
                  className="bg-gradient-to-r from-[#0a0a0a] to-[#111] border p-3 rounded-lg flex items-center gap-2"
                  style={{ borderColor: `${agent.color}30` }}
                >
                  <Loader2 size={12} className="animate-spin" style={{ color: agent.color }} />
                  <span className="text-xs" style={{ color: agent.color }}>Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3" style={{ borderTop: `1px solid ${agent.color}20` }}>
            <div className="flex gap-2 items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Message ${agent.name.split(' ')[0]}...`}
                disabled={isLoading}
                className="flex-1 bg-[#111] border border-[#333] rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-opacity-50 transition-all"
                style={{ borderColor: `${agent.color}40` }}
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="p-2.5 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105"
                style={{ 
                  background: `linear-gradient(135deg, ${agent.color} 0%, ${agent.color}cc 100%)`, 
                  color: 'black',
                  boxShadow: `0 0 15px ${agent.color}40`
                }}
              >
                <Send size={16} />
              </button>
            </div>
          </div>

          {/* Resize Handle */}
          <div 
            className="resize-handle absolute bottom-0 right-0 w-4 h-4 cursor-se-resize"
            onMouseDown={handleResizeStart}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" className="absolute bottom-2 right-2 text-gray-600">
              <path d="M10 0L0 10M10 4L4 10M10 8L8 10" stroke="currentColor" strokeWidth="1.5" fill="none" />
            </svg>
          </div>
        </>
      )}
    </div>
  );
};

export default AgentChat;
