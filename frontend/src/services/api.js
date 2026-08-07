import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendInitialText = async (text) => {
  const response = await api.post('/api/chat', {
    complaint_id: null,
    sender: 'user',
    message: text,
  });
  return response.data;
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/api/upload-complaint', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const sendChatEdit = async (complaintId, text) => {
  const response = await api.post('/api/chat', {
    complaint_id: complaintId,
    sender: 'user',
    message: text,
  });
  return response.data;
};

export const fetchComplaint = async (complaintId) => {
  const response = await api.get(`/api/complaints/${complaintId}`);
  return response.data;
};

export const commitComplaint = async (complaintId) => {
  const response = await api.put(`/api/complaints/${complaintId}`, {
    status: 'Committed to QMS',
  });
  return response.data;
};
