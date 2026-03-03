import { Bot, ChevronDown, ChevronRight, Plus, Save, Settings, X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { createAgent, getSettings, listAgents, updateAgent, updateSettings, type AgentProfile, type Settings as SettingsType } from '../api';

interface SettingsPanelProps {
  onClose: () => void;
}

type SettingsTab = 'general' | 'agents';

export function SettingsPanel({ onClose }: SettingsPanelProps) {
  const [tab, setTab] = useState<SettingsTab>('general');
  const [settings, setSettings] = useState<SettingsType>({});
  const [agents, setAgents] = useState<AgentProfile[]>([]);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [editingFile, setEditingFile] = useState<{ agentId: string; file: string; content: string } | null>(null);
  const [newAgentId, setNewAgentId] = useState('');
  const [showNewAgent, setShowNewAgent] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getSettings().then(setSettings).catch(() => {});
    listAgents().then(setAgents).catch(() => {});
  }, []);

  const handleChange = (key: string, value: string | number | string[]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleCheckboxToggle = (key: 'help_package', item: string) => {
    setSettings((prev) => {
      const current = prev[key] || [];
      if (current.includes(item)) {
        return { ...prev, [key]: current.filter((i: string) => i !== item) };
      }
      return { ...prev, [key]: [...current, item] };
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSettings(settings);
    } catch { /* silent */ }
    setSaving(false);
    onClose();
  };

  const handleSaveAgent = useCallback(async () => {
    if (!editingFile) return;
    setSaving(true);
    try {
      const result = await updateAgent(editingFile.agentId, { [editingFile.file]: editingFile.content });

      if (result.error) {
        alert(`Safety Check Failed:\n\n${result.error}`);
        setSaving(false);
        return; // Don't close the editor
      }

      // Refresh agent list
      const updated = await listAgents();
      setAgents(updated);
      setEditingFile(null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      alert(`Network error saving agent: ${msg}`);
    }
    setSaving(false);
  }, [editingFile]);

  const handleCreateAgent = useCallback(async () => {
    if (!newAgentId.trim()) return;
    setSaving(true);
    try {
      await createAgent(newAgentId.trim().toLowerCase().replace(/\s+/g, '_'), {
        identity: `# ${newAgentId.trim()}\n\n**Codename:** New Agent\n\n## Core Identity\n\nDescribe this agent's purpose and role.\n`,
        skills: `# ${newAgentId.trim()} - Skills\n\n## Technical Capabilities\n\n- [ ] Add skills here\n`,
        soul: `# ${newAgentId.trim()} - Soul\n\n## Philosophical Core\n\n> Add the agent's core philosophy here.\n`,
      });
      const updated = await listAgents();
      setAgents(updated);
      setNewAgentId('');
      setShowNewAgent(false);
    } catch { /* silent */ }
    setSaving(false);
  }, [newAgentId]);

  return (
    <div className="settings-overlay" onClick={(e) => {
      if (e.target === e.currentTarget) onClose();
    }}>
      <div className="settings-panel" style={{ maxWidth: 700, maxHeight: '90vh' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>
            <Settings size={20} /> Configuration
          </h2>
          <button className="settings-btn" onClick={onClose} style={{ border: 'none' }}>
            <X size={18} />
          </button>
        </div>

        {/* Tab bar */}
        <div className="settings-tabs">
          <button
            className={`settings-tab ${tab === 'general' ? 'active' : ''}`}
            onClick={() => setTab('general')}
          >
            ⚙️ General
          </button>
          <button
            className={`settings-tab ${tab === 'agents' ? 'active' : ''}`}
            onClick={() => setTab('agents')}
          >
            🤖 Agents
          </button>
        </div>

        {/* ── General Tab ── */}
        {tab === 'general' && (
          <>
            <div className="settings-section">
              <h3>LLM Providers</h3>
              <div className="settings-field">
                <label>Default Provider</label>
                <select
                  value={settings.default_provider || 'auto'}
                  onChange={(e) => handleChange('default_provider', e.target.value)}
                >
                  <option value="auto">Auto-detect (LMStudio → Gemini → OpenAI)</option>
                  <option value="lmstudio">LMStudio (Local)</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic Claude</option>
                </select>
              </div>
              <div className="settings-field">
                <label>LMStudio URL</label>
                <input type="text" placeholder="http://localhost:1234" value={settings.lmstudio_url || ''} onChange={(e) => handleChange('lmstudio_url', e.target.value)} />
              </div>
              <div className="settings-field">
                <label>Gemini API Key</label>
                <input type="password" placeholder="Enter Gemini API key" value={settings.gemini_api_key || ''} onChange={(e) => handleChange('gemini_api_key', e.target.value)} />
              </div>
              <div className="settings-field">
                <label>OpenAI API Key</label>
                <input type="password" placeholder="Enter OpenAI API key" value={settings.openai_api_key || ''} onChange={(e) => handleChange('openai_api_key', e.target.value)} />
              </div>
              <div className="settings-field">
                <label>Anthropic API Key</label>
                <input type="password" placeholder="Enter Anthropic API key" value={settings.anthropic_api_key || ''} onChange={(e) => handleChange('anthropic_api_key', e.target.value)} />
              </div>
            </div>

            <div className="settings-section">
              <h3>External APIs</h3>
              <div className="settings-field">
                <label>SerpAPI Key (Required for Deep Web Research)</label>
                <input type="password" placeholder="Enter SerpAPI key for Google Search integration" value={settings.serpapi_key || ''} onChange={(e) => handleChange('serpapi_key', e.target.value)} />
              </div>
              <div className="settings-field">
                <label>Tavily API Key</label>
                <input type="password" placeholder="Enter Tavily API key" value={settings.tavily_api_key || ''} onChange={(e) => handleChange('tavily_api_key', e.target.value)} />
              </div>
            </div>

            <div className="settings-section">
              <h3>Help Package (Deliverables)</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 12 }}>Check the specific artifacts you want the agents to produce during analysis.</p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {['Strategy (Default)', 'Pre-written Emails', 'Contact List', 'Possible Lawsuits', 'Mermaid Diagrams', 'Generated Images/Audio'].map((item) => {
                  const isChecked = (settings.help_package || ['Strategy (Default)']).includes(item);
                  return (
                    <label key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleCheckboxToggle('help_package', item)}
                        style={{ accentColor: 'var(--accent)', cursor: 'pointer' }}
                      />
                      {item}
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="settings-section">
              <h3>Agent Configuration</h3>
              <div className="settings-field">
                <label>Debate Rounds (0–10)</label>
                <input type="number" min={0} max={10} value={settings.debate_rounds ?? 2} onChange={(e) => handleChange('debate_rounds', parseInt(e.target.value) || 0)} />
              </div>
            </div>

            <div className="settings-section">
              <h3>Processing</h3>
              <div className="settings-field">
                <label>Chunk Size</label>
                <input type="number" min={200} max={5000} value={settings.chunk_size ?? 1000} onChange={(e) => handleChange('chunk_size', parseInt(e.target.value) || 1000)} />
              </div>
              <div className="settings-field">
                <label>OCR Engine</label>
                <select value={settings.ocr_engine || 'vision'} onChange={(e) => handleChange('ocr_engine', e.target.value)}>
                  <option value="vision">Apple Vision</option>
                  <option value="tesseract">Tesseract</option>
                </select>
              </div>
              <div className="settings-field">
                <label>Transcription Engine</label>
                <select value={settings.transcription_engine || 'whisper'} onChange={(e) => handleChange('transcription_engine', e.target.value)}>
                  <option value="whisper">OpenAI Whisper</option>
                  <option value="mlx-whisper">MLX Whisper</option>
                </select>
              </div>
            </div>

            <div className="settings-footer">
              <button className="btn-cancel" onClick={onClose}>Cancel</button>
              <button className="btn-save" onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save Settings'}</button>
            </div>
          </>
        )}

        {/* ── Agents Tab ── */}
        {tab === 'agents' && (
          <>
            <div className="agents-list">
              {agents.map((agent) => (
                <div key={agent.id} className="agent-card">
                  <div
                    className="agent-card-header"
                    onClick={() => setExpandedAgent(expandedAgent === agent.id ? null : agent.id)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      {expandedAgent === agent.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      <Bot size={18} style={{ color: '#60a5fa' }} />
                      <div>
                        <strong>{agent.name}</strong>
                        {agent.codename && (
                          <span style={{ color: '#9ca3af', fontSize: '0.78rem', marginLeft: 8 }}>
                            ({agent.codename})
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="agent-files-badge">
                      {Object.keys(agent.files).length} files
                    </div>
                  </div>

                  {expandedAgent === agent.id && (
                    <div className="agent-card-body">
                      {(['identity', 'skills', 'soul'] as const).map((fileKey) => {
                        const content = agent.files[fileKey];
                        if (!content) return null;

                        const isEditing = editingFile?.agentId === agent.id && editingFile?.file === fileKey;

                        return (
                          <div key={fileKey} className="agent-file-section">
                            <div className="agent-file-header">
                              <span className="agent-file-label">
                                {fileKey === 'identity' ? '🪪' : fileKey === 'skills' ? '⚡' : '💫'}
                                {' '}{fileKey.toUpperCase()}.md
                              </span>
                              {!isEditing ? (
                                <button
                                  className="agent-edit-btn"
                                  onClick={() => setEditingFile({ agentId: agent.id, file: fileKey, content })}
                                >
                                  Edit
                                </button>
                              ) : (
                                <button className="agent-edit-btn" style={{ color: '#34d399' }} onClick={handleSaveAgent}>
                                  <Save size={14} /> Save
                                </button>
                              )}
                            </div>
                            {isEditing ? (
                              <textarea
                                className="agent-file-editor"
                                value={editingFile.content}
                                onChange={(e) => setEditingFile({ ...editingFile, content: e.target.value })}
                                rows={12}
                              />
                            ) : (
                              <pre className="agent-file-preview">
                                {content.slice(0, 400)}
                                {content.length > 400 ? '\n...' : ''}
                              </pre>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Add New Agent */}
            {showNewAgent ? (
              <div className="new-agent-form">
                <input
                  className="prompt-input"
                  type="text"
                  placeholder="e.g. risk_assessor"
                  value={newAgentId}
                  onChange={(e) => setNewAgentId(e.target.value)}
                  style={{ fontSize: '0.88rem' }}
                />
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <button className="btn-cancel" onClick={() => setShowNewAgent(false)}>Cancel</button>
                  <button className="btn-save" onClick={handleCreateAgent} disabled={!newAgentId.trim() || saving}>
                    {saving ? 'Creating...' : 'Create Agent'}
                  </button>
                </div>
              </div>
            ) : (
              <button
                className="add-agent-btn"
                onClick={() => setShowNewAgent(true)}
              >
                <Plus size={16} /> Add New Agent
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
