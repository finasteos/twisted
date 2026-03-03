import { Activity, Cpu, HardDrive, Thermometer } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { getSystemHealth, type SystemHealth } from '../../api';

export const SystemStatus: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await getSystemHealth();
        setHealth(data);
        setError(null);
      } catch (err) {
        setError('Engine offline');
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="system-status-container glass-card offline">
        <div className="status-header">
          <Activity size={14} style={{ color: '#ef4444' }} />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!health) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok': return '#10b981'; // Green
      case 'error': return '#ef4444'; // Red
      case 'warning': return '#f59e0b'; // Amber
      case 'missing_key': return '#6b7280'; // Gray
      default: return '#6b7280';
    }
  };

  const getThermalColor = (state: string) => {
    switch (state) {
      case 'cool': return '#10b981';
      case 'warm': return '#f59e0b';
      case 'hot': return '#f97316';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className="system-status-container glass-card">
      <div className="status-header">
        <Activity size={14} className="pulse-icon" />
        <span>Glass Engine Health</span>
      </div>

      <div className="status-grid">
        {/* Resources Section */}
        <div className="status-section">
          <div className="status-item">
            <Cpu size={12} />
            <div className="status-bar-bg">
              <div
                className="status-bar-fg"
                style={{
                  width: `${health.resources?.cpu_percent || 0}%`,
                  backgroundColor: (health.resources?.cpu_percent || 0) > 80 ? '#ef4444' : '#60a5fa'
                }}
              />
            </div>
            <span className="status-value">{Math.round(health.resources?.cpu_percent || 0)}%</span>
          </div>

          <div className="status-item">
            <Thermometer size={12} />
            <span
              className="status-label"
              style={{ color: getThermalColor(health.resources?.thermal_state || 'unknown') }}
            >
              {(health.resources?.thermal_state || 'unknown').toUpperCase()}
            </span>
          </div>

          <div className="status-item">
            <HardDrive size={12} />
            <span className="status-value">
              {health.resources?.unified_memory_gb?.used || 0} / {health.resources?.unified_memory_gb?.total || 0} GB
            </span>
          </div>
        </div>

        {/* APIs Section */}
        <div className="status-section apis">
          <div className="api-dot-item">
            <div
              className="api-dot"
              style={{
                backgroundColor: getStatusColor(health.apis.gemini?.status || 'unknown'),
                boxShadow: `0 0 8px ${getStatusColor(health.apis.gemini?.status || 'unknown')}`
              }}
            />
            <span>Gemini</span>
          </div>

          <div className="api-dot-item">
            <div
              className="api-dot"
              style={{
                backgroundColor: getStatusColor(health.apis.search?.tavily?.status || 'unknown'),
                boxShadow: `0 0 8px ${getStatusColor(health.apis.search?.tavily?.status || 'unknown')}`
              }}
            />
            <div
              className="api-dot"
              style={{
                backgroundColor: getStatusColor(health.apis.search?.serpapi?.status || 'unknown'),
                boxShadow: `0 0 8px ${getStatusColor(health.apis.search?.serpapi?.status || 'unknown')}`,
                marginLeft: -4
              }}
            />
            <span>Search</span>
          </div>

          <div className="api-dot-item">
            <div
              className="api-dot"
              style={{
                backgroundColor: getStatusColor(health.apis.chromadb?.status || 'unknown'),
                boxShadow: `0 0 8px ${getStatusColor(health.apis.chromadb?.status || 'unknown')}`
              }}
            />
            <span>DB</span>
          </div>
        </div>
      </div>
    </div>
  );
};
