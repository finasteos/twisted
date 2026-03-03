import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Mail, Phone } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  references?: string[];
}

interface AftermathChatProps {
  caseId: string;
  onSendMessage: (message: unknown) => void;
  context: any;
}

export function AftermathChat({ caseId, onSendMessage, context }: AftermathChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `I've analyzed your case and generated a strategic report. I'm here to help you implement it.

**What I can do:**
- Explain any part of the strategy
- Revise the pre-written emails
- Identify your next immediate action
- Research specific contacts or organizations
- Prepare you for conversations

What would you like to focus on first?`,
      timestamp: Date.now(),
      references: ['strategic_report']
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    onSendMessage({
      type: 'user_message',
      case_id: caseId,
      message: input
    });

    setTimeout(() => {
      const response = `I understand you're asking about "${input}". I have full context from your case analysis including ${context?.contacts?.length || 0} contacts and ${context?.emails?.length || 0} email templates.

Could you clarify what aspect you'd like to explore? I can:
- Explain specific recommendations
- Help prioritize your actions
- Research additional background
- Prepare talking points for conversations`;

      setMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response,
        timestamp: Date.now(),
        references: ['emails']
      }]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <div className="fixed bottom-8 right-8 w-96 glass-card flex flex-col shadow-2xl z-50 overflow-hidden" style={{ height: '500px' }}>
      <div className="flex items-center justify-between px-4 py-3 bg-[rgba(0,0,0,0.4)] border-b border-[rgba(255,255,255,0.1)]">
        <div className="flex items-center space-x-2">
          <Bot size={20} className="text-[var(--accent-phosphor)]" />
          <span className="font-semibold text-sm">Strategy Assistant</span>
        </div>
        <span className="text-xs text-[var(--text-muted)] font-mono">Case: {caseId.slice(0, 8)}...</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-[rgba(255,255,255,0.1)] ml-2' : 'bg-[rgba(0,255,136,0.1)] text-[var(--accent-phosphor)] mr-2'}`}>
                {msg.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
              </div>
              <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`px-4 py-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-[var(--accent-blue)] text-black rounded-tr-none' : 'bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-tl-none'}`}>
                  <div className="prose prose-sm prose-invert max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
                {msg.references && msg.references.length > 0 && (
                  <div className="flex space-x-1 mt-1">
                    {msg.references.map(ref => (
                      <span key={ref} className="flex items-center space-x-1 px-2 py-1 bg-[rgba(0,0,0,0.3)] rounded-full text-[10px] text-[var(--text-muted)] border border-[rgba(255,255,255,0.05)]">
                        {ref === 'emails' && <Mail size={10} />}
                        {ref === 'contacts' && <Phone size={10} />}
                        {ref === 'strategic_report' && <FileText size={10} />}
                        <span className="capitalize">{ref.replace('_', ' ')}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="flex flex-row">
              <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-[rgba(0,255,136,0.1)] text-[var(--accent-phosphor)] mr-2">
                <Bot size={16} />
              </div>
              <div className="px-4 py-3 rounded-2xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-tl-none flex items-center space-x-1">
                <span className="w-1.5 h-1.5 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={scrollRef} />
      </div>

      <div className="p-4 bg-[rgba(0,0,0,0.2)] border-t border-[rgba(255,255,255,0.1)]">
        <div className="flex items-center space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your strategy..."
            className="flex-1 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-full px-4 py-2 text-sm text-white focus:outline-none focus:border-[var(--accent-phosphor)] transition-colors"
          />
          <button 
            onClick={handleSend}
            disabled={!input.trim()}
            className="w-10 h-10 rounded-full bg-[var(--accent-phosphor)] text-black flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_0_15px_rgba(0,255,136,0.4)] transition-all"
          >
            <Send size={16} className="ml-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
