import React, { useState, useEffect } from 'react';
import { Play, TrendingDown, MapPin, Check, AlertTriangle, ShieldCheck } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function FloodSimulation() {
  const [rainValue, setRainValue] = useState(100);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const runSimulation = (val) => {
    setLoading(true);
    fetch(`/api/simulation?rainfall_mm=${val}`)
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error running simulation:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    runSimulation(rainValue);
  }, []);

  const handleSliderChange = (e) => {
    const val = parseInt(e.target.value);
    setRainValue(val);
  };

  const handleReleaseSlider = () => {
    runSimulation(rainValue);
  };

  if (!data) return null;

  const chartData = [
    {
      name: 'Overflow Drains',
      Current: data.summary.overflowing_drains_current,
      Optimized: data.summary.overflowing_drains_optimized
    },
    {
      name: 'Flooded Roads',
      Current: data.summary.affected_roads_current,
      Optimized: data.summary.affected_roads_optimized
    },
    {
      name: 'Markets Affected',
      Current: data.summary.affected_markets_current,
      Optimized: data.summary.affected_markets_optimized
    },
    {
      name: 'Schools/Hospitals',
      Current: data.summary.hospitals_at_risk_current,
      Optimized: data.summary.hospitals_at_risk_optimized
    }
  ];

  return (
    <div>
      <div className="sim-controls">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '50px', height: '50px', borderRadius: '50%', backgroundColor: 'var(--primary-container)', color: 'var(--primary)' }}>
          <Play size={24} />
        </div>
        <div className="slider-group">
          <label>
            <span>Simulate Rainfall Intensity Scenario</span>
            <strong>{rainValue} mm (3-Hour Monsoon Downpour)</strong>
          </label>
          <input 
            type="range" 
            min="50" 
            max="200" 
            step="10"
            value={rainValue} 
            onChange={handleSliderChange}
            onMouseUp={handleReleaseSlider}
            onTouchEnd={handleReleaseSlider}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>
            <span>50mm (Moderate)</span>
            <span>100mm (Heavy)</span>
            <span>150mm (Very Heavy)</span>
            <span>200mm (Extreme Flood Warning)</span>
          </div>
        </div>
      </div>

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', margin: '20px 0' }}>
          <p>Running hydro-geographic simulations...</p>
        </div>
      )}

      {!loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="simulation-layout">
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '8px' }}>Simulation Summary</h3>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                  Compares the impact of {rainValue}mm rain on the current drainage system versus an optimized system where all AI desilting recommendations are fully executed.
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', borderBottom: '1px solid var(--border)' }}>
                  <span>Overflowing Drains</span>
                  <div style={{ fontWeight: '700', display: 'flex', gap: '16px' }}>
                    <span style={{ color: 'var(--risk-red)' }}>{data.summary.overflowing_drains_current} (Current)</span>
                    <span style={{ color: 'var(--risk-green)' }}>{data.summary.overflowing_drains_optimized} (Desilted)</span>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', borderBottom: '1px solid var(--border)' }}>
                  <span>Flooded Roads</span>
                  <div style={{ fontWeight: '700', display: 'flex', gap: '16px' }}>
                    <span style={{ color: 'var(--risk-red)' }}>{data.summary.affected_roads_current}</span>
                    <span style={{ color: 'var(--risk-green)' }}>{data.summary.affected_roads_optimized}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', borderBottom: '1px solid var(--border)' }}>
                  <span>Flooded Commercial Markets</span>
                  <div style={{ fontWeight: '700', display: 'flex', gap: '16px' }}>
                    <span style={{ color: 'var(--risk-red)' }}>{data.summary.affected_markets_current}</span>
                    <span style={{ color: 'var(--risk-green)' }}>{data.summary.affected_markets_optimized}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', borderBottom: '1px solid var(--border)' }}>
                  <span>Residential Areas Flooded</span>
                  <div style={{ fontWeight: '700', display: 'flex', gap: '16px' }}>
                    <span style={{ color: 'var(--risk-red)' }}>{data.summary.residential_impact_current}</span>
                    <span style={{ color: 'var(--risk-green)' }}>{data.summary.residential_impact_optimized}</span>
                  </div>
                </div>
              </div>

              <div 
                style={{ 
                  marginTop: '20px', 
                  backgroundColor: 'var(--primary-container)', 
                  color: 'var(--primary)', 
                  borderRadius: 'var(--radius-sm)', 
                  padding: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  fontWeight: '600'
                }}
              >
                <TrendingDown size={24} />
                <span>
                  By executing AI recommendations, we can prevent overflows in <strong>{data.summary.overflowing_drains_current - data.summary.overflowing_drains_optimized} drainage channels</strong> and safeguard <strong>{data.summary.affected_roads_current - data.summary.affected_roads_optimized} arterial roadways</strong>.
                </span>
              </div>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Flooding Impact footprint</h3>
              <div style={{ width: '100%', height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={12} />
                    <YAxis stroke="var(--text-secondary)" fontSize={12} />
                    <Tooltip cursor={{ fill: 'var(--surface-variant)' }} />
                    <Legend />
                    <Bar dataKey="Current" fill="#ff4b4b" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Optimized" fill="#4caf50" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Infrastructure Risk & Protection Log</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Lists schools, hospitals, residential societies, and major roads located inside a 400-meter radius of overflowing drains, displaying their protection status.
            </p>

            <div className="table-container" style={{ maxHeight: '350px', overflowY: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Asset Name</th>
                    <th>Type</th>
                    <th>Distance to Drain</th>
                    <th>Current Status</th>
                    <th>Optimized Status</th>
                    <th>Protection Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.affected_infrastructure.length > 0 ? (
                    data.affected_infrastructure.map((infra, idx) => (
                      <tr key={idx}>
                        <td><strong>{infra.name}</strong></td>
                        <td>{infra.type}</td>
                        <td>{infra.distance_to_drain_m}m</td>
                        <td>
                          <span className={`badge ${infra.current_status === 'Flooded' ? 'badge-red' : 'badge-green'}`}>
                            {infra.current_status}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${infra.optimized_status === 'Flooded' ? 'badge-red' : 'badge-green'}`}>
                            {infra.optimized_status}
                          </span>
                        </td>
                        <td>
                          {infra.current_status === 'Flooded' && infra.optimized_status === 'Safe' ? (
                            <span style={{ color: 'var(--risk-green)', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <ShieldCheck size={16} /> Safeguarded
                            </span>
                          ) : infra.current_status === 'Safe' ? (
                            <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <Check size={16} /> Already Safe
                            </span>
                          ) : (
                            <span style={{ color: 'var(--risk-red)', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <AlertTriangle size={16} /> Flooding Unavoidable
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-secondary)' }}>
                        No infrastructure assets at risk in this rain scenario.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
