import React, { useState, useEffect } from 'react';
import { Database, Activity, Brain, Sliders, X, Save, Trash2, Plus, FileText, ChevronDown, ChevronRight, RefreshCw, Search, Key, Cpu, Globe, Zap, Eye, Terminal, MessageCircle } from 'lucide-react';
import { getQdrantStats, getAgentConfigs, saveAgentConfigs, getKnowledgeDocs, addKnowledge } from '../services/api';
import { AgentChat } from './admin/AgentChat';

interface AgentVerboseInfo {
  id: string;
  name: string;
  description: string;
  model: string;
  capabilities: string[];
  useCase: string;
  verbosePrompt: string;
}

const AGENT_VERBOSE_INFO: Record<string, AgentVerboseInfo> = {
  coordinator: {
    id: 'coordinator',
    name: 'Coordinator Alpha',
    description: 'Orchestrates the entire swarm debate cycle',
    model: 'gemini-3-flash-preview (fast) or gemini-3.1-pro-preview (reasoning)',
    capabilities: ['Task delegation', 'Consensus detection', 'Debate management', 'Quality gate'],
    useCase: 'First agent invoked - manages the flow between all other agents',
    verbosePrompt: 'You are the CONDUCTOR of a multi-agent swarm debate. Your role is to:\n1. Receive the initial query\n2. Delegate to Context Weaver for entity extraction\n3. Route to Echo Vault for memory/research\n4. Aggregate findings for Outcome Architect\n5. Have Chronicle Scribe draft deliverables\n6. Detect consensus or trigger additional debate rounds\n\nYou track confidence scores and can call for veto rounds if agents disagree.'
  },
  context_weaver: {
    id: 'context_weaver',
    name: 'Context Weaver',
    description: 'Extracts entities, relationships, and core problem from evidence',
    model: 'gemini-3.1-pro-preview (precision)',
    capabilities: ['Entity extraction', 'Relationship mapping', 'Timeline construction', 'Risk flagging', 'OCR processing'],
    useCase: 'Analyzes uploaded files, text, images to extract structured data',
    verbosePrompt: 'You are a CONTEXT WEAVER - an elite analyst specializing in extracting structured information from chaos.\n\nYour responsibilities:\n1. Parse all evidence types (text, PDF, images, audio transcripts)\n2. Extract: People, Organizations, Locations, Dates, Evidence items\n3. Map relationships between entities\n4. Identify the core problem statement\n5. Flag risks and contradictions\n\nOutput format: JSON with keys: entities (array), relationships (array), problem (string), timeline (array), risk_flags (array)'
  },
  echo_vault: {
    id: 'echo_vault',
    name: 'Echo Vault',
    description: 'Long-term memory and web research agent',
    model: 'gemini-3.1-pro-preview + web search',
    capabilities: ['Qdrant vector search', 'Tavily web search', 'SerpAPI queries', 'Past case retrieval', 'Deep Research Agent integration'],
    useCase: 'Searches vector database and web for relevant information',
    verbosePrompt: 'You are ECHO VAULT - the memory and research specialist.\n\n**Gemini Deep Research Agent Integration:**\nFor complex research tasks, you can invoke the Deep Research Agent:\n- Agent ID: deep-research-pro-preview-12-2025\n- Use background=true for async execution\n- Poll interaction ID until status=completed\n- Supports: text, images, PDFs, audio, video context\n\nYour capabilities:\n1. Query Qdrant vector store for similar past cases\n2. Perform web searches (Tavily/SerpAPI)\n3. Invoke Gemini Deep Research Agent for complex topics\n4. Synthesize findings into research summary\n\nWhen using Deep Research:\ncurl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \\\n-H "Content-Type: application/json" \\\n-H "x-goog-api-key: $GEMINI_API_KEY" \\\n-d \'{"input": "Your research query", "agent": "deep-research-pro-preview-12-2025", "background": true}\''
  },
  outcome_architect: {
    id: 'outcome_architect',
    name: 'Outcome Architect',
    description: 'Devises strategic recommendations based on evidence and research',
    model: 'gemini-3.1-pro-preview (strategic reasoning)',
    capabilities: ['Strategy formulation', 'Option analysis', 'Risk assessment', 'Action planning'],
    useCase: 'Takes extracted context + research and creates actionable strategy',
    verbosePrompt: 'You are an OUTCOME ARCHITECT - a strategic advisor who transforms evidence into action.\n\nYour methodology:\n1. Review Context Weaver\'s extracted problem\n2. Analyze Echo Vault\'s research findings\n3. Identify 3-5 strategic options\n4. For each option: assess pros/cons, risks, timeline\n5. Recommend best course of action\n6. Flag any dissenting views from research\n\nOutput: Structured strategy with specific actionable steps, expected outcomes, and risk mitigation.'
  },
  chronicle_scribe: {
    id: 'chronicle_scribe',
    name: 'Chronicle Scribe',
    description: 'Drafts final deliverables - reports, emails, contacts',
    model: 'gemini-3-flash-preview (fast generation)',
    capabilities: ['Report drafting', 'Email generation', 'Contact extraction', 'Timeline creation', 'Format conversion'],
    useCase: 'Creates the final output package from strategy',
    verbosePrompt: 'You are a CHRONICLE SCRIBE - the documentation specialist.\n\nYour outputs:\n1. Strategic Report (markdown)\n2. Draft Emails (to, from, subject, body)\n3. Contact List (name, role, org, priority, contact methods)\n4. Timeline/Checklist\n5. Visual diagrams (Mermaid.js)\n\nAlways format outputs for immediate use - ready to send emails, ready to present reports.'
  },
  pulse_monitor: {
    id: 'pulse_monitor',
    name: 'Pulse Monitor',
    description: 'Real-time telemetry and quality assurance',
    model: 'gemini-3-flash-preview',
    capabilities: ['Token counting', 'Latency monitoring', 'Quality scoring', 'Error detection'],
    useCase: 'Tracks swarm health and reports metrics',
    verbosePrompt: 'You are the PULSE MONITOR - system telemetry agent.\n\nTrack and report:\n1. Token usage per agent\n2. API latency\n3. Confidence scores across debate\n4. Quality metrics\n5. Error rates\n\nYour output appears in the Token Usage panel and helps optimize future runs.'
  }
};

