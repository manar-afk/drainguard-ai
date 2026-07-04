import React, { useState, useEffect } from 'react';
import { HelpCircle, AlertCircle, ShieldCheck, Zap, Info } from 'lucide-react';

export default function RiskPrediction() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDrain, setSelectedDrain] = useState(null);

  useEffect(() => {
    fetch('/api/predictions')
      .then(res => res.json())
      .then(data => {
        setPredictions(data);
        setLoading(false);
        if (data.length > 0) {
          setSelectedDrain(data[0]);
        }
      })
      .catch(err => {
        console.error("Error loading predictions:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <p>Running AI prediction neural layers...</p>
      </div>
    );
  }

  const getSeverityBadgeClass = (sev) => {
    if (sev === 'Critical' || sev === 'Red') return 'badge-red';
    if (sev === 'High' || sev === 'Orange') return 'badge-orange';
    if (sev === 'Medium' || sev === 'Yellow') return 'badge-yellow';
    return 'badge-green';
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr', gap: '24px' }}>
      <div className="card" style={{ overflow: 'hidden' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Network Overflow Risk Assessment</h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
          Calculated using physical discharge capacity models binned with elevation gradients, forecast volumes, and historical overflows. Click any drain to view Explainable AI (XAI) factors.
        </p>

        <div className="table-container" style={{ maxHeight: '550px', overflowY: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Drain Segment</th>
                <th>Ward</th>
                <th>Condition</th>
                <th>Overflow Prob.</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {predictions.map(drain => (
                <tr 
                  key={drain.drain_id} 
                  style={{ 
                    cursor: 'pointer',
                    backgroundColor: selectedDrain?.drain_id === drain.drain_id ? 'var(--surface-variant)' : ''
                  }}
                  onClick={() => setSelectedDrain(drain)}
                >
                  <td><strong>{drain.drain_id}</strong></td>
                  <td>{drain.name}</td>
                  <td>{drain.ward}</td>
                  <td>{drain.condition_pct}%</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ 
                        flexGrow: 1, 
                        height: '6px', 
                        background: 'var(--border)', 
                        borderRadius: '3px',
                        overflow: 'hidden',
                        minWidth: '60px'
                      }}>
                        <div style={{ 
                          width: `${drain.overflow_probability * 100}%`,
                          height: '100%',
                          background: drain.overflow_probability > 0.8 ? 'red' : drain.overflow_probability > 0.5 ? 'orange' : drain.overflow_probability > 0.25 ? 'yellow' : 'green'
                        }}></div>
                      </div>
                      <span style={{ fontSize: '12px', fontWeight: '600', width: '32px' }}>
                        {(drain.overflow_probability * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${getSeverityBadgeClass(drain.severity)}`}>
                      {drain.severity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {selectedDrain ? (
          <div className="card" style={{ flexGrow: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700' }}>Explainable AI (XAI)</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Confidence: <strong>{(selectedDrain.confidence_score * 100).toFixed(0)}%</strong>
              </span>
            </div>

            <h4 style={{ fontWeight: '600', fontSize: '16px', marginBottom: '8px' }}>
              {selectedDrain.name} ({selectedDrain.drain_id})
            </h4>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              {selectedDrain.ward} • Elevation: {selectedDrain.elevation_m}m • Capacity: {selectedDrain.capacity_m3s} m³/s
            </p>

            <div style={{ marginBottom: '24px' }}>
              <h5 style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                AI Model Feature Weights
              </h5>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {Object.entries(selectedDrain.feature_importance).map(([feature, weight]) => (
                  <div key={feature}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                      <span>{feature}</span>
                      <strong>{weight}%</strong>
                    </div>
                    <div style={{ height: '8px', background: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ 
                        width: `${weight}%`, 
                        height: '100%', 
                        background: 'var(--primary)',
                        borderRadius: '4px'
                      }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ 
              border: '1px solid var(--border)', 
              borderRadius: 'var(--radius-sm)', 
              padding: '16px', 
              backgroundColor: 'var(--surface-variant)',
              marginBottom: '20px',
              fontSize: '13.5px',
              lineHeight: '1.6'
            }}>
              <h5 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '700', marginBottom: '8px', fontSize: '13px' }}>
                <Zap size={14} style={{ color: 'var(--primary)' }} />
                Reasoning Narrative
              </h5>
              <p>{selectedDrain.explainable_reasoning}</p>
            </div>

            {selectedDrain.overflow_probability > 0.35 && (
              <div style={{ 
                border: '1px solid var(--risk-orange)', 
                borderRadius: 'var(--radius-sm)', 
                padding: '16px', 
                backgroundColor: 'var(--risk-orange-bg)',
                color: 'var(--text)',
                marginBottom: '20px',
                fontSize: '13px'
              }}>
                <h5 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '700', marginBottom: '8px', color: 'var(--risk-orange)' }}>
                  <AlertCircle size={14} />
                  Predicted Local Impact Footprint
                </h5>
                <ul style={{ paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <li>Estimated Flood Area: <strong>{selectedDrain.estimated_flood_area_sqm} m²</strong></li>
                  <li>Water Accumulation Depth: <strong>{selectedDrain.estimated_accumulation_depth_cm} cm</strong></li>
                </ul>
              </div>
            )}

            {selectedDrain.overflow_probability <= 0.35 && (
              <div style={{ 
                border: '1px solid var(--risk-green)', 
                borderRadius: 'var(--radius-sm)', 
                padding: '16px', 
                backgroundColor: 'var(--risk-green-bg)',
                color: 'var(--text)',
                marginBottom: '20px',
                fontSize: '13px'
              }}>
                <h5 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '700', marginBottom: '8px', color: 'var(--risk-green)' }}>
                  <ShieldCheck size={14} />
                  Safe Zone Prediction
                </h5>
                <p>Drain has sufficient capacity and is de-silted adequately to handle predicted storm runoff. No overflow is expected.</p>
              </div>
            )}
          </div>
        ) : (
          <div className="card text-center" style={{ padding: '40px', flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <Info size={32} style={{ color: 'var(--text-secondary)', margin: '0 auto 12px' }} />
            <p>Select a drain from the table to load prediction explanations.</p>
          </div>
        )}
      </div>
    </div>
  );
}
