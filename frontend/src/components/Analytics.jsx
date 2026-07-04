import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { BarChart3, TrendingUp, ShieldAlert, Sparkles } from 'lucide-react';

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/analytics')
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading analytics data:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <p>Structuring database matrices and charts...</p>
      </div>
    );
  }

  if (!data) return null;

  const COLORS = ['#4caf50', '#2196f3', '#ff9800', '#f44336'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={16} />
            Rainfall vs. Drain Overflow Rate
          </h3>
          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.rainfall_flood_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="rainfall_bin_mm" stroke="var(--text-secondary)" fontSize={11} tickFormatter={(v) => `${v}mm`} />
                <YAxis stroke="var(--text-secondary)" fontSize={11} unit="%" />
                <Tooltip />
                <Legend />
                <Bar dataKey="overflow_rate_pct" name="Overflow Probability" fill="var(--primary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert size={16} />
            Drain Network Condition Categories
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', alignItems: 'center', height: '280px' }}>
            <div style={{ width: '100%', height: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.drain_condition_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="count"
                    nameKey="status"
                  >
                    {data.drain_condition_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
              {data.drain_condition_distribution.map((entry, index) => (
                <div key={entry.status} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: COLORS[index] }}></span>
                  <span>{entry.status}: <strong>{entry.count}</strong></span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={16} />
            Citizen Complaint Topics Distribution
          </h3>
          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.citizen_complaint_categories} layout="vertical" margin={{ top: 10, right: 10, left: 30, bottom: 0 }}>
                <XAxis type="number" stroke="var(--text-secondary)" fontSize={11} />
                <YAxis dataKey="category" type="category" stroke="var(--text-secondary)" fontSize={10} width={120} />
                <Tooltip />
                <Bar dataKey="count" name="Unique Reports" fill="#ff9800" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} />
            Monsoon Rainfall Trend (7-Day Forecast)
          </h3>
          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.forecast} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="date" stroke="var(--text-secondary)" fontSize={11} tickFormatter={(d) => d.substring(5)} />
                <YAxis stroke="var(--text-secondary)" fontSize={11} unit="mm" />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="rainfall_mm" name="Rainfall" stroke="#2196f3" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      <div className="card" style={{ background: 'linear-gradient(90deg, rgba(76, 175, 80, 0.1), rgba(33, 150, 243, 0.1))', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px' }}>
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '4px' }}>Maintenance Performance Index</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Aggregates labor hours, sucking pumps, and desilting activities compared with post-maintenance sensor readings.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '32px' }}>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Avg Work Cost</span>
            <h4 style={{ fontSize: '24px', fontWeight: '800', color: 'var(--primary)' }}>${data.maintenance_metrics.average_cost_usd}</h4>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Avg Risk Reduction</span>
            <h4 style={{ fontSize: '24px', fontWeight: '800', color: 'var(--risk-green)' }}>-{data.maintenance_metrics.average_risk_reduction_pct}%</h4>
          </div>
        </div>
      </div>
    </div>
  );
}
