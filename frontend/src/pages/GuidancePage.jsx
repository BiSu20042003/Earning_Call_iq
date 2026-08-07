import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, Target, TrendingUp, ShieldCheck, 
  FileText, Download, Info, AlertCircle, Loader2
} from 'lucide-react'
import { getAnalysis } from '../services/api'

// Turns one raw claim item (string or object) into a clean row for the table
function parseClaim(item) {
  let parsed = item
  if (typeof item === 'string') {
    try {
      parsed = JSON.parse(item)
    } catch (e) {
      parsed = { raw_sentence: item }
    }
  }

  const metric = parsed.metric || ''
  const sentence = parsed.raw_sentence || parsed.claim || parsed.sentence || ''

  const periodParts = [parsed.target_period, parsed.target_year].filter(Boolean)
  const timeFrame = periodParts.length > 0 ? periodParts.join(' ') : (parsed.guidance_horizon || '')

  let guidance = ''
  if (parsed.raw_value) {
    guidance = parsed.raw_value
  } else if (parsed.value_low && parsed.value_high) {
    guidance = `${parsed.value_low}${parsed.value_unit || ''} – ${parsed.value_high}${parsed.value_unit || ''}`
  } else if (parsed.value) {
    guidance = parsed.value
  }

  return { metric, sentence, timeFrame, guidance, confidence: parsed.confidence }
}

