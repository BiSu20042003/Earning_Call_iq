import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { motion } from 'framer-motion' // animation library
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@radix-ui/react-tabs'
import { AlertTriangle, MessageSquare, TrendingUp, Eye, Loader2, Info, Lock } from 'lucide-react' //Icon library
import { getAnalysis } from '../services/api'

import RiskGauge from './RiskGuage'
import SentimentChart from './SentimentChart'
import { EvasionCard, GuidanceTabAction } from './EvasionCard'
import ChatPanel from './ChatPanel'

const TABS = [
  { value: 'evasion', label: 'Evasion Details', icon: Eye },
  { value: 'guidance', label: 'Guidance', icon: TrendingUp },
  { value: 'chat', label: 'Ask Anything', icon: MessageSquare }
]

export default function Analysis() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchData() {
      try{
        const result = await getAnalysis(id)
        setData(result)
      }
      catch{
        setError('Failed to load analysis')
      }
      finally{
        setLoading(false)
      }
    }
    fetchData();
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-80px)] w-full bg-[#060814]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 size={36} className="animate-spin text-indigo-400" />
          <p className="text-gray-400 text-sm">Loading analysis dashboard...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-80px)] w-full bg-[#060814]">
        <div className="flex flex-col items-center gap-3 text-red-400">
          <AlertTriangle size={36} />
          <p className="text-sm font-medium">{error || 'Analysis not found'}</p>
        </div>
      </div>
    )
  }

  const evasion = data.evasion || {}
  const evasionRate = Math.round((evasion.evasion_rate || 0) * 100)

  return (
    <div className="w-full bg-[#060814] min-h-screen text-gray-200 flex justify-center">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">

        {/* Top Cards Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">

          {/* 1. Overall Risk Card */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-[#090c21] border border-white/5 rounded-2xl p-6 md:p-7 flex flex-col shadow-xl relative"
          >
            <div className="flex items-center gap-1.5 text-gray-300 text-sm font-semibold mb-4">
              <span>Overall Risk</span>
              <Info size={14} className="text-gray-500 cursor-pointer" />
            </div>
            <RiskGauge score={data.risk_score || 0} />
          </motion.div>

          {/* 2. Sentiment Distribution Card */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 }}
            className="bg-[#090c21] border border-white/5 rounded-2xl p-6 md:p-7 flex flex-col shadow-xl relative"
          >
            <div className="flex items-center gap-1.5 text-gray-300 text-sm font-semibold mb-4">
              <span>Sentiment Distribution</span>
              <Info size={14} className="text-gray-500 cursor-pointer" />
            </div>
            <SentimentChart data={data.sentiment || {}} />
          </motion.div>

          {/* 3. Evasion Summary Card */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.16 }}
            className="bg-[#090c21] border border-white/5 rounded-2xl p-6 md:p-7 flex flex-col shadow-xl relative overflow-hidden min-h-[340px]"
          >
            <div className="relative z-10 flex-1">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-1.5 text-gray-300 text-sm font-semibold">
                  <span>Evasion Summary</span>
                  <Info size={14} className="text-gray-500 cursor-pointer" />
                </div>
                <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0">
                  <AlertTriangle size={18} />
                </div>
              </div>

              <p className="text-4xl font-extrabold text-amber-400 tracking-tight">
                {evasionRate}%
              </p>
              <p className="text-gray-400 text-xs mt-1 mb-6 font-medium">Evasion Rate</p>

              <div className="bg-[#101433]/80 border border-indigo-500/10 rounded-xl px-4 py-3">
                <p className="text-xs text-indigo-200 leading-relaxed">
                  <span className="text-indigo-400 font-bold">{evasion.evasion_count || 0}</span> evasive answers detected out of <span className="text-white font-bold">{evasion.total_qa_pairs || 0} Q&A</span> pairs
                </p>
              </div>
            </div>

            <div className="absolute bottom-0 left-0 right-0 h-24 overflow-hidden pointer-events-none">
              <svg viewBox="0 0 500 120" preserveAspectRatio="none" className="w-full h-full">
                <defs>
                  <linearGradient id="waveFill" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
                  </linearGradient>
                  <linearGradient id="waveStroke" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.2" />
                    <stop offset="50%" stopColor="#fbbf24" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.6" />
                  </linearGradient>
                </defs>

                <path
                  d="M0,80 Q125,120 250,60 T500,40 L500,120 L0,120 Z"
                  fill="url(#waveFill)"
                  stroke="none"
                />

                <path
                  d="M0,80 Q125,120 250,60 T500,40"
                  fill="none"
                  stroke="url(#waveStroke)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />

                <circle cx="120" cy="98" r="3" fill="#fbbf24" opacity="0.7">
                  <animate attributeName="opacity" values="0.2;0.9;0.2" dur="2.2s" repeatCount="indefinite" />
                </circle>
                <circle cx="250" cy="60" r="3.5" fill="#fbbf24">
                  <animate attributeName="opacity" values="0.9;0.2;0.9" dur="1.8s" repeatCount="indefinite" />
                </circle>
                <circle cx="410" cy="45" r="4" fill="#fbbf24">
                  <animate attributeName="opacity" values="0.3;1;0.3" dur="2.5s" repeatCount="indefinite" />
                  <animate attributeName="r" values="3;5;3" dur="2.5s" repeatCount="indefinite" />
                </circle>
                <circle cx="410" cy="45" r="8" fill="#f59e0b" opacity="0.3">
                  <animate attributeName="r" values="6;12;6" dur="2.5s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.4;0;0.4" dur="2.5s" repeatCount="indefinite" />
                </circle>
              </svg>
            </div>
          </motion.div>

        </div>

        {/* Bottom Tabs Panel */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.24 }}
          className="bg-[#090c21] border border-white/5 rounded-2xl p-6 md:p-8 shadow-xl"
        >
          <Tabs defaultValue="evasion">
            <TabsList className="flex gap-6 border-b border-white/10 mb-6">
              {TABS.map(({ value, label, icon: Icon }) => (
                <TabsTrigger
                  key={value}
                  value={value}
                  className="flex items-center gap-2 pb-3.5 text-sm font-medium text-gray-400 data-[state=active]:text-purple-400 data-[state=active]:border-b-2 data-[state=active]:border-purple-500 transition-all outline-none cursor-pointer"
                >
                  <Icon size={16} />
                  <span>{label}</span>
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value="evasion" className="outline-none">
              <EvasionCard evasion={evasion} />
            </TabsContent>

            <TabsContent value="guidance" className="outline-none">
              <GuidanceTabAction docId={id} />
            </TabsContent>

            <TabsContent value="chat" className="outline-none">
              <ChatPanel docId={id} />
            </TabsContent>
          </Tabs>
        </motion.div>

        {/* Security Footer Note */}
        <div className="flex items-center justify-center gap-1.5 text-gray-500 text-xs pt-2">
          <Lock size={12} />
          <span>Your data is <span className="text-indigo-400 font-medium">encrypted</span> and secure. We never share your transcripts.</span>
        </div>

      </div>
    </div>
  )
}
