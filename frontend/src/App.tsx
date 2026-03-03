import { useCallback, useState } from 'react';
import { AgentFlowGraph } from './components/agentflow/AgentFlowGraph';
import { DropZone } from './components/dropzone/DropZone';
import { EventLog } from './components/eventlog/EventLog';
import { ReportView as ReportViewer } from './components/ReportView';
import { SettingsPanel as SettingsModal } from './components/SettingsPanel';
import { SystemStatus } from './components/system/SystemStatus';
import { AuroraBackground } from './components/ui/aurora-background';
import { useCaseState } from './hooks/useCaseState';
import { useWebSocket } from './hooks/useWebSocket';
import { CaseStatus } from './types/case';

/**
 * TWISTED: The Glass Engine
 * Main application entry point.
 */

function App() {
  const [caseId, setCaseId] = useState<string | null>(null);
  const [userQuery, setUserQuery] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [isCalmMode, setIsCalmMode] = useState(true);

  const {
    caseState,
    updateProgress,
    addAgentThought,
    addEventLog,
    updateAgentTasks,
    setDeliverables,
    resetCase
  } = useCaseState();

  const {
    connect,
    disconnect,
    sendMessage,
    isConnected
  } = useWebSocket({
    onProgress: updateProgress,
    onAgentThought: addAgentThought,
    onEventLog: addEventLog,
    onAgentTasks: updateAgentTasks,
    onComplete: setDeliverables,
    onError: (err: Error) => addEventLog({
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      level: 'ERROR',
      agent: 'System',
      message: err.message
    })
  });

  // Initialize new case
  const handleCreateCase = useCallback(async (query: string, enableDeepResearch: boolean) => {
    setUserQuery(query);

    const response = await fetch('http://localhost:8000/api/cases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_query: query,
        enable_deep_research: enableDeepResearch,
        priority: 5
      })
    });

    const data = await response.json();
    setCaseId(data.case_id);

    // Connect WebSocket for real-time updates
    connect(`ws://localhost:8000/ws/cases/${data.case_id}`);
  }, [connect]);

  // Reset for new case
  const handleReset = useCallback(() => {
    disconnect();
    resetCase();
    setCaseId(null);
    setUserQuery('');
  }, [disconnect, resetCase]);

  return (
    <AuroraBackground className="w-full">
      <div className="twisted-app w-full z-10">
        {/* Header */}
        <header className="glass-header w-full">
          <div className="logo">
            <span className="logo-twisted">TWISTED</span>
            <span className="logo-tagline">Glass Engine</span>
          </div>
          <div className="header-actions">
            <SystemStatus />
            <button
              className={`glass-button subtle ${!isCalmMode ? 'active' : ''}`}
              onClick={() => setIsCalmMode(!isCalmMode)}
              title="Toggle between Calm and Engine view"
            >
              {isCalmMode ? 'Engine Insight' : 'Calm Mode'}
            </button>
            <button
              className="glass-button subtle"
              onClick={() => setShowSettings(!showSettings)}
            >
              Settings
            </button>
            {caseState.status === CaseStatus.COMPLETE && (
              <button className="glass-button primary" onClick={handleReset}>
                New Case
              </button>
            )}
          </div>
        </header>

        {/* Main Content Area */}
        <main className="main-container w-full max-w-7xl mx-auto flex justify-center">
          {!caseId ? (
            <DropZone onCreateCase={handleCreateCase} />
          ) : (
            <div className={`engine-layout ${isCalmMode ? 'calm-view' : 'insight-view'} w-full`}>
              {/* Engine Panels (Hidden in Calm Mode) */}
              {!isCalmMode && (
                <>
                  <section className="panel flow-panel">
                    <h2 className="panel-title">Agent Swarm</h2>
                    <AgentFlowGraph
                      agents={caseState.agents}
                      connections={caseState.connections}
                      activeAgent={caseState.currentAgent}
                    />
                  </section>

                  <section className="panel log-panel">
                    <h2 className="panel-title">Event Log</h2>
                    <EventLog
                      entries={caseState.eventLog}
                      status={caseState.status}
                      progress={caseState.progress}
                      stage={caseState.stage}
                    />
                  </section>
                </>
              )}

              {/* Stage Summary (Visible in Calm Mode) */}
              {isCalmMode && caseState.status !== CaseStatus.COMPLETE && (
                 <section className="panel calm-status-panel w-full max-w-lg mx-auto">
                    <div className="calm-status-card glass-card">
                      <div className="pulse-indicator" />
                      <h2>{caseState.status === CaseStatus.ANALYZING ? 'Processing Evidence' : 'Deliberating Strategy'}</h2>
                      <p>{caseState.stage} — {Math.round(caseState.progress)}%</p>
                      <span className="subtle-hint">Switch to 'Engine Insight' to see the swarm in action.</span>
                    </div>
                 </section>
              )}

              {/* Deliverables Panel */}
              <section className="panel deliverables-panel w-full mx-auto max-w-4xl">
                {caseState.status === CaseStatus.COMPLETE ? (
                  <>
                    <h2 className="panel-title">Strategy</h2>
                    <ReportViewer
                      report={caseState.deliverables?.strategic_report || ''}
                      onNewAnalysis={handleReset}
                    />
                  </>
                ) : (
                  !isCalmMode && (
                    <div className="processing-placeholder glass-card">
                      <div className="pulse-indicator" />
                      <p>Swarm is deliberating...</p>
                      <span className="progress-detail">
                        {caseState.stage}: {Math.round(caseState.progress)}%
                      </span>
                    </div>
                  )
                )}
              </section>
            </div>
          )}
        </main>

        {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
      </div>
    </AuroraBackground>
  );
}

export default App;
