import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, ChevronDown, ChevronUp, TrendingUp, ArrowRight } from 'lucide-react'

export function EvasionCard({ evasion }) {
  const [expandedIndex, setExpandedIndex] = useState(null)

  const toggleExpanded = (i) => {
    setExpandedIndex(expandedIndex === i ? null : i)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between mb-3 pb-4 border-b border-white/5">
        <div>
          <p className="text-3xl font-extrabold text-white">
            {Math.round((evasion.evasion_rate || 0) * 100)}%
          </p>
          <p className="text-gray-400 text-xs font-medium mt-0.5">Evasion Rate</p>
        </div>
        <p className="text-sm font-medium text-gray-300">
          <span className="text-white font-bold">{evasion.evasion_count || 0}</span>
          <span className="text-gray-500"> of {evasion.total_qa_pairs || 0} Q&A pairs</span>
        </p>
      </div>

      <div className="space-y-3">
        {evasion.flagged_pairs?.map((pair, i) => (
          <div
            key={i}
            className="bg-[#0b0e24] hover:bg-[#0f1330] rounded-xl border border-white/5 transition-all overflow-hidden"
          >
            <button
              onClick={() => toggleExpanded(i)}
              className="w-full flex items-center justify-between px-4 py-4 text-left gap-4 cursor-pointer"
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <span className="w-6 h-6 rounded-md bg-indigo-950/70 text-indigo-300 border border-indigo-500/20 text-xs font-semibold flex items-center justify-center shrink-0">
                  {i + 1}
                </span>
                <Eye size={15} className="text-amber-400 shrink-0" />
                <span className="text-sm text-gray-300 truncate">
                  {pair.question}
                </span>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full font-medium whitespace-nowrap">
                  {Math.round(pair.confidence * 100)} % confident
                </span>
                {expandedIndex === i
                  ? <ChevronUp size={15} className="text-gray-400" />
                  : <ChevronDown size={15} className="text-gray-400" />}
              </div>
            </button>

            {expandedIndex === i && (
              <div className="px-5 pb-5 pt-4 border-t border-white/5 space-y-4 bg-[#07091a]/50">
                <div>
                  <p className="text-[10px] tracking-wider font-semibold text-indigo-400 mb-1.5 uppercase">Analyst Question</p>
                  <p className="text-sm text-gray-200 leading-relaxed">{pair.question}</p>
                </div>
                <div>
                  <p className="text-[10px] tracking-wider font-semibold text-amber-400 mb-1.5 uppercase">Executive Answer</p>
                  <p className="text-sm text-gray-300 leading-relaxed">{pair.answer}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// Guidance tab doesn't render data inline anymore, it just links to the dedicated guidance page
export function GuidanceTabAction({ docId }) {
  const navigate = useNavigate()

  return (
    <div className="bg-[#0b0e24] border border-white/10 rounded-2xl p-8 text-center space-y-4 my-2">
      <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
        <TrendingUp size={24} />
      </div>
      <div className="space-y-1">
        <h3 className="text-lg font-bold text-green">Full Executive Guidance Report</h3>
      </div>
      <button
        onClick={() => navigate(`/guidance/${docId}`)}
        className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-5 py-3 rounded-xl transition-all cursor-pointer shadow-lg hover:shadow-indigo-500/20"
      >
        <span>View Full Guidance Page</span>
        <ArrowRight size={15} />
      </button>
    </div>
  )
}