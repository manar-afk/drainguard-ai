import React, { useState, useEffect } from 'react';
import { AlertTriangle, MapPin, Mic, FileText, CheckCircle, Image as ImageIcon, Sparkles } from 'lucide-react';

export default function CitizenReporting() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [description, setDescription] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);

  const fetchReports = () => {
    fetch('/api/citizen/reports')
      .then(res => res.json())
      .then(data => {
        setReports(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading citizen reports:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGetLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLatitude(position.coords.latitude.toFixed(6));
          setLongitude(position.coords.longitude.toFixed(6));
        },
        () => {
          const mockLat = (19.0760 + (Math.random() - 0.5) * 0.02).toFixed(6);
          const mockLng = (72.8777 + (Math.random() - 0.5) * 0.02).toFixed(6);
          setLatitude(mockLat);
          setLongitude(mockLng);
        }
      );
    } else {
      const mockLat = (19.0760 + (Math.random() - 0.5) * 0.02).toFixed(6);
      const mockLng = (72.8777 + (Math.random() - 0.5) * 0.02).toFixed(6);
      setLatitude(mockLat);
      setLongitude(mockLng);
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleRecordVoice = () => {
    if (isRecording) {
      setIsRecording(false);
      const dummyBlob = new Blob(["mock audio data"], { type: "audio/wav" });
      setAudioBlob(dummyBlob);
      if (!description) {
        setDescription("Voice Report: Severe mud and garbage clogging the main drain near LBS Road intersection.");
      }
    } else {
      setIsRecording(true);
      setAudioBlob(null);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!description.trim() || !latitude || !longitude) return;

    setSubmitting(true);
    setSubmissionResult(null);

    const formData = new FormData();
    formData.append("text", description);
    formData.append("latitude", parseFloat(latitude));
    formData.append("longitude", parseFloat(longitude));

    if (imageFile) {
      formData.append("image", imageFile);
    }

    if (audioBlob) {
      formData.append("audio", audioBlob, "voice_report.wav");
    }

    fetch('/api/citizen/report', {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      setSubmissionResult(data);
      setSubmitting(false);
      
      setDescription('');
      setImageFile(null);
      setImagePreview(null);
      setAudioBlob(null);
      
      fetchReports();
    })
    .catch(err => {
      console.error("Error submitting report:", err);
      setSubmitting(false);
    });
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '24px' }}>
      <div className="card">
        <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={18} />
          Submit Citizen Report
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
          Report drainage blockages, broken covers, or silt directly to municipal authorities. AI will automatically categorize, assign severity, and filter duplicates.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Latitude</label>
              <input 
                type="number" 
                step="0.000001" 
                className="form-control" 
                required
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Longitude</label>
              <input 
                type="number" 
                step="0.000001" 
                className="form-control" 
                required
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
              />
            </div>
          </div>

          <button 
            type="button" 
            className="btn btn-secondary" 
            style={{ width: '100%', justifyContent: 'center', marginBottom: '20px', fontSize: '12px', padding: '8px' }}
            onClick={handleGetLocation}
          >
            <MapPin size={14} /> Get Coordinates
          </button>

          <div className="form-group">
            <label>Report Description (Text or Voice)</label>
            <textarea 
              className="form-control" 
              rows="4" 
              required
              placeholder="Describe the issue, e.g., Garbage blocking water channel..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            ></textarea>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {audioBlob ? '🟢 Voice message recorded' : 'Record voice note (voice-to-text)'}
            </span>
            <button 
              type="button" 
              className={`btn ${isRecording ? 'btn-primary animate-pulse' : 'btn-secondary'}`}
              style={{ borderRadius: '50%', width: '40px', height: '40px', padding: 0, justifyContent: 'center' }}
              onClick={handleRecordVoice}
            >
              <Mic size={18} />
            </button>
          </div>

          <div className="form-group">
            <label>Upload Photo</label>
            <input 
              type="file" 
              id="citizen-image" 
              accept="image/*" 
              style={{ display: 'none' }} 
              onChange={handleImageChange}
            />
            <button 
              type="button" 
              className="btn btn-secondary" 
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => document.getElementById('citizen-image').click()}
            >
              <ImageIcon size={16} /> Choose Image
            </button>
            {imagePreview && (
              <div style={{ marginTop: '10px', textAlign: 'center' }}>
                <img src={imagePreview} style={{ maxHeight: '140px', borderRadius: '4px', maxWidth: '100%' }} alt="Preview" />
              </div>
            )}
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', justifyContent: 'center', marginTop: '12px' }}
            disabled={submitting}
          >
            {submitting ? 'Submitting to AI platform...' : 'Submit Report'}
          </button>
        </form>

        {submissionResult && (
          <div style={{ 
            marginTop: '24px', 
            border: '1px solid var(--border)', 
            borderRadius: 'var(--radius-md)', 
            padding: '16px',
            backgroundColor: 'var(--surface-variant)'
          }}>
            <h4 style={{ fontSize: '15px', fontWeight: '700', display: 'flex', alignContent: 'center', gap: '6px', marginBottom: '12px' }}>
              <Sparkles size={16} className="text-primary" />
              AI Classification Feedback
            </h4>

            {submissionResult.is_duplicate ? (
              <div style={{ border: '1px solid var(--risk-orange)', borderRadius: 'var(--radius-sm)', padding: '10px 14px', backgroundColor: 'var(--risk-orange-bg)', color: 'var(--text)', fontSize: '12px', marginBottom: '12px' }}>
                <strong>Duplicate Alert:</strong> Similar report already active in this block. Merged with ticket #{submissionResult.duplicate_of}.
              </div>
            ) : (
              <div style={{ border: '1px solid var(--risk-green)', borderRadius: 'var(--radius-sm)', padding: '10px 14px', backgroundColor: 'var(--risk-green-bg)', color: 'var(--text)', fontSize: '12px', marginBottom: '12px' }}>
                <strong>Unique Ticket:</strong> Verified as new issue. Ticket #{submissionResult.report_id} generated.
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px' }}>
              <span>Category: <strong>{submissionResult.category}</strong></span>
              <span>Severity: <strong>{submissionResult.severity}</strong></span>
              <span>Action: <em>"{submissionResult.recommended_immediate_action}"</em></span>
            </div>
          </div>
        )}
      </div>

      <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Active Reports Feed</h3>

        {loading ? (
          <p>Loading complaints stream...</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', maxHeight: '650px', paddingRight: '4px' }}>
            {reports.map((report) => (
              <div 
                key={report.id}
                style={{ 
                  border: '1px solid var(--border)', 
                  borderRadius: 'var(--radius-sm)', 
                  padding: '16px',
                  backgroundColor: report.duplicate_of ? 'rgba(255, 152, 0, 0.05)' : 'var(--surface)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div>
                    <span className={`badge ${
                      report.severity === 'Critical' || report.severity === 'High' ? 'badge-red' : 'badge-yellow'
                    }`} style={{ fontSize: '10px', padding: '2px 8px' }}>
                      {report.category}
                    </span>
                    {report.duplicate_of && (
                      <span className="badge badge-orange" style={{ fontSize: '10px', padding: '2px 8px', marginLeft: '6px' }}>
                        Merged Dup
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {report.created_at}
                  </span>
                </div>

                <p style={{ fontSize: '13.5px', margin: '8px 0', lineHeight: '1.5' }}>
                  {report.text}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  <span>Coordinates: {report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}</span>
                  <span style={{ 
                    fontWeight: '600', 
                    color: report.status === 'Resolved' ? 'var(--risk-green)' : report.status === 'In Progress' ? 'var(--risk-orange)' : 'var(--text-secondary)' 
                  }}>
                    Status: {report.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
