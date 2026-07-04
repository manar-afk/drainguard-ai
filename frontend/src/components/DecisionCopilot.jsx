import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Sparkles, BookOpen, ChevronDown, ChevronUp } from 'lucide-react';

export default function DecisionCopilot() {
  const [messages, setMessages] = useState([
    {
      sender: 'agent',
      text: "Hello! I am the **DrainGuard AI Decision Copilot**.\n\nI have indexed our municipal weather forecasts, hydraulic simulation graphs, and desilting histories. Ask me queries like:\n- *'Which drains should be cleaned today?'*\n- *'Which ward is at highest flood risk?'*\n- *'Show top 10 choke points.'*\n\nHow can I assist you with urban water prevention today?",
      context: null
    }
  ]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [openContextIdx, setOpenContextIdx] = useState(null);

  const suggestions = [
    "Which drains should be cleaned today?",
    "Which ward is at highest flood risk?",
    "Show top 10 choke points.",
    "How much flooding can be prevented if Drain D05 is cleaned?",
    "Explain why Ward C is high risk."
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = (textToSend) => {
    const text = textToSend || query;
    if (!text.trim()) return;

    setMessages(prev => [...prev, { sender: 'user', text: text }]);
    setQuery('');
    setLoading(true);

    fetch('/api/copilot/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: text })
    })
    .then(res => res.json())
    .then(data => {
      setMessages(prev => [...prev, { 
        sender: 'agent', 
        text: data.answer, 
        context: data.context 
      }]);
      setLoading(false);
    })
    .catch(err => {
      console.error("Error talking to copilot:", err);
      setMessages(prev => [...prev, { 
        sender: 'agent', 
        text: "Error connecting to backend services. Make sure the FastAPI application is running.", 
        context: null 
      }]);
      setLoading(false);
    });
  };

  const renderMessageText = (text) => {
    let formatted = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    formatted = formatted.split('\n').map(line => {
      if (line.trim().startsWith('- ')) {
        return `<li>${line.trim().substring(2)}</li>`;
      }
      return line;
    }).join('\n');

    formatted = formatted.replace(/(<li>.*?<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`);

    if (formatted.includes('|')) {
      const lines = formatted.split('\n');
      let inTable = false;
      let tableHtml = '<table class="copilot-table">';
      
      lines.forEach(line => {
        if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
          if (line.includes('---')) {
            return;
          }
          const cells = line.split('|').map(c => c.trim()).filter((c, i, arr) => i > 0 && i < arr.length - 1);
          
          if (!inTable) {
            inTable = true;
            tableHtml += '<thead><tr>' + cells.map(c => `<th>${c}</th>`).join('') + '</tr></thead><tbody>';
          } else {
            tableHtml += '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>';
          }
        } else {
          if (inTable) {
            inTable = false;
            tableHtml += '</tbody></table>';
            formatted = formatted.replace(line, tableHtml + '\n' + line);
          }
        }
      });
    }

    formatted = formatted.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');

    return <div dangerouslySetInnerHTML={{ __html: formatted }} />;
  };

  const toggleContext = (idx) => {
    setOpenContextIdx(openContextIdx === idx ? null : idx);
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
            <div className={`message ${msg.sender === 'user' ? 'user' : 'agent'}`}>
              {renderMessageText(msg.text)}
            </div>

            {msg.sender === 'agent' && msg.context && (
              <div style={{ 
                alignSelf: 'flex-start', 
                width: '75%', 
                marginTop: '6px', 
                marginBottom: '12px',
                fontSize: '12px',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                overflow: 'hidden'
              }}>
                <div 
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center', 
                    padding: '8px 12px', 
                    backgroundColor: 'var(--surface-variant)', 
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                  onClick={() => toggleContext(idx)}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <BookOpen size={13} className="text-primary" />
                    Grounded RAG Sources ({msg.context.intent})
                  </span>
                  {openContextIdx === idx ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </div>

                {openContextIdx === idx && (
                  <div style={{ padding: '12px', backgroundColor: 'var(--surface)', borderTop: '1px solid var(--border)', fontFamily: 'monospace', fontSize: '11px', whiteSpace: 'pre-wrap', maxHeight: '180px', overflowY: 'auto' }}>
                    {msg.context.text_summary}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message agent" style={{ alignSelf: 'flex-start' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={16} className="animate-spin text-primary" />
              Retrieving context and formulating grounded answer...
            </span>
          </div>
        )}
        <div ref={scrollToBottom} />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', borderTop: '1px solid var(--border)', backgroundColor: 'var(--surface)', padding: '16px' }}>
        <div className="chat-suggestions" style={{ marginBottom: '12px' }}>
          {suggestions.map((suggestion, idx) => (
            <div 
              key={idx} 
              className="suggestion-chip"
              onClick={() => handleSend(suggestion)}
            >
              {suggestion}
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <input 
            type="text" 
            className="chat-input"
            placeholder="Query drain conditions, risk levels, desilting priorities..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button className="send-btn" onClick={() => handleSend()}>
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
