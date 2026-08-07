import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileText, Trash2, ChevronRight, Loader2, Clock } from 'lucide-react'
import { getHistory, deleteAnalysis } from '../services/api'

function getRiskColor(score) {
  if (score > 65) return 'text-red-400'
  if (score > 40) return 'text-yellow-400'
  return 'text-green-400'
}

export default function History() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getHistory()
      .then(setItems)
      .finally(() => setLoading(false))
  }, [])

  async function handleDelete(e, docId) {
    e.stopPropagation()
    await deleteAnalysis(docId)
    setItems(prev => prev.filter(i => i.document_id !== docId))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-73px)] w-full bg-[#060814]">
        <Loader2 size={32} className="animate-spin text-blue-400" />
      </div>
    )
  }

  if (!items.length) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-73px)] w-full bg-[#060814] text-center">
        <Clock className="text-gray-600 mb-3" size={48} />
        <p className="text-gray-400 text-lg">No analyses yet</p>
        <p className="text-gray-600 text-sm mt-1">Upload a transcript to get started</p>
      </div>
    )
  }

  return (
    <div className="w-full bg-[#060814] min-h-screen flex justify-center">
      <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="text-2xl font-bold text-white mb-6">Analysis History</h1>

        <div className="flex flex-col gap-4">
          {items.map((item, i) => (
            <motion.div
              key={item.document_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => navigate(`/analysis/${item.document_id}`)}
              className="bg-[#0d0d1a] border border-white/10 rounded-xl p-4 flex items-center justify-between cursor-pointer hover:border-blue-500/30 hover:bg-blue-500/5 transition-all"
            >
              <div className="flex items-center gap-4">
                <div className="bg-blue-500/10 p-3 rounded-lg">
                  <FileText className="text-blue-400" size={20} />
                </div>
                <div>
                  <p className="text-white font-medium">{item.filename}</p>
                  <p className="text-gray-500 text-sm">
                    {item.ticker && `${item.ticker} · `}
                    {item.quarter && `Q${item.quarter} ${item.year} · `}
                    {new Date(item.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                {item.risk_score !== null && item.risk_score !== undefined && (
                  <div className="text-center">
                    <p className={`text-xl font-bold ${getRiskColor(item.risk_score)}`}>
                      {item.risk_score}
                    </p>
                    <p className="text-gray-600 text-xs">risk</p>
                  </div>
                )}

                <button
                  onClick={(e) => handleDelete(e, item.document_id)}
                  className="text-gray-600 hover:text-red-400 p-2 rounded-lg hover:bg-red-400/10 transition-all"
                >
                  <Trash2 size={16} />
                </button>

                <ChevronRight className="text-gray-600" size={18} />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}