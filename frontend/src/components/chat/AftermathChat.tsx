import { Bot, FileText, Mail, Phone, Send, User } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  references?: string[]; // Case facts referenced
}

interface AftermathChatProps {
  caseId: string;
  onSendMessage: (message: unknown) => void;
  context: {
    strategic_report?: string;
    emails?: unknown[];
    contacts?: unknown[];
  };
}

/**
 * Aftermath Chat: Interactive guidance through strategy implementation.
 *
 * Features:
 * - Full case context awareness
 * - Reference to specific deliverables
 * - Revision requests for emails
 * - "What should I do next?" guidance
 */

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

  // Auto-scroll
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

    // Send to backend with context
    onSendMessage({
      type: 'user_message',
      case_id: caseId,
      message: input,
      context_references: detectReferences(input, context)
    });

    // Simulate response (in production, from WebSocket)
    setTimeout(() => {
      const response = generateContextualResponse(input, context);
      setMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response,
        timestamp: Date.now(),
        references: extractReferences(response)
      }]);
      setIsTyping(false);
    }, 1500);
  };

  const detectReferences = (input: string, ctx: typeof context): string[] => {
    const refs: string[] = [];
    const lower = input.toLowerCase();

    if (lower.includes('email') || lower.includes('write')) refs.push('emails');
    if (lower.includes('contact') || lower.includes('call')) refs.push('contacts');
    if (lower.includes('strategy') || lower.includes('plan')) refs.push('strategic_report');

    return refs;
  };

  const extractReferences = (response: string): string[] => {
    // Extract mentioned deliverables
    const refs: string[] = [];
    if (response.includes('email')) refs.push('emails');
    if (response.includes('contact')) refs.push('contacts');
    return refs;
  };

  const generateContextualResponse = (query: string, ctx: typeof context): string => {
    // In production, this comes from backend RAG
    const lower = query.toLowerCase();

    if (lower.includes('next') || lower.includes('what should i do')) {
      return `Based on your strategic report, your **immediate next action** is:

**Step 1**: ${ctx.emails && ctx.emails[0] ? 'Send the initial consultation email to the attorney identified in your contact list.' : 'Review the strategic report and identify your primary objective.'}

This creates momentum and establishes professional representation early. Would you like me to revise that email or help you prepare for the conversation?`;
    }

    if (lower.includes('email') || lower.includes('revise')) {
      return `I can revise any of the pre-written emails. Which one would you like to adjust?

1. **Legal consultation request** — Currently formal, professional tone
2. **Insurance dispute letter** — Currently firm, evidence-based
3. **Counterparty negotiation** — Currently assertive but open

Tell me what you'd like to change (tone, length, specific points to emphasize).`;
    }

    return `I understand you're asking about "${query}". I have full context from your case analysis including ${ctx.contacts?.length || 0} contacts and ${ctx.emails?.length || 0} email templates.

Could you clarify what aspect you'd like to explore? I can:
- Explain specific recommendations
- Help prioritize your actions
- Research additional background
- Prepare talking points for conversations`;
  };

  return (
    <div className="aftermath-chat glass-card">
      <div className="chat-header">
        <Bot size={20} className="header-icon" />
        <span className="header-title">Strategy Assistant</span>
        <span className="header-context">Case: {caseId.slice(0, 8)}...</span>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'assistant' ? <Bot size={18} /> : <User size={18} />}
            </div>
            <div className="message-content">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
              {msg.references && msg.references.length > 0 && (
                <div className="message-references">
                  {msg.references.map(ref => (
                    <span key={ref} className="reference-pill">
                      {ref === 'emails' && <Mail size={12} />}
                      {ref === 'contacts' && <Phone size={12} />}
                      {ref === 'strategic_report' && <FileText size={12} />}
                      {ref}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="message assistant typing">
            <div className="message-avatar"><Bot size={18} /></div>
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about your strategy, revise emails, or get next steps..."
          className="chat-input"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          className="send-button glass-button"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
