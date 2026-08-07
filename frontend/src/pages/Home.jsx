import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles, ShieldCheck, Brain, Shield, FileSpreadsheet, BarChart3, TrendingUp, Building2, Users } from 'lucide-react'
import { uploadTranscript, analyzeDocument } from '../services/api'

import UploadCard from './UploadCard'
import FeatureCard from './FeatureCard'

export default function Home() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('idle') // idle | uploading | analyzing | done | error
  const [error, setError] = useState(null)
  const [dragOver, setDragOver] = useState(false)

  const navigate = useNavigate()

  function handleFile(selectedFile) {
    if (!selectedFile) return
    if (!selectedFile.name.endsWith('.pdf') && !selectedFile.name.endsWith('.json')) {
      setError('Only PDF and JSON files are supported')
      return
    }
    setFile(selectedFile)
    setError(null)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }

  function handleDragOver(e) {
    e.preventDefault()
    setDragOver(true)
  }

  async function handleAnalyze() {
    if (!file) return
    setError(null)

    try {
      setStatus('uploading')
      const uploadResult = await uploadTranscript(file)
      const docId = uploadResult.id

      setStatus('analyzing')
      await analyzeDocument(docId)

      setStatus('done')
      setTimeout(() => navigate(`/analysis/${docId}`), 800)

    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.')
      setStatus('error')
    }
  }

  return (
    // Explicit top padding (pt-16) pushes the header text down.
    // gap-12 creates explicit breathing space between the card and lower elements.
    <div className="relative min-h-[calc(100vh-65px)] flex flex-col items-center justify-center pt-16 pb-12 px-4 gap-12 md:gap-16 bg-[#060814] overflow-x-hidden">

      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-pink-600/10 blur-[120px] pointer-events-none rounded-full" />

      {/* Hero Section Container */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-4xl flex flex-col items-center text-center"
      >
        {/* Header Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-purple-950/40 border border-purple-500/30 text-purple-300 text-xs font-semibold tracking-wider uppercase mb-5 shadow-sm shadow-purple-900/20">
          <Sparkles size={13} className="text-purple-400" />
          <span>AI Powered Insights</span>
        </div>

        {/* Title & Subtitle */}
        <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
          Earnings Call <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">Intelligence</span>
        </h1>
        <p className="text-gray-400 text-base md:text-lg max-w-2xl font-normal leading-relaxed mb-8">
          Transform earnings call transcripts into actionable insights with AI.<br className="hidden sm:inline" />
          Detect sentiment, uncover evasions, extract guidance, and more.
        </p>

        <UploadCard
          file={file}
          status={status}
          error={error}
          dragOver={dragOver}
          onFileSelect={handleFile}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={() => setDragOver(false)}
          onAnalyze={handleAnalyze}
        />
      </motion.div>

      {/* Feature Highlights Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="w-full max-w-5xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 px-2 z-10"
      >
        <FeatureCard
          icon={<Brain size={20} />}
          color="purple"
          title="AI-Powered Analysis"
          description="Advanced NLP models deliver deep insights in seconds."
        />
        <FeatureCard
          icon={<Shield size={20} />}
          color="emerald"
          title="Evasion Detection"
          description="Identify evasive language and potential red flags."
        />
        <FeatureCard
          icon={<FileSpreadsheet size={20} />}
          color="blue"
          title="Guidance Extraction"
          description="Extract forward-looking statements and guidance."
        />
        <FeatureCard
          icon={<BarChart3 size={20} />}
          color="amber"
          title="Actionable Insights"
          description="Get clear summaries and visuals for smarter decisions."
        />
      </motion.div>

      {/* Bottom Branding / Trust Footer */}
      <div className="pt-6 border-t border-white/5 w-full max-w-4xl text-center z-10">
        <p className="text-xs text-gray-500 tracking-wide font-medium mb-3">
          Trusted by analysts, investors, and professionals worldwide
        </p>
        <div className="flex items-center justify-center gap-8 text-gray-600">
          <ShieldCheck size={18} />
          <BarChart3 size={18} />
          <Building2 size={18} />
          <TrendingUp size={18} />
          <Users size={18} />
        </div>
      </div>

    </div>
  )
}