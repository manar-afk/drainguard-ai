import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  ShieldAlert, 
  CloudRain, 
  Droplet, 
  CheckCircle,
  Clock, 
  Users, 
  DollarSign, 
  TrendingDown,
  Hammer
} from 'lucide-react';

export default function Dashboard({ setActiveTab }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cleaningId, setCleaningId] = useState(null);

  const fetchDashboardData = () => {
    fetch('/api/dashboard')
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching dashboard data:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleCleanDrain = (drainId) => {
    setCleaningId(drainId);
    fetch(`/api/maintenance/clean/${drainId}`, {
      method: 'POST'
    })
    .then(res => res.json())
    .then(res => {
      setCleaningId(null);
      fetchDashboardData();
    })
    .catch(err => {
      console.error("Error cleaning drain:", err);
      setCleaningId(null);
    });
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <p>Analyzing monsoon forecasts and drainage models...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card text-center" style={{ padding: '40px' }}>
        <AlertTriangle size={48} style={{ color: 'var(--risk-red)', margin: '0 auto 16px' }} />
        <h3>Failed to load Dashboard data</h3>
        <p style={{ color: 'var(--text-secondary)' }}>Make sure the FastAPI backend is running and the database is generated.</p>
      </div>
    );
  }

  const getRiskBadgeClass = (val) => {
    if (val >= 75) return 'badge-red';
    if (val >= 50) return 'badge-orange';
    if (val >= 25) return 'badge-yellow';
    return 'badge-green';
  };

  return (
    <div>
      <div className="grid-kpi">
        <div className="card card-kpi">
          <div className="kpi-header">
            <span>Overall Flood Risk Index</span>
            <AlertTriangle size={18} style={{ color: 'var(--risk-red)' }} />
          </div>
          <div className="kpi-value" style={{ color: 'var(--risk-red)' }}>
            {data.flood_risk_index}%
          </div>
          <div className="kpi-footer">
            <span>Critical threshold is <strong>60%</strong></span>
          </div>
        </div>

        <div className="card card-kpi">
          <div className="kpi-header">
            <span>Drain Health Score</span>
            <Droplet size={18} style={{ color: 'var(--primary)' }} />
          </div>
          <div className="kpi-value" style={{ color: 'var(--primary)' }}>
            {data.drain_health_score}%
          </div>
          <div className="kpi-footer">
            <span>Average structural condition</span>
          </div>
        </div>

        <div className="card card-kpi">
          <div className="kpi-header">
            <span>Monsoon Readiness</span>
            <CheckCircle size={18} style={{ color: 'var(--risk-green)' }} />
          </div>
          <div className="kpi-value" style={{ color: 'var(--risk-green)' }}>
            {data.monsoon_readiness_score}%
          </div>
          <div className="kpi-footer">
            <span>Incorporates weather risk</span>
          </div>
        </div>

        <div className="card card-kpi">
          <div className="kpi-header">
            <span>Critical Choke Points</span>
            <ShieldAlert size={18} style={{ color: 'var(--risk-orange)' }} />
          </div>
          <div className="kpi-value" style={{ color: 'var(--risk-orange)' }}>
            {data.critical_choke_points}
          </div>
          <div className="kpi-footer">
            <span style={{ cursor: 'pointer' }} onClick={() => setActiveTab('map')}>
              Click to view locations
            </span>
          </div>
        </div>
      </div>

      <div className="actions-layout">
        <div className="card" style={{ flexGrow: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>AI Recommended Immediate Actions</h3>
            <span className="badge badge-red animate-pulse-slow">High Urgency</span>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {data.recommended_actions.map(action => (
              <div 
                key={action.drain_id} 
                style={{ 
                  border: '1px solid var(--border)', 
                  borderRadius: 'var(--radius-md)', 
                  padding: '20px', 
                  backgroundColor: 'var(--surface-variant)' 
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <h4 style={{ fontWeight: '600', fontSize: '16px' }}>{action.drain_name} ({action.drain_id})</h4>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{action.ward} • Silt Level: {100 - action.condition}%</p>
                  </div>
                  <span className={`badge ${getRiskBadgeClass(action.condition < 50 ? 80 : 40)}`}>
                    {action.risk_status} Risk
                  </span>
                </div>
                
                <p style={{ fontSize: '14px', marginBottom: '16px', lineHeight: '1.5' }}>
                  {action.executive_summary}
                </p>
                
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Users size={14} /> {action.details.workers} workers
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={14} /> {action.details.time_hours} hrs
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <DollarSign size={14} /> ${action.details.cost}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <TrendingDown size={14} /> -{action.details.workers * 6}% overflow risk
                  </span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {action.details.equipment.map((eq, i) => (
                      <span key={i} style={{ fontSize: '11px', background: 'var(--border)', padding: '2px 8px', borderRadius: '4px' }}>
                        {eq}
                      </span>
                    ))}
                  </div>
                  
                  <button 
                    className="btn btn-primary" 
                    style={{ padding: '8px 16px', fontSize: '13px' }}
                    onClick={() => handleCleanDrain(action.drain_id)}
                    disabled={cleaningId === action.drain_id}
                  >
                    <Hammer size={14} />
                    {cleaningId === action.drain_id ? 'Dispatching Crew...' : 'Mark Cleaned'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="card" style={{ background: 'linear-gradient(135deg, var(--primary-container), var(--surface))' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CloudRain size={18} />
              Weather Intelligence Alert
            </h3>
            
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ 
                width: '60px', 
                height: '60px', 
                borderRadius: '50%', 
                backgroundColor: 'var(--surface)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center' 
              }}>
                <CloudRain size={32} style={{ color: 'var(--primary)' }} />
              </div>
              <div>
                <span className={`badge ${
                  data.rainfall_forecast.alert_level === 'Red' ? 'badge-red' :
                  data.rainfall_forecast.alert_level === 'Orange' ? 'badge-orange' :
                  data.rainfall_forecast.alert_level === 'Yellow' ? 'badge-yellow' : 'badge-green'
                }`}>
                  {data.rainfall_forecast.alert_level} Alert
                </span>
                <h4 style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px' }}>
                  {data.rainfall_forecast.rainfall_mm} mm
                </h4>
              </div>
            </div>
            
            <p style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '16px', lineHeight: '1.6' }}>
              A heavy monsoon wave is predicted over the next 24 hours. The high rainfall intensity will saturate local soils and pressure the drainage lines.
            </p>
            
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
              <span>Temp: <strong>{data.rainfall_forecast.temperature_c}°C</strong></span>
              <span style={{ marginLeft: '16px' }}>Humidity: <strong>{data.rainfall_forecast.humidity_pct}%</strong></span>
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>
              High Vulnerability Wards
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {data.high_risk_wards.map((ward, i) => (
                <div 
                  key={i} 
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center', 
                    padding: '12px 16px', 
                    borderRadius: 'var(--radius-sm)', 
                    backgroundColor: 'var(--surface-variant)',
                    borderLeft: `4px solid ${i === 0 ? 'var(--risk-red)' : 'var(--risk-orange)'}`
                  }}
                >
                  <span style={{ fontWeight: '600' }}>{ward}</span>
                  <span className={`badge ${i === 0 ? 'badge-red' : 'badge-orange'}`}>
                    {i === 0 ? 'Critical Risk' : 'High Risk'}
                  </span>
                </div>
              ))}
              
              <div 
                style={{ 
                  marginTop: '12px', 
                  fontSize: '13px', 
                  color: 'var(--primary)', 
                  textAlign: 'center', 
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
                onClick={() => setActiveTab('predictions')}
              >
                View Detailed Risk Forecast &rarr;
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