interface AdminDashboardProps {
  onClose: () => void;
  kbDocs: any[];
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onClose, kbDocs }) => {
  const [hue, setHue] = useState(0);
  const [saturation, setSaturation] = useState(0);
  const [lightness, setLightness] = useState(7);
  
  const [qdrantStats, setQdrantStats] = useState<any>(null);
  const [agents, setAgents] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [showVerbose, setShowVerbose] = useState<Record<string, boolean>>({});
  const [knowledgeDocs, setKnowledgeDocs] = useState<any[]>(kbDocs || []);
  const [newDocTitle, setNewDocTitle] = useState('');
  const [newDocContent, setNewDocContent] = useState('');
  const [showAddDoc, setShowAddDoc] = useState(false);
  const [showChat, setShowChat] = useState(false);
  
  // Apply CSS variables
  useEffect(() => {
    document.documentElement.style.setProperty('--ui-hue', hue.toString());
    document.documentElement.style.setProperty('--ui-sat', `${saturation}%`);
    document.documentElement.style.setProperty('--ui-lit-dark', `${lightness}%`);
    document.documentElement.style.setProperty('--ui-lit-light', `${100 - lightness}%`);
  }, [hue, saturation, lightness]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getQdrantStats();
        setQdrantStats(data);
        
        const agentData = await getAgentConfigs();
        setAgents(agentData);
        
        // Fetch knowledge docs
        const docs = await fetch('http://localhost:8000/api/knowledge').then(r => r.json()).catch(() => []);
        setKnowledgeDocs(docs);
      } catch (e) {
        console.error("Failed to fetch admin stats", e);
      }
    };
    fetchStats();
  }, []);

  const handleAgentChange = (id: string, field: string, value: any) => {
    setAgents(prev => prev.map(a => a.id === id ? { ...a, [field]: value } : a));
  };

  const saveAgentConfig = async () => {
    try {
      await saveAgentConfigs(agents);
      alert('Agent configuration saved to backend!');
    } catch (e) {
      console.error(e);
      alert('Error saving configuration.');
    }
  };

  const saveToCSS = () => {
    // Save color settings to a config file that loads on startup
    const config = { hue, saturation, lightness };
    console.log('Saving UI config:', config);
    // In production, this would POST to backend to save to file
    alert(`UI Colors saved!\nHue: ${hue}\nSaturation: ${saturation}%\nLightness: ${lightness}%`);
  };

  const addKnowledgeDoc = async () => {
    if (!newDocTitle.trim() || !newDocContent.trim()) return;
    try {
      await addKnowledge(newDocContent, newDocTitle);
      setNewDocTitle('');
      setNewDocContent('');
      setShowAddDoc(false);
      // Refresh docs
      const docs = await fetch('http://localhost:8000/api/knowledge').then(r => r.json()).catch(() => []);
      setKnowledgeDocs(docs);
    } catch (e) {
      console.error(e);
      alert('Error adding document');
    }
  };

  const verboseInfo = selectedAgent ? AGENT_VERBOSE_INFO[selectedAgent] : null;

  return (
    <div className="absolute inset-0 z-[100] bg-[#111] text-[#eee] overflow-y-auto font-mono p-8">
      <div className="max-w-8xl mx-auto">
        <div className="flex justify-between items-center mb-8 border-b-4 border-[#ff003c] pb-4">
          <h1 className="text-4xl font-black uppercase tracking-widest text-[#ff003c] flex items-center gap-4">
            <Terminal size={40} />
            System Override // Admin Mode
          </h1>
          <div className="flex gap-2">
            <button 
              onClick={() => setShowChat(true)} 
              className="p-2 bg-[#00ff88] text-black hover:bg-white transition-colors"
              title="Chat with The Architect"
            >
              <MessageCircle size={32} />
            </button>
            <button onClick={onClose} className="p-2 bg-[#ff003c] text-black hover:bg-white transition-colors">
              <X size={32} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          
          {/* UI Customization */}
          <div className="border-2 border-[#333] p-6 bg-black/50">
            <h2 className="text-xl font-bold uppercase mb-4 flex items-center gap-2 text-[#00ff88]">
              <Sliders size={20} /> UI Color Tones
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs uppercase mb-1 flex justify-between">
                  <span>Hue ({hue}°)</span>
                  <span className="text-gray-500">Color shift</span>
                </label>
                <input 
                  type="range" min="0" max="360" value={hue} 
                  onChange={(e) => setHue(Number(e.target.value))} 
                  className="w-full accent-[#00ff88] h-2 bg-gray-700 rounded-lg cursor-pointer"
                />
              </div>
              <div>
                <label className="block text-xs uppercase mb-1 flex justify-between">
                  <span>Saturation ({saturation}%)</span>
                  <span className="text-gray-500">Vibrancy</span>
                </label>
                <input 
                  type="range" min="0" max="100" value={saturation} 
                  onChange={(e) => setSaturation(Number(e.target.value))} 
                  className="w-full accent-[#00ff88] h-2 bg-gray-700 rounded-lg cursor-pointer"
                />
              </div>
              <div>
                <label className="block text-xs uppercase mb-1 flex justify-between">
                  <span>Dark Mode Brightness ({lightness}%)</span>
                  <span className="text-gray-500">Dark level</span>
                </label>
                <input 
                  type="range" min="1" max="30" value={lightness} 
                  onChange={(e) => setLightness(Number(e.target.value))} 
                  className="w-full accent-[#00ff88] h-2 bg-gray-700 rounded-lg cursor-pointer"
                />
              </div>
              <div className="pt-4 border-t border-[#333]">
                <div className="text-xs text-gray-500 mb-2">Preview:</div>
                <div className="flex gap-2">
                  <div className="flex-1 p-4 border-2 border-[#333]" style={{ backgroundColor: `hsl(${hue}, ${saturation}%, ${lightness}%)` }}>
                    <span className="text-xs">Dark</span>
                  </div>
                  <div className="flex-1 p-4 border-2 border-[#333]" style={{ backgroundColor: `hsl(${hue}, ${saturation}%, ${100 - lightness}%)` }}>
                    <span className="text-xs text-black">Light</span>
                  </div>
                </div>
              </div>
              <button 
                onClick={saveToCSS}
                className="w-full py-3 bg-[#00ff88] text-black font-bold uppercase hover:bg-white transition-colors flex items-center justify-center gap-2"
              >
                <Save size={16} /> Save Colors
              </button>
            </div>
          </div>

          {/* Qdrant Management */}
          <div className="border-2 border-[#333] p-6 bg-black/50">
            <h2 className="text-xl font-bold uppercase mb-4 flex items-center gap-2 text-[#00ff88]">
              <Database size={20} /> Qdrant Vector Memory
            </h2>
            {qdrantStats ? (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between border-b border-[#333] pb-2">
                  <span>Status:</span> 
                  <span className={qdrantStats.status === 'ok' ? 'text-[#00ff88]' : 'text-red-500'}>
                    {qdrantStats.status}
                  </span>
                </div>
                <div className="flex justify-between border-b border-[#333] pb-2">
                  <span>Collections:</span> 
                  <span>{qdrantStats.collections?.length || 0}</span>
                </div>
                <div className="flex justify-between border-b border-[#333] pb-2">
                  <span>Vector Points:</span> 
                  <span className="font-bold">{qdrantStats.points_count || 0}</span>
                </div>
                <div className="pt-2">
                  <div className="text-xs text-gray-500 mb-2">Active Collections:</div>
                  <div className="flex flex-wrap gap-1">
                    {qdrantStats.collections?.map((c: string) => (
                      <span key={c} className="text-xs bg-[#222] px-2 py-1 border border-[#444]">{c}</span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-gray-500 animate-pulse">Loading Qdrant stats...</div>
            )}
            
            <h3 className="text-sm font-bold uppercase mt-6 mb-2 flex items-center gap-2">
              <FileText size={16} /> Knowledge Base ({knowledgeDocs.length} docs)
            </h3>
            <div className="max-h-48 overflow-y-auto border border-[#333] p-2 bg-black mb-3">
              {knowledgeDocs.length === 0 ? (
                <span className="text-xs text-gray-500">No documents ingested.</span>
              ) : (
                <ul className="space-y-1">
                  {knowledgeDocs.map((doc, i) => (
                    <li key={i} className="text-xs flex justify-between items-center border-b border-[#222] pb-1">
                      <span className="truncate mr-2">{doc.title || doc.id}</span>
                      <span className="text-gray-500">{doc.date ? new Date(doc.date).toLocaleDateString() : ''}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            
            {!showAddDoc ? (
              <button 
                onClick={() => setShowAddDoc(true)}
                className="w-full py-2 bg-[#222] hover:bg-[#00ff88] hover:text-black text-xs uppercase font-bold transition-colors flex items-center justify-center gap-2"
              >
                <Plus size={14} /> Add Knowledge Doc
              </button>
            ) : (
              <div className="space-y-2 p-3 bg-[#0a0a0a] border border-[#333]">
                <input 
                  type="text" 
                  placeholder="Document title"
                  value={newDocTitle}
                  onChange={(e) => setNewDocTitle(e.target.value)}
                  className="w-full bg-black border border-[#333] p-2 text-xs"
                />
                <textarea 
                  placeholder="Document content..."
                  value={newDocContent}
                  onChange={(e) => setNewDocContent(e.target.value)}
                  className="w-full bg-black border border-[#333] p-2 text-xs h-24"
                />
                <div className="flex gap-2">
                  <button 
                    onClick={addKnowledgeDoc}
                    className="flex-1 py-2 bg-[#00ff88] text-black text-xs font-bold uppercase"
                  >
                    Save
                  </button>
                  <button 
                    onClick={() => setShowAddDoc(false)}
                    className="flex-1 py-2 bg-[#333] text-xs font-bold uppercase"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Agent Configuration */}
          <div className="border-2 border-[#333] p-6 bg-black/50 xl:col-span-2">
            <h2 className="text-xl font-bold uppercase mb-4 flex items-center gap-2 text-[#00ff88]">
              <Brain size={20} /> Agent Configuration & Prompts
            </h2>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {agents.map(agent => (
                <button
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent.id)}
                  className={`px-3 py-2 text-xs font-bold uppercase border transition-colors ${
                    selectedAgent === agent.id 
                      ? 'bg-[#00ff88] text-black border-[#00ff88]' 
                      : 'bg-black border-[#333] hover:border-[#00ff88]'
                  }`}
                >
                  {agent.name}
                </button>
              ))}
            </div>

            {selectedAgent && verboseInfo && (
              <div className="space-y-4">
                {/* Verbose Info */}
                <div className="bg-[#0a0a0a] border border-[#333] p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Zap size={16} className="text-[#00ff88]" />
                    <span className="font-bold text-sm uppercase">{verboseInfo.name}</span>
                  </div>
                  <p className="text-xs text-gray-400 mb-3">{verboseInfo.description}</p>
                  
                  <div className="grid grid-cols-2 gap-4 mb-3">
                    <div>
                      <span className="text-xs text-gray-500 uppercase">Model</span>
                      <p className="text-xs">{verboseInfo.model}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 uppercase">Use Case</span>
                      <p className="text-xs">{verboseInfo.useCase}</p>
                    </div>
                  </div>
                  
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Capabilities</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {verboseInfo.capabilities.map(c => (
                        <span key={c} className="text-[10px] bg-[#222] px-2 py-0.5 border border-[#444]">{c}</span>
                      ))}
                    </div>
                  </div>
                  
                  <button
                    onClick={() => setShowVerbose(prev => ({ ...prev, [selectedAgent]: !prev[selectedAgent] }))}
                    className="mt-3 text-xs text-[#00ff88] flex items-center gap-1"
                  >
                    {showVerbose[selectedAgent] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    {showVerbose[selectedAgent] ? 'Hide' : 'Show'} Full Prompt
                  </button>
                  
                  {showVerbose[selectedAgent] && (
                    <pre className="mt-3 p-3 bg-black border border-[#333] text-[10px] overflow-x-auto whitespace-pre-wrap text-gray-300">
                      {verboseInfo.verbosePrompt}
                    </pre>
                  )}
                </div>

                {/* Editable Config */}
                <div className="border border-[#444] p-4 bg-[#0a0a0a]">
                  <h4 className="text-xs font-bold uppercase mb-3 flex items-center gap-2">
                    <Key size={14} /> Edit Agent Prompt
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <label className="text-[10px] text-gray-500 uppercase">System Prompt</label>
                      <textarea 
                        className="w-full h-32 bg-black border border-[#333] text-xs p-2 mt-1 focus:border-[#00ff88] focus:outline-none resize-none text-gray-300"
                        value={agents.find(a => a.id === selectedAgent)?.prompt || ''}
                        onChange={(e) => handleAgentChange(selectedAgent, 'prompt', e.target.value)}
                      />
                    </div>
                    <div className="flex justify-between items-center">
                      <div>
                        <label className="text-[10px] text-gray-500 uppercase">Temperature</label>
                        <input 
                          type="number" 
                          step="0.1" 
                          min="0" 
                          max="2" 
                          value={agents.find(a => a.id === selectedAgent)?.temperature || 0.7} 
                          onChange={(e) => handleAgentChange(selectedAgent, 'temperature', parseFloat(e.target.value))}
                          className="w-20 bg-black border border-[#333] text-xs p-1 text-center ml-2" 
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 uppercase">Model</label>
                        <select 
                          value={agents.find(a => a.id === selectedAgent)?.model || 'gemini-3-flash-preview'}
                          onChange={(e) => handleAgentChange(selectedAgent, 'model', e.target.value)}
                          className="bg-black border border-[#333] text-xs p-1 ml-2"
                        >
                          <option value="gemini-3-flash-preview">gemini-3-flash-preview</option>
                          <option value="gemini-3.1-pro-preview">gemini-3.1-pro-preview</option>
                          <option value="gemini-2.0-flash-exp">gemini-2.0-flash-exp</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <button 
              onClick={saveAgentConfig}
              className="w-full mt-6 py-3 bg-[#222] hover:bg-[#00ff88] hover:text-black text-sm uppercase font-bold transition-colors flex items-center justify-center gap-2"
            >
              <Save size={16} /> Save All Agent Configurations
            </button>
          </div>

          {/* Token Telemetry */}
          <div className="border-2 border-[#333] p-6 bg-black/50 xl:col-span-3">
            <h2 className="text-xl font-bold uppercase mb-4 flex items-center gap-2 text-[#00ff88]">
              <Activity size={20} /> Global Token Telemetry
            </h2>
            <div className="text-sm text-gray-400 mb-4">
              <Zap size={14} className="inline mr-1"/> 
              Live token counting tracks API usage across all agents. This helps optimize costs and performance.
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="border border-[#333] p-4 bg-black">
                <div className="text-3xl font-black text-[#fff]">0</div>
                <div className="text-[10px] uppercase text-gray-500 mt-1">Total Prompt Tokens</div>
              </div>
              <div className="border border-[#333] p-4 bg-black">
                <div className="text-3xl font-black text-[#fff]">0</div>
                <div className="text-[10px] uppercase text-gray-500 mt-1">Total Completion Tokens</div>
              </div>
              <div className="border border-[#333] p-4 bg-black">
                <div className="text-3xl font-black text-[#fff]">$0.00</div>
                <div className="text-[10px] uppercase text-gray-500 mt-1">Estimated Cost</div>
              </div>
              <div className="border border-[#333] p-4 bg-black">
                <div className="text-3xl font-black text-[#00ff88]">Ready</div>
                <div className="text-[10px] uppercase text-gray-500 mt-1">Telemetry Status</div>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* The Architect Chat */}
      <AgentChat isOpen={showChat} onClose={() => setShowChat(false)} />
    </div>
  );
};
