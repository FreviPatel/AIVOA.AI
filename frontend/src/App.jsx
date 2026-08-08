import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import LeftForm from './components/LeftForm';
import RightCopilot from './components/RightCopilot';
import { ShieldCheck, RotateCcw } from 'lucide-react';
import { restoreState, resetState } from './redux/complaintSlice';
import './App.css';

function App() {
  const dispatch = useDispatch();
  const { complaintId, hasUnsavedChanges } = useSelector(
    (state) => state.complaint
  );

  // Hook 1: Restore state from localStorage on initial mount
  useEffect(() => {
    const savedState = localStorage.getItem('qms_state');
    if (savedState) {
      try {
        const parsedState = JSON.parse(savedState);
        if (parsedState && (parsedState.complaintData || parsedState.complaintId)) {
          dispatch(restoreState(parsedState));
        }
      } catch (err) {
        console.error('Failed to parse qms_state from localStorage:', err);
      }
    }
  }, [dispatch]);

  // Hook 2: Prevent accidental tab closure / refresh when there are unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [hasUnsavedChanges]);

  return (
    <div className="app-root">
      {/* App Header Navigation */}
      <header className="app-header">
        <div className="brand-container">
          <div className="brand-logo">
            <ShieldCheck size={20} />
          </div>
          <div>
            <div className="brand-title">AIVOA QMS Complaint Manager</div>
            <div className="brand-subtitle">
              AI-Powered Quality Management & Complaint Triaging
            </div>
          </div>
        </div>

        {complaintId && (
          <button
            onClick={() => dispatch(resetState())}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: '#F3F4F6',
              border: '1px solid #D1D5DB',
              color: '#374151',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            title="Start New Complaint Extraction"
          >
            <RotateCcw size={14} />
            <span>New Complaint</span>
          </button>
        )}
      </header>

      {/* Split-Screen Main Workspace (60% / 40%) */}
      <main className="app-layout">
        <LeftForm />
        <RightCopilot />
      </main>
    </div>
  );
}

export default App;
