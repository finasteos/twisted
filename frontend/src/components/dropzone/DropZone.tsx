import { Brain, Sparkles, Upload } from 'lucide-react';
import { useCallback, useState } from 'react';
import { HoverBorderGradient } from '../ui/hover-border-gradient';

interface DropZoneProps {
  onCreateCase: (query: string, enableDeepResearch: boolean) => void;
}

/**
 * The TWISTED Entry Point
 *
 * Two inputs:
 * 1. "Who should I help?" — The core question
 * 2. Deep Research toggle — Optional exhaustive background
 *
 * Everything else is drag-and-drop after case creation.
 */

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
    <div className="dropzone-container">
      <div className="dropzone-hero">
        <h1 className="hero-title">
          <span className="title-gradient">TWISTED</span>
        </h1>
        <p className="hero-subtitle">
          Liquid clarity for complex problems
        </p>
      </div>

      <form onSubmit={handleSubmit} className="case-form glass-card">
        <div className="input-group">
          <label htmlFor="help-query" className="input-label">
            Who should I help?
          </label>
          <input
            id="help-query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'Help Sarah with her insurance claim denial'"
            className="query-input"
            autoFocus
          />
          <span className="input-hint">
            Describe the person and their situation
          </span>
        </div>

        <div className="options-row">
          <label className="toggle-option">
            <input
              type="checkbox"
              checked={enableDeepResearch}
              onChange={(e) => setEnableDeepResearch(e.target.checked)}
            />
            <span className="toggle-slider" />
            <span className="toggle-label">
              <Brain size={16} />
              Deep Research
              <span className="toggle-description">
                Exhaustive background intelligence (5-15 min)
              </span>
            </span>
          </label>
        </div>

        <div className="flex justify-center w-full mt-4">
          <HoverBorderGradient
            containerClassName="rounded-full"
            as="button"
            className="dark:bg-black bg-white text-black dark:text-white flex items-center space-x-2 py-3 px-8 text-lg font-semibold"
            disabled={!query.trim()}
          >
            <Sparkles size={18} />
            <span>Initialize Glass Engine</span>
          </HoverBorderGradient>
        </div>
      </form>

      <div
        className={`drop-area glass-card ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDragLeave}
      >
        <Upload size={48} className="drop-icon" />
        <p className="drop-text">
          Drop files here after initialization
        </p>
        <span className="drop-formats">
          PDF, DOCX, TXT, Images, Video, Audio
        </span>
      </div>

      <div className="trust-indicators">
        <div className="trust-item">
          <div className="trust-dot" />
          <span>Local processing</span>
        </div>
        <div className="trust-item">
          <div className="trust-dot" />
          <span>Encrypted at rest</span>
        </div>
        <div className="trust-item">
          <div className="trust-dot" />
          <span>Transparent reasoning</span>
        </div>
      </div>
    </div>
  );
}
