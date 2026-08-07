import axios from 'axios'

const BASE_URL = 'http://localhost:8000/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 300000  // 5 min — analysis can take time
})

export const uploadTranscript = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const res = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export const analyzeDocument = async (docId) => {
  const res = await api.post(`/analyze/${docId}`)
  return res.data
}

export const chatWithDocument = async (docId, question) => {
  const res = await api.post('/chat', {
    document_id: docId,
    question:    question
  })
  return res.data
}

export const getChatHistory = async (docId) => {
  const res = await api.get(`/chat/history/${docId}`)
  return res.data
}

export const getHistory = async () => {
  const res = await api.get('/history')
  return res.data
}

export const getAnalysis = async (docId) => {
  const res = await api.get(`/analysis/${docId}`)
  return res.data
}

export const deleteAnalysis = async (docId) => {
  const res = await api.delete(`/analysis/${docId}`)
  return res.data
}