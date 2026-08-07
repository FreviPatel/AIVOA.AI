import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  sendInitialText,
  uploadDocument,
  sendChatEdit,
  fetchComplaint,
  commitComplaint,
} from '../services/api';

const saveToLocalStorage = (state) => {
  try {
    const toSave = {
      complaintData: state.complaintData,
      chatMessages: state.chatMessages,
      complaintId: state.complaintId,
      hasUnsavedChanges: state.hasUnsavedChanges,
    };
    localStorage.setItem('qms_state', JSON.stringify(toSave));
  } catch (err) {
    console.error('Error persisting state to localStorage:', err);
  }
};

export const submitInitialText = createAsyncThunk(
  'complaint/submitInitialText',
  async (text, { rejectWithValue }) => {
    try {
      const chatRes = await sendInitialText(text);
      const complaintId = chatRes.complaint_id;
      let complaintData = null;
      if (complaintId) {
        complaintData = await fetchComplaint(complaintId);
      }
      return {
        userMessage: text,
        aiMessage: chatRes.message,
        complaintId,
        complaintData,
      };
    } catch (err) {
      return rejectWithValue(
        err.response?.data?.detail || 'Failed to process complaint text'
      );
    }
  }
);

export const uploadFileDocument = createAsyncThunk(
  'complaint/uploadFileDocument',
  async (file, { rejectWithValue }) => {
    try {
      const res = await uploadDocument(file);
      return {
        userMessage: `Uploaded document: ${file.name}`,
        aiMessage: `I have parsed document '${file.name}' and created Complaint ID #${res.complaint_id}.`,
        complaintId: res.complaint_id,
        complaintData: res.complaint_data,
      };
    } catch (err) {
      return rejectWithValue(
        err.response?.data?.detail || 'Failed to upload and parse document'
      );
    }
  }
);

export const submitChatEdit = createAsyncThunk(
  'complaint/submitChatEdit',
  async ({ complaintId, text }, { rejectWithValue }) => {
    try {
      const chatRes = await sendChatEdit(complaintId, text);
      const updatedComplaintData = await fetchComplaint(complaintId);
      return {
        userMessage: text,
        aiMessage: chatRes.message,
        complaintId,
        complaintData: updatedComplaintData,
      };
    } catch (err) {
      return rejectWithValue(
        err.response?.data?.detail || 'Failed to process chat edit'
      );
    }
  }
);

export const commitComplaintToQms = createAsyncThunk(
  'complaint/commitComplaintToQms',
  async (complaintId, { rejectWithValue }) => {
    try {
      const updatedComplaintData = await commitComplaint(complaintId);
      return updatedComplaintData;
    } catch (err) {
      return rejectWithValue(
        err.response?.data?.detail || 'Failed to commit complaint to QMS'
      );
    }
  }
);

const initialState = {
  complaintData: null,
  chatMessages: [
    {
      sender: 'ai',
      message:
        "Hello! I am your AI QMS Assistant. Paste a raw complaint email, text report, or upload a document (PDF/TXT) to automatically extract and populate the QMS form.",
    },
  ],
  complaintId: null,
  hasUnsavedChanges: false,
  isLoading: false,
  isCommitting: false,
  commitSuccessMessage: null,
  error: null,
};

export const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    restoreState: (state, action) => {
      if (action.payload) {
        state.complaintData = action.payload.complaintData || null;
        state.chatMessages = action.payload.chatMessages || initialState.chatMessages;
        state.complaintId = action.payload.complaintId || null;
        state.hasUnsavedChanges = Boolean(action.payload.hasUnsavedChanges);
      }
    },
    resetState: (state) => {
      state.complaintData = null;
      state.chatMessages = [
        {
          sender: 'ai',
          message:
            "Hello! I am your AI QMS Assistant. Paste a raw complaint email, text report, or upload a document (PDF/TXT) to automatically extract and populate the QMS form.",
        },
      ];
      state.complaintId = null;
      state.hasUnsavedChanges = false;
      state.isLoading = false;
      state.isCommitting = false;
      state.commitSuccessMessage = null;
      state.error = null;
      try {
        localStorage.removeItem('qms_state');
      } catch (err) {
        console.error('Error clearing localStorage:', err);
      }
    },
    clearCommitMessage: (state) => {
      state.commitSuccessMessage = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // submitInitialText
      .addCase(submitInitialText.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(submitInitialText.fulfilled, (state, action) => {
        state.isLoading = false;
        state.complaintId = action.payload.complaintId;
        state.complaintData = action.payload.complaintData;
        state.hasUnsavedChanges = true;
        state.commitSuccessMessage = null;
        state.chatMessages.push({
          sender: 'user',
          message: action.payload.userMessage,
        });
        state.chatMessages.push({
          sender: 'ai',
          message: action.payload.aiMessage,
        });
        saveToLocalStorage(state);
      })
      .addCase(submitInitialText.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        state.chatMessages.push({
          sender: 'ai',
          message: `Error: ${action.payload}`,
        });
      })

      // uploadFileDocument
      .addCase(uploadFileDocument.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(uploadFileDocument.fulfilled, (state, action) => {
        state.isLoading = false;
        state.complaintId = action.payload.complaintId;
        state.complaintData = action.payload.complaintData;
        state.hasUnsavedChanges = true;
        state.commitSuccessMessage = null;
        state.chatMessages.push({
          sender: 'user',
          message: action.payload.userMessage,
        });
        state.chatMessages.push({
          sender: 'ai',
          message: action.payload.aiMessage,
        });
        saveToLocalStorage(state);
      })
      .addCase(uploadFileDocument.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        state.chatMessages.push({
          sender: 'ai',
          message: `Error uploading document: ${action.payload}`,
        });
      })

      // submitChatEdit
      .addCase(submitChatEdit.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(submitChatEdit.fulfilled, (state, action) => {
        state.isLoading = false;
        state.complaintId = action.payload.complaintId;
        state.complaintData = action.payload.complaintData;
        state.hasUnsavedChanges = true;
        state.commitSuccessMessage = null;
        state.chatMessages.push({
          sender: 'user',
          message: action.payload.userMessage,
        });
        state.chatMessages.push({
          sender: 'ai',
          message: action.payload.aiMessage,
        });
        saveToLocalStorage(state);
      })
      .addCase(submitChatEdit.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        state.chatMessages.push({
          sender: 'ai',
          message: `Error updating complaint: ${action.payload}`,
        });
      })

      // commitComplaintToQms
      .addCase(commitComplaintToQms.pending, (state) => {
        state.isCommitting = true;
      })
      .addCase(commitComplaintToQms.fulfilled, (state, action) => {
        state.isCommitting = false;
        state.complaintData = action.payload;
        state.hasUnsavedChanges = false;
        state.commitSuccessMessage = 'All changes committed.';
        saveToLocalStorage(state);
      })
      .addCase(commitComplaintToQms.rejected, (state, action) => {
        state.isCommitting = false;
        state.error = action.payload;
      });
  },
});

export const { restoreState, resetState, clearCommitMessage } = complaintSlice.actions;
export default complaintSlice.reducer;
