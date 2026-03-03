import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { adminChat } from '../../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AdminChatProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AdminChat: React.FC<AdminChatProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "I am The Architect - your system observer. I can analyze your agent swarm and suggest improvements. Ask me anything about how the system is performing or how it could be better. What would you like to know?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

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
      const response = await adminChat(input.trim());
      
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
    <div className="fixed bottom-4 right-4 w-96 h-[500px] bg-black border-2 border-[#00ff88] shadow-[8px_8px_0px_0px_#00ff88] flex flex-col z-[200]">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b-2 border-[#00ff88] bg-[#00ff88]/10">
        <div className="flex items-center gap-2">
          <Bot size={20} className="text-[#00ff88]" />
          <span className="font-bold text-sm uppercase text-[#00ff88]">The Architect</span>
        </div>
        <button 
          onClick={onClose}
          className="text-gray-500 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map(msg => (
          <div 
            key={msg.id} 
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`max-w-[85%] p-3 text-xs ${
                msg.role === 'user' 
                  ? 'bg-[#333] text-white border border-[#555]' 
                  : 'bg-[#0a0a0a] text-gray-200 border border-[#00ff88]/30'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                {msg.role === 'user' ? (
                  <User size={12} className="text-gray-400" />
                ) : (
                  <Bot size={12} className="text-[#00ff88]" />
                )}
                <span className="text-[10px] text-gray-500 uppercase">
                  {msg.role === 'user' ? 'You' : 'The Architect'}
                </span>
              </div>
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-[#0a0a0a] border border-[#00ff88]/30 p-3 flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-[#00ff88]" />
              <span className="text-xs text-[#00ff88]">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t-2 border-[#00ff88]">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask The Architect..."
            disabled={isLoading}
            className="flex-1 bg-[#111] border border-[#333] px-3 py-2 text-xs text-white placeholder-gray-500 focus:border-[#00ff88] focus:outline-none"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="bg-[#00ff88] text-black p-2 hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
