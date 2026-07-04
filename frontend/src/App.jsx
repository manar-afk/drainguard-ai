import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Map, 
  TrendingUp, 
  Play, 
  Eye, 
  MessageSquare, 
  AlertTriangle, 
  BarChart3, 
  Sun, 
  Moon, 
  Key, 
  Sparkles, 
  Activity,
  X
} from 'lucide-react';

import Dashboard from './components/Dashboard';
import ChokePointsMap from './components/ChokePointsMap';
import RiskPrediction from './components/RiskPrediction';
import FloodSimulation from './components/FloodSimulation';
import VisionInspection from './components/VisionInspection';
import DecisionCopilot from './components/DecisionCopilot';
import CitizenReporting from './components/CitizenReporting';
import Analytics from './components/Analytics';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [darkTheme, setDarkTheme] = useState(true);
  const [apiKeyModal, setApiKeyModal] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [hasApiKey, setHasApiKey] = useState(false);

  useEffect(() => {
    // Check if backend already has API key configured
    fetch('/api/settings/apikey')
      .then(res => res.json())
      .then(data => {
        setHasApiKey(data.has_key);
      })
      .catch(err => console.error("Error checking API key status:", err));
  }, []);

  const handleSaveApiKey = () => {
    fetch('/api/settings/apikey', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey })
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        setHasApiKey(!!apiKey.trim());
        setApiKeyModal(false);
      }
    })
    .catch(err => console.error("Error setting API key:", err));
  };

  const toggleTheme = () => {
    setDarkTheme(!darkTheme);
  };

  const navItems = [
    { id: 'dashboard', label: 'Decision Dashboard', icon: LayoutDashboard },
    { id: 'map', label: 'Smart Choke Points', icon: Map },
    { id: 'predictions', label: 'Risk Predictions', icon: TrendingUp },
    { id: 'simulation', label: 'Flood Simulation', icon: Play },
    { id: 'vision', label: 'Vision Inspection', icon: Eye },
    { id: 'copilot', label: 'Decision Copilot', icon: MessageSquare },
    { id: 'citizen', label: 'Citizen reporting', icon: AlertTriangle },
    { id: 'analytics', label: 'Analytics Panel', icon: BarChart3 },
  ];

  return (
    <div className={`app-container ${darkTheme ? 'dark-theme' : ''}`}>
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-icon">DG</div>
          <div className="logo-text">
            <h1>DrainGuard AI</h1>
            <p>Decision Platform</p>
          </div>
        </div>
        
        <ul className="sidebar-nav">
          {navItems.map(item => {
            const Icon = item.icon;
            return (
              <li 
                key={item.id}
                className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </li>
            );
          })}
        </ul>
        
        <div className="sidebar-footer">
          <div 
            className={`api-key-indicator ${hasApiKey ? 'active' : ''}`}
            onClick={() => setApiKeyModal(true)}
          >
            <Key size={14} />
            <span>{hasApiKey ? 'Live Gemini Mode' : 'Simulated Mode'}</span>
          </div>
        </div>
      </aside>

      {/* Main Core View Area */}
      <div style={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
        <header className="header">
          <div className="header-title">
            <h2>
              {navItems.find(item => item.id === activeTab)?.label}
            </h2>
          </div>
          <div className="header-actions">
            <button className="icon-btn" onClick={toggleTheme} title="Toggle Theme">
              {darkTheme ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '13px' }}>
              <Activity size={16} className="text-primary animate-pulse" />
              <span>Platform Active</span>
            </div>
          </div>
        </header>

        <main className="main-content">
          {activeTab === 'dashboard' && <Dashboard setActiveTab={setActiveTab} />}
          {activeTab === 'map' && <ChokePointsMap />}
          {activeTab === 'predictions' && <RiskPrediction />}
          {activeTab === 'simulation' && <FloodSimulation />}
          {activeTab === 'vision' && <VisionInspection />}
          {activeTab === 'copilot' && <DecisionCopilot />}
          {activeTab === 'citizen' && <CitizenReporting />}
          {activeTab === 'analytics' && <Analytics />}
        </main>
      </div>

      {/* Settings Modal for API Key */}
      {apiKeyModal && (
        <div className="api-modal-overlay">
          <div className="api-modal">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '18px' }}>
                <Sparkles size={18} className="text-primary" />
                Configure Vertex AI / Gemini API
              </h3>
              <button className="icon-btn" onClick={() => setApiKeyModal(false)}>
                <X size={18} />
              </button>
            </div>
            
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Input your Gemini API key below to unlock live, real-time response generation and actual computer vision analysis. If empty, the system runs on pre-baked rule simulations based on the datasets.
            </p>
            
            <div className="form-group">
              <label>Gemini API Key</label>
              <input 
                type="password" 
                className="form-control" 
                placeholder="AIzaSy..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
            
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '24px' }}>
              <button className="btn btn-secondary" onClick={() => setApiKeyModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSaveApiKey}>Save Config</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
