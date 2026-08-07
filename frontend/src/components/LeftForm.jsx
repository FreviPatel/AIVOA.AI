import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { commitComplaintToQms } from '../redux/complaintSlice';
import {
  Building2,
  Package,
  Factory,
  AlertTriangle,
  ClipboardCheck,
  FileSearch,
  CheckCircle2,
  Save,
  Loader2,
} from 'lucide-react';

export default function LeftForm() {
  const dispatch = useDispatch();
  const {
    complaintData,
    complaintId,
    hasUnsavedChanges,
    isCommitting,
    commitSuccessMessage,
  } = useSelector((state) => state.complaint);

  if (!complaintData) {
    return (
      <div className="left-pane">
        <div className="empty-form-placeholder">
          <div className="placeholder-icon-box">
            <FileSearch size={32} />
          </div>
          <div className="placeholder-title">Awaiting AI Extraction</div>
          <div className="placeholder-desc">
            Upload a complaint PDF/TXT document or paste raw complaint text into the AI Copilot on the right to automatically extract and populate the QMS form.
          </div>
        </div>
      </div>
    );
  }

  const handleCommit = () => {
    if (complaintId && hasUnsavedChanges && !isCommitting) {
      dispatch(commitComplaintToQms(complaintId));
    }
  };

  const isCommitted =
    (complaintData.status || '').toLowerCase().includes('commit') ||
    (!hasUnsavedChanges && Boolean(commitSuccessMessage));

  const getSeverityBadgeClass = (severity) => {
    const s = (severity || '').toLowerCase();
    if (s === 'critical') return 'badge-severity-critical';
    if (s === 'major') return 'badge-severity-major';
    return 'badge-severity-minor';
  };

  return (
    <div className="left-pane">
      {/* Form Header */}
      <div className="form-header-bar">
        <div className="complaint-title-group">
          <h1>Customer Complaint Form</h1>
          <div className="complaint-id-badge">
            QMS Record ID: #{complaintId || complaintData.id || 'N/A'}
          </div>
        </div>
        <div className="badge-group">
          <span
            className={`badge ${
              isCommitted ? 'badge-status-committed' : 'badge-status-pending'
            }`}
          >
            {isCommitted ? 'Committed to QMS' : complaintData.status || 'Pending Triage'}
          </span>
          <span className={`badge ${getSeverityBadgeClass(complaintData.severity)}`}>
            {complaintData.severity || 'Major'}
          </span>
        </div>
      </div>

      {/* Section 1: Origin & Customer Details */}
      <div className="qms-section">
        <div className="section-header">
          <Building2 size={18} color="#2563EB" />
          <span>1. Origin & Customer Details</span>
        </div>
        <div className="form-grid">
          <div className="form-field">
            <label>Complaint Source</label>
            <input
              type="text"
              readOnly
              value={complaintData.complaint_source || ''}
              placeholder="e.g. Web Portal, Email"
            />
          </div>
          <div className="form-field">
            <label>Customer / Hospital Name</label>
            <input
              type="text"
              readOnly
              value={complaintData.customer_name || ''}
              placeholder="e.g. St. Jude Hospital"
            />
          </div>
        </div>
      </div>

      {/* Section 2: Product & Batch Identification */}
      <div className="qms-section">
        <div className="section-header">
          <Package size={18} color="#2563EB" />
          <span>2. Product & Batch Identification</span>
        </div>
        <div className="form-grid">
          <div className="form-field">
            <label>Product Name</label>
            <input
              type="text"
              readOnly
              value={complaintData.product_name || ''}
              placeholder="e.g. Paracetamol"
            />
          </div>
          <div className="form-field">
            <label>Product Strength</label>
            <input
              type="text"
              readOnly
              value={complaintData.product_strength || ''}
              placeholder="e.g. 500mg"
            />
          </div>
          <div className="form-field">
            <label>Batch / Lot Number</label>
            <input
              type="text"
              readOnly
              value={complaintData.batch_number || ''}
              placeholder="e.g. BATCH-998822"
            />
          </div>
          <div className="form-field">
            <label>Affected Quantity</label>
            <input
              type="text"
              readOnly
              value={complaintData.affected_quantity || ''}
              placeholder="e.g. 50 bottles"
            />
          </div>
          <div className="form-field">
            <label>Manufacturing Date</label>
            <input
              type="text"
              readOnly
              value={complaintData.manufacturing_date || ''}
              placeholder="YYYY-MM-DD"
            />
          </div>
          <div className="form-field">
            <label>Expiry Date</label>
            <input
              type="text"
              readOnly
              value={complaintData.expiry_date || ''}
              placeholder="YYYY-MM-DD"
            />
          </div>
        </div>
      </div>

      {/* Section 3: Manufacturing Site & Impacted Materials */}
      <div className="qms-section">
        <div className="section-header">
          <Factory size={18} color="#2563EB" />
          <span>3. Manufacturing Site & Impacted Materials</span>
        </div>
        <div className="form-grid">
          <div className="form-field">
            <label>Originating Site / Block</label>
            <input
              type="text"
              readOnly
              value={complaintData.originating_site_block || ''}
              placeholder="e.g. Block B - Packaging Unit 3"
            />
          </div>
          <div className="form-field">
            <label>Impacted Non-Product Materials</label>
            <input
              type="text"
              readOnly
              value={complaintData.impacted_non_product_materials || ''}
              placeholder="e.g. Cartons, Cap Seals"
            />
          </div>
        </div>
      </div>

      {/* Section 4: Complaint Classification & Description */}
      <div className="qms-section">
        <div className="section-header">
          <AlertTriangle size={18} color="#2563EB" />
          <span>4. Complaint Classification & Description</span>
        </div>
        <div className="form-grid">
          <div className="form-field">
            <label>Complaint Category</label>
            <input
              type="text"
              readOnly
              value={complaintData.complaint_category || ''}
              placeholder="e.g. Packaging Defect"
            />
          </div>
          <div className="form-field">
            <label>Severity Level</label>
            <input
              type="text"
              readOnly
              value={complaintData.severity || ''}
              placeholder="Minor, Major, Critical"
            />
          </div>
          <div className="form-field form-grid-full">
            <label>Detailed Complaint Description</label>
            <textarea
              readOnly
              value={complaintData.complaint_description || ''}
              placeholder="Full issue details..."
            />
          </div>
        </div>
      </div>

      {/* Section 5: QA Risk Assessment & Suggested Action */}
      <div className="qms-section">
        <div className="section-header">
          <ClipboardCheck size={18} color="#2563EB" />
          <span>5. QA Risk Assessment & Next Action</span>
        </div>
        <div className="form-grid">
          <div className="form-field form-grid-full">
            <label>Initial Risk Assessment</label>
            <textarea
              readOnly
              value={complaintData.initial_risk_assessment || ''}
              placeholder="Risk assessment details..."
            />
          </div>
          <div className="form-field form-grid-full">
            <label>Suggested Next Action</label>
            <textarea
              readOnly
              value={complaintData.suggested_next_action || ''}
              placeholder="Recommended QA action..."
            />
          </div>
        </div>
      </div>

      {/* Footer Action Bar */}
      <div className="form-footer-bar">
        <div>
          {!hasUnsavedChanges && commitSuccessMessage && (
            <div className="success-alert">
              <CheckCircle2 size={18} color="#059669" />
              <span>{commitSuccessMessage}</span>
            </div>
          )}
          {hasUnsavedChanges && (
            <span style={{ fontSize: '0.85rem', color: '#D97706', fontWeight: 500 }}>
              Unsaved AI changes pending commit
            </span>
          )}
        </div>
        <button
          className="commit-button"
          onClick={handleCommit}
          disabled={!hasUnsavedChanges || isCommitting}
          style={
            !hasUnsavedChanges && !isCommitting
              ? {
                  backgroundColor: '#D1D5DB',
                  color: '#9CA3AF',
                  cursor: 'not-allowed',
                  boxShadow: 'none',
                }
              : {}
          }
        >
          {isCommitting ? (
            <>
              <Loader2 size={18} className="spin-loader" />
              <span>Committing...</span>
            </>
          ) : !hasUnsavedChanges ? (
            <>
              <CheckCircle2 size={18} />
              <span>All Changes Committed</span>
            </>
          ) : (
            <>
              <Save size={18} />
              <span>Save Complaint</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
