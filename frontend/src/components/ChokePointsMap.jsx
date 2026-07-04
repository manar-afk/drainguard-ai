import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { ShieldAlert, Crosshair, HelpCircle, Hammer } from 'lucide-react';

export default function ChokePointsMap() {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDrain, setSelectedDrain] = useState(null);
  const [cleaningId, setCleaningId] = useState(null);
  const layersRef = useRef([]);

  const fetchData = () => {
    fetch('/api/chokepoints')
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading map data:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (loading || !data || !mapRef.current) return;

    if (!mapInstanceRef.current) {
      mapInstanceRef.current = L.map(mapRef.current).setView([19.0760, 72.8777], 13.5);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(mapInstanceRef.current);
    }

    const map = mapInstanceRef.current;

    layersRef.current.forEach(layer => map.removeLayer(layer));
    layersRef.current = [];

    data.wards.forEach(ward => {
      const color = ward.color === 'red' ? '#ff4b4b' : ward.color === 'orange' ? '#ff9800' : ward.color === 'yellow' ? '#ffeb3b' : '#4caf50';
      const wardCircle = L.circle([ward.lat, ward.lng], {
        color: color,
        fillColor: color,
        fillOpacity: 0.1,
        radius: 1200,
        weight: 1
      }).addTo(map);
      
      wardCircle.bindTooltip(`<strong>${ward.name}</strong><br>Risk index: ${ward.risk_index}%`, {
        permanent: false,
        direction: 'center'
      });
      layersRef.current.push(wardCircle);
    });

    data.drains.forEach(drain => {
      const color = drain.severity_color === 'red' ? '#ff4b4b' : drain.severity_color === 'orange' ? '#ff9800' : drain.severity_color === 'yellow' ? '#ffeb3b' : '#4caf50';
      const size = Math.max(8, Math.min(22, drain.capacity * 2.2));
      
      const marker = L.circleMarker([drain.latitude, drain.longitude], {
        radius: size,
        fillColor: color,
        color: '#ffffff',
        weight: 1.5,
        opacity: 1,
        fillOpacity: 0.85
      }).addTo(map);

      const popupContent = document.createElement('div');
      popupContent.style.minWidth = '200px';
      popupContent.innerHTML = `
        <h4 style="margin:0 0 8px;font-family:Outfit;font-weight:700;">${drain.name} (${drain.id})</h4>
        <p style="margin:0 0 4px;font-size:12px;"><strong>Zone:</strong> ${drain.ward}</p>
        <p style="margin:0 0 4px;font-size:12px;"><strong>Silt condition:</strong> ${drain.condition}%</p>
        <p style="margin:0 0 4px;font-size:12px;"><strong>Capacity:</strong> ${drain.capacity} m³/s</p>
        <p style="margin:0 0 12px;font-size:12px;"><strong>Flood Probability:</strong> ${(drain.overflow_probability * 100).toFixed(0)}%</p>
        <div style="display:flex;justify-content:flex-end;">
          <button id="btn-clean-${drain.id}" class="btn btn-primary" style="padding:6px 12px;font-size:11px;display:flex;align-items:center;gap:4px;">
             Clean Segment
          </button>
        </div>
      `;

      marker.bindPopup(popupContent);

      marker.on('popupopen', () => {
        const btn = document.getElementById(`btn-clean-${drain.id}`);
        if (btn) {
          btn.onclick = () => {
            handleCleanFromMap(drain.id);
            map.closePopup();
          };
        }
      });

      marker.on('click', () => {
        setSelectedDrain(drain);
      });

      layersRef.current.push(marker);
    });

    data.infrastructure.forEach(infra => {
      const emoji = infra.type === 'School' ? '🏫' : infra.type === 'Hospital' ? '🏥' : infra.type === 'Market' ? '🛒' : infra.type === 'Residential Area' ? '🏠' : '🛣️';
      
      const customIcon = L.divIcon({
        html: `<div style="font-size: 20px; line-height: 20px; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">${emoji}</div>`,
        className: 'infra-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      const marker = L.marker([infra.latitude, infra.longitude], { icon: customIcon }).addTo(map);
      marker.bindPopup(`
        <h4 style="margin:0 0 4px;font-family:Outfit;">${infra.name}</h4>
        <p style="margin:0;font-size:12px;color:gray;"><strong>Type:</strong> ${infra.type}</p>
        <p style="margin:0;font-size:12px;color:gray;"><strong>Elevation:</strong> ${infra.elevation_m}m</p>
      `);
      layersRef.current.push(marker);
    });

  }, [loading, data]);

  const handleCleanFromMap = (drainId) => {
    setCleaningId(drainId);
    fetch(`/api/maintenance/clean/${drainId}`, {
      method: 'POST'
    })
    .then(res => res.json())
    .then(res => {
      setCleaningId(null);
      fetchData();
    })
    .catch(err => {
      console.error(err);
      setCleaningId(null);
    });
  };

  const focusOnDrain = (drain) => {
    setSelectedDrain(drain);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([drain.latitude, drain.longitude], 15.5);
      
      mapInstanceRef.current.eachLayer((layer) => {
        if (layer instanceof L.CircleMarker && !(layer instanceof L.Circle)) {
          const latlng = layer.getLatLng();
          if (Math.abs(latlng.lat - drain.latitude) < 0.0001 && Math.abs(latlng.lng - drain.longitude) < 0.0001) {
            layer.openPopup();
          }
        }
      });
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <p>Loading interactive GIS map layers...</p>
      </div>
    );
  }

  const topChokePoints = data ? [...data.drains]
    .sort((a, b) => a.condition - b.condition)
    .slice(0, 5) : [];

  return (
    <div className="map-card-layout">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div ref={mapRef} className="map-container"></div>
        <div className="card" style={{ padding: '12px 24px', display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-secondary)' }}>
          <div style={{ display: 'flex', gap: '16px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ff4b4b' }}></span> Critical Risk
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ff9800' }}></span> High Risk
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ffeb3b' }}></span> Medium Risk
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#4caf50' }}></span> Low Risk
            </span>
          </div>
          <div>
            <span>Icons: 🏫 School • 🏥 Hospital • 🛒 Market • 🏠 Residential</span>
          </div>
        </div>
      </div>

      <div className="map-sidebar">
        <div className="card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert size={18} className="text-primary" />
            Top Critical Chokes
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            These segments have the highest silting blockages in the city network.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {topChokePoints.map(drain => (
              <div 
                key={drain.id}
                className="choke-point-card"
                onClick={() => focusOnDrain(drain)}
                style={selectedDrain?.id === drain.id ? { borderColor: 'var(--primary)', backgroundColor: 'var(--primary-container)' } : {}}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <strong style={{ fontSize: '14px' }}>{drain.id} - {drain.name}</strong>
                  <span className={`badge ${
                    drain.severity_color === 'red' ? 'badge-red' : 'badge-orange'
                  }`} style={{ fontSize: '10px', padding: '2px 6px' }}>
                    {100 - drain.condition}% Silt
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {drain.ward} • Overflow Prob: {(drain.overflow_probability * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        </div>

        {selectedDrain && (
          <div className="card" style={{ padding: '16px' }}>
            <h4 style={{ fontWeight: '600', marginBottom: '8px' }}>Detailed Inspector</h4>
            <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span><strong>Name:</strong> {selectedDrain.name}</span>
              <span><strong>Capacity:</strong> {selectedDrain.capacity} m³/s</span>
              <span><strong>Elevation:</strong> {selectedDrain.elevation}m</span>
              <span><strong>Type:</strong> {selectedDrain.type}</span>
              <button 
                className="btn btn-primary" 
                style={{ marginTop: '10px', padding: '6px 12px', width: '100%', fontSize: '12px' }}
                onClick={() => handleCleanFromMap(selectedDrain.id)}
                disabled={cleaningId === selectedDrain.id}
              >
                <Hammer size={12} />
                {cleaningId === selectedDrain.id ? 'Cleaning...' : 'Simulate De-silting'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