export default function GuidancePage() {
  const { doc_id, id } = useParams()
  const documentId = doc_id || id
  const navigate = useNavigate()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!documentId) {
      setError('No Document ID provided in URL.')
      setLoading(false)
      return
    }

    setLoading(true)
    getAnalysis(documentId)
      .then((res) => {
        setData(res)
      })
      .catch((err) => {
        console.error('Error fetching guidance:', err)
        setError('Failed to load guidance analysis.')
      })
      .finally(() => setLoading(false))
  }, [documentId])

  if (loading) {
    return (
      <div className="w-full min-h-screen bg-[#070913] text-gray-300 flex flex-col items-center justify-center p-6">
        <Loader2 size={36} className="animate-spin text-indigo-500 mb-3" />
        <p className="text-sm font-medium">Loading Management Guidance...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full min-h-screen bg-[#070913] text-red-400 flex flex-col items-center justify-center p-6 gap-3">
        <AlertCircle size={40} />
        <p className="text-base font-semibold">{error}</p>
        <button 
          onClick={() => navigate(-1)}
          className="mt-2 text-xs text-indigo-400 hover:underline flex items-center gap-1 cursor-pointer"
        >
          <ArrowLeft size={14} /> Back to Dashboard
        </button>
      </div>
    )
  }

  // Parse claimed_sentences directly without assumptions
  const rawClaims = data?.claimed_sentences || data?.guidance || []
  const claims = rawClaims.map(parseClaim)

  // Aggregates computed purely from returned claims
  const totalItems = claims.length
  const uniqueMetrics = Array.from(new Set(claims.map(c => c.metric).filter(Boolean)))
  const focusAreas = uniqueMetrics.length > 0 ? uniqueMetrics.join(', ') : 'N/A'

  const validConfidences = claims.map(c => c.confidence).filter(val => typeof val === 'number')
  const avgConfidence = validConfidences.length > 0
    ? validConfidences.reduce((a, b) => a + b, 0) / validConfidences.length
    : null

  let confidenceLabel = 'N/A'
  if (avgConfidence !== null) {
    if (avgConfidence >= 0.8) confidenceLabel = 'High'
    else if (avgConfidence >= 0.5) confidenceLabel = 'Medium'
    else confidenceLabel = 'Low'
  }

  return (
    /* Outer wrapper centers everything and adds left/right margin on wide screens */
    <div className="w-full min-h-screen bg-[#070913] text-gray-200 flex justify-center">
      <div className="w-full max-w-6xl px-6 sm:px-10 py-8 space-y-8">
        
        {/* Header Section */}
        <div className="space-y-2 border-b border-white/10 pb-6">
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 text-xs font-semibold text-gray-400 hover:text-white transition-colors cursor-pointer mb-2"
          >
            <ArrowLeft size={14} /> Back to Dashboard
          </button>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Management Guidance
          </h1>
          <p className="text-sm text-gray-400">
            Key forward-looking statements and outlook provided by management.
          </p>
        </div>

        {/* 3 Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
          
          {/* Card 1: Total Guidance Items */}
          <div className="bg-[#0b0e20] border border-white/10 rounded-2xl p-6 flex items-center gap-5 shadow-xl w-full">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center shrink-0">
              <Target size={22} />
            </div>
            <div className="space-y-1">
              <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Total Guidance Items</p>
              <p className="text-2xl font-bold text-white">{totalItems}</p>
              <p className="text-xs text-gray-500">Across key financial metrics</p>
            </div>
          </div>

          {/* Card 2: Focus Areas */}
          <div className="bg-[#0b0e20] border border-white/10 rounded-2xl p-6 flex items-center gap-5 shadow-xl w-full">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
              <TrendingUp size={22} />
            </div>
            <div className="space-y-1 overflow-hidden">
              <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Focus Areas</p>
              <p className="text-sm font-semibold text-gray-200 truncate leading-relaxed">
                {focusAreas}
              </p>
            </div>
          </div>

          {/* Card 3: Confidence */}
          <div className="bg-[#0b0e20] border border-white/10 rounded-2xl p-6 flex items-center gap-5 shadow-xl w-full">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
              <ShieldCheck size={22} />
            </div>
            <div className="space-y-1">
              <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Confidence</p>
              <p className="text-2xl font-bold text-amber-400">{confidenceLabel}</p>
              <p className="text-xs text-gray-500">Based on quantitative guidance</p>
            </div>
          </div>

        </div>

        {/* Guidance Summary Table Card */}
        <div className="bg-[#0b0e20] border border-white/10 rounded-2xl overflow-hidden shadow-2xl w-full">
          
          {/* Table Top Title */}
          <div className="p-6 border-b border-white/10 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
              <FileText size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Guidance Summary</h2>
              <p className="text-xs text-gray-400">All metrics as reported by executive management.</p>
            </div>
          </div>

          {/* Table Wrapper */}
          <div className="w-full overflow-x-auto">
            <div className="min-w-[800px] w-full">
              
              {/* Header Row */}
              <div className="grid grid-cols-12 bg-[#080a18] border-b border-white/10 py-4 px-6 text-xs font-bold text-gray-400 uppercase tracking-wider">
                <div className="col-span-1 text-center">#</div>
                <div className="col-span-6">Guidance Claim (Management Reported)</div>
                <div className="col-span-2">Metric</div>
                <div className="col-span-1">Time Frame</div>
                <div className="col-span-2 text-right">Guidance</div>
              </div>

              {/* Rows List */}
            <div className="text-sm text-gray-300">
              {claims.length === 0 ? (
                <div className="p-12 text-center text-gray-500 font-medium">
                  No management guidance detected in this analysis.
                </div>
              ) : (
                claims.map((row, idx) => (
                  <div 
                    key={idx} 
                    className="grid grid-cols-12 items-center py-5 px-6 border-b border-white/5 last:border-b-0 hover:bg-white/[0.02] transition-colors"
                  >
                    {/* Index */}
                    <div className="col-span-1 text-center font-semibold text-gray-500">
                      {idx + 1}
                    </div>

                    {/* Claim Sentence */}
                    <div className="col-span-6 text-gray-200 leading-relaxed pr-4">
                      {row.sentence || '—'}
                    </div>

                    {/* Metric Badge */}
                    <div className="col-span-2">
                      {row.metric ? (
                        <span className="inline-block bg-blue-500/10 border border-blue-500/20 text-blue-400 font-bold px-3 py-1 rounded-md text-xs tracking-wide uppercase">
                          {row.metric}
                        </span>
                      ) : (
                        '—'
                      )}
                    </div>

                    {/* Time Frame */}
                    <div className="col-span-1 font-medium text-gray-300 whitespace-nowrap">
                      {row.timeFrame || '—'}
                    </div>

                    {/* Guidance Value */}
                    <div className="col-span-2 text-right font-semibold text-white whitespace-nowrap">
                      {row.guidance || '—'}
                    </div>
                  </div>
                ))
              )}
            </div>

            </div>
          </div>

          {/* Footer Bar */}
          <div className="p-5 bg-[#080a18] border-t border-white/10 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <Info size={16} className="text-blue-400 shrink-0" />
              <span>These guidance statements are forward-looking and subject to risks and uncertainties.</span>
            </div>
          </div>

        </div>

      </div>
    </div>
  )
}