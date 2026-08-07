import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  submitInitialText,
  uploadFileDocument,
  submitChatEdit,
} from '../redux/complaintSlice';
import {
  Sparkles,
  Paperclip,
  Send,
  User,
  Bot,
  Loader2,
} from 'lucide-react';

export default function RightCopilot() {
  const dispatch = useDispatch();
  const { chatMessages, complaintId, isLoading } = useSelector(
    (state) => state.complaint
  );

  const [inputMessage, setInputMessage] = useState('');
  const fileInputRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isLoading]);

  const handleSend = () => {
    const text = inputMessage.trim();
    if (!text || isLoading) return;

    if (!complaintId) {
      dispatch(submitInitialText(text));
    } else {
      dispatch(submitChatEdit({ complaintId, text }));
    }
    setInputMessage('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && !isLoading) {
      dispatch(uploadFileDocument(file));
      e.target.value = '';
    }
  };

  return (
    <div className="right-pane">
      {/* Top File Upload Header */}
      <div className="copilot-upload-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="#2563EB" />
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#111827' }}>
            AI QMS Copilot
          </span>
        </div>

        <input
          type="file"
          ref={fileInputRef}
          className="hidden-file-input"
          accept=".pdf,.txt,.eml"
          onChange={handleFileChange}
        />

        <button
          className="upload-button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
        >
          <Paperclip size={16} />
          <span>Upload Complaint (PDF/TXT)</span>
        </button>
      </div>

      {/* Middle Scrollable Chat Messages */}
      <div className="chat-messages-container">
        {chatMessages.map((msg, index) => (
          <div
            key={index}
            className={`chat-bubble-row ${msg.sender === 'user' ? 'user' : 'ai'}`}
          >
            <div className={`avatar ${msg.sender === 'user' ? 'user' : 'ai'}`}>
              {msg.sender === 'user' ? <User size={18} /> : <Bot size={18} />}
            </div>
            <div className="chat-bubble-content">{msg.message}</div>
          </div>
        ))}

        {isLoading && (
          <div className="chat-bubble-row ai">
            <div className="avatar ai">
              <Sparkles size={18} />
            </div>
            <div
              className="chat-bubble-content"
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <Loader2 size={16} className="spin-loader" />
              <span>Analyzing & extracting complaint details with AI...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Bottom Text Area Input Bar */}
      <div className="chat-input-bar">
        <textarea
          className="chat-textarea"
          rows={2}
          placeholder={
            complaintId
              ? "Enter your complaint details or edit instructions (e.g., 'Change batch number to BATCH-999')..."
              : "Enter your complaint details or paste text report here..."
          }
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />


        <button
          className="send-button"
          onClick={handleSend}
          disabled={isLoading || !inputMessage.trim()}
          title="Send message"
        >
          {isLoading ? (
            <Loader2 size={20} className="spin-loader" />
          ) : (
            <Send size={20} />
          )}
        </button>
      </div>
    </div>
  );
}
