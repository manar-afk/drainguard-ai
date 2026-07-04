import React, { useState } from 'react';
import { Eye, Upload, AlertCircle, FileText, CheckCircle, Flame, Hammer } from 'lucide-react';

export default function VisionInspection() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const sampleTemplates = [
    {
      name: "Market Garbage Clog",
      filename: "garbage_blockage.jpg",
      desc: "Drain near market is completely clogged with plastic bags and boxes after yesterday's market day.",
      preview: "https://images.unsplash.com/photo-1611284446314-60a58ac0deb9?w=500&auto=format&fit=crop&q=60"
    },
    {
      name: "Silt Siltation",
      filename: "silt_mud.jpg",
      desc: "Heavy clay and construction silt accumulated at the bottom, restricting water flow.",
      preview: "https://images.unsplash.com/photo-1584824486509-112e4181ff6b?w=500&auto=format&fit=crop&q=60"
    },
    {
      name: "Broken Cover Slab",
      filename: "broken_cover.jpg",
      desc: "A major pedestrian concrete cover slab has cracked and collapsed into the drainage channel.",
      preview: "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=500&auto=format&fit=crop&q=60"
    }
  ];

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleSelectSample = (sample) => {
    setSelectedFile({ name: sample.filename, mock: true });
    setPreviewUrl(sample.preview);
    setDescription(sample.desc);
    setResult(null);
  };

  const handleInspect = () => {
    if (!selectedFile) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("description", description);

    if (selectedFile.mock) {
      formData.append("image", new File([""], selectedFile.name, { type: "image/jpeg" }));
    } else {
      formData.append("image", selectedFile);
    }

    fetch('/api/vision/inspect', {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      setResult(data);
      setLoading(false);
    })
    .catch(err => {
      console.error("Error inspecting drain:", err);
      setLoading(false);
    });
  };

  const getPriorityStars = (pri) => {
    return "★".repeat(pri) + "☆".repeat(5 - pri);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '24px' }}>
      <div className="card">
        <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Upload size={18} />
          Computer Vision Upload
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
          Upload a drainage photo taken by a field worker. Gemini Vision will analyze the image, detect blockages/defects, and calculate priority.
        </p>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Quick Test Templates
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {sampleTemplates.map((sample, i) => (
              <button 
                key={i} 
                className="btn btn-secondary" 
                style={{ fontSize: '12px', justifyContent: 'flex-start', padding: '8px 12px' }}
                onClick={() => handleSelectSample(sample)}
              >
                📁 {sample.name}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <input 
            type="file" 
            id="drain-image" 
            accept="image/*" 
            style={{ display: 'none' }} 
            onChange={handleFileChange}
          />
          <div 
            className="upload-dropzone" 
            onClick={() => document.getElementById('drain-image').click()}
          >
            <Eye size={24} style={{ color: 'var(--primary)' }} />
            <div>
              <strong>Choose a photo</strong> or drag it here
              <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>PNG, JPG, JPEG up to 10MB</p>
            </div>
          </div>
        </div>

        {previewUrl && (
          <div style={{ marginBottom: '20px', textAlign: 'center' }}>
            <img src={previewUrl} className="upload-preview" alt="Drain preview" />
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>
              Selected: {selectedFile.name}
            </p>
          </div>
        )}

        <div className="form-group">
          <label>Optional Field Worker Remarks</label>
          <textarea 
            className="form-control" 
            rows="3" 
            placeholder="e.g. Near highway intersection..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          ></textarea>
        </div>

        <button 
          className="btn btn-primary" 
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={handleInspect}
          disabled={loading || !selectedFile}
        >
          {loading ? 'AI analyzing image...' : 'Run Vision Inspection'}
        </button>
      </div>

      <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>AI Detection Results</h3>

        {loading && (
          <div style={{ display: 'flex', flexGrow: 1, flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <p>Gemini Vision is extracting features...</p>
          </div>
        )}

        {!loading && !result && (
          <div style={{ display: 'flex', flexGrow: 1, flexDirection: 'column', justifyContent: 'center', alignItems: 'center', color: 'var(--text-secondary)' }}>
            <Eye size={36} style={{ marginBottom: '12px' }} />
            <p>Upload a photo or click a template to inspect details.</p>
          </div>
        )}

        {!loading && result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
              <div style={{ 
                width: '70px', 
                height: '70px', 
                borderRadius: '50%', 
                border: '4px solid var(--primary)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                fontWeight: '800',
                fontSize: '20px'
              }}>
                {result.risk_score}
              </div>
              <div>
                <h4 style={{ fontSize: '18px', fontWeight: '700' }}>Inspection Risk Score</h4>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                  <span className={`badge ${
                    result.severity === 'Critical' || result.severity === 'High' ? 'badge-red' : 'badge-yellow'
                  }`}>
                    {result.severity} Severity
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Priority: <strong style={{ color: 'var(--primary)' }}>{getPriorityStars(result.cleaning_priority)}</strong>
                  </span>
                </div>
              </div>
            </div>

            <div>
              <h5 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Detected Drainage Obstacles
              </h5>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {result.detected_issues.map((issue, idx) => (
                  <span key={idx} className="badge badge-red" style={{ fontSize: '11px' }}>
                    ⚠️ {issue}
                  </span>
                ))}
                {result.detected_issues.length === 0 && (
                  <span className="badge badge-green" style={{ fontSize: '11px' }}>
                    ✓ No Obstacles Detected
                  </span>
                )}
              </div>
            </div>

            <div style={{ borderLeft: '4px solid var(--primary)', paddingLeft: '16px', margin: '8px 0' }}>
              <h5 style={{ fontWeight: '700', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Hammer size={14} className="text-primary" />
                Action Directive
              </h5>
              <p style={{ fontSize: '14.5px', marginTop: '4px', fontStyle: 'italic' }}>
                "{result.suggested_action}"
              </p>
            </div>

            <div style={{ 
              border: '1px solid var(--border)', 
              borderRadius: 'var(--radius-sm)', 
              padding: '16px', 
              backgroundColor: 'var(--surface-variant)',
              fontSize: '13.5px',
              lineHeight: '1.6'
            }}>
              <h5 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '700', marginBottom: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                <FileText size={14} />
                Visual Evidence Breakdown
              </h5>
              <p>{result.explainable_reasoning}</p>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <CheckCircle size={14} style={{ color: 'var(--risk-green)' }} />
              <span>Inspection logged and forwarded to Sanitation Coordinator.</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
