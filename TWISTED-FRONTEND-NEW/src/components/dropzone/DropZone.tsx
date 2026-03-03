import { useState, useCallback } from 'react';
import { Upload, Sparkles, Brain } from 'lucide-react';

interface DropZoneProps {
  onCreateCase: (query: string, enableDeepResearch: boolean) => void;
}

export function DropZone({ onCreateCase }: DropZoneProps) {
  const [query, setQuery] = useState('');
  const [enableDeepResearch, setEnableDeepResearch] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onCreateCase(query.trim(), enableDeepResearch);
    }
  }, [query, enableDeepResearch, onCreateCase]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto space-y-12">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold tracking-tighter">
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--accent-phosphor)] to-[var(--accent-blue)]">TWISTED</span>
        </h1>
        <p className="text-xl text-[var(--text-secondary)]">
          Liquid clarity for complex problems
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass-card w-full p-8 space-y-6">
        <div className="space-y-2">
          <label htmlFor="help-query" className="block text-sm font-medium text-[var(--text-secondary)]">
            Who should I help?
          </label>
          <input
            id="help-query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'Help Sarah with her insurance claim denial'"
            className="w-full bg-[rgba(0,0,0,0.2)] border border-[rgba(255,255,255,0.1)] rounded-lg px-4 py-3 text-white placeholder-[rgba(255,255,255,0.3)] focus:outline-none focus:border-[var(--accent-phosphor)] transition-colors"
            autoFocus
          />
          <span className="block text-xs text-[var(--text-muted)] mt-1">
            Describe the person and their situation
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <label className="flex items-center cursor-pointer relative">
            <input
              type="checkbox"
              className="sr-only"
              checked={enableDeepResearch}
              onChange={(e) => setEnableDeepResearch(e.target.checked)}
            />
            <div className={`w-10 h-6 rounded-full transition-colors ${enableDeepResearch ? 'bg-[var(--accent-phosphor)]' : 'bg-[rgba(255,255,255,0.1)]'}`}>
              <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${enableDeepResearch ? 'translate-x-4' : ''}`} />
            </div>
            <div className="ml-3 flex flex-col">
              <span className="flex items-center text-sm font-medium text-white">
                <Brain size={16} className="mr-2 text-[var(--accent-phosphor)]" />
                Deep Research
              </span>
              <span className="text-xs text-[var(--text-muted)]">
                Exhaustive background intelligence (5-15 min)
              </span>
            </div>
          </label>
        </div>

        <button 
          type="submit" 
          className="glass-button primary w-full flex items-center justify-center space-x-2 py-3"
          disabled={!query.trim()}
        >
          <Sparkles size={18} />
          <span>Initialize Glass Engine</span>
        </button>
      </form>

      <div 
        className={`glass-card w-full border-dashed border-2 p-12 flex flex-col items-center justify-center text-center transition-all ${isDragging ? 'border-[var(--accent-phosphor)] bg-[rgba(0,255,136,0.05)]' : 'border-[rgba(255,255,255,0.1)]'}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDragLeave}
      >
        <Upload size={48} className="text-[var(--text-muted)] mb-4" />
        <p className="text-lg font-medium text-[var(--text-secondary)] mb-2">
          Drop files here after initialization
        </p>
        <span className="text-sm text-[var(--text-muted)]">
          PDF, DOCX, TXT, Images, Video, Audio
        </span>
      </div>

      <div className="flex space-x-8 text-sm text-[var(--text-muted)]">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-[var(--accent-phosphor)]" />
          <span>Local processing</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-[var(--accent-blue)]" />
          <span>Encrypted at rest</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-[var(--accent-purple)]" />
          <span>Transparent reasoning</span>
        </div>
      </div>
    </div>
  );
}
