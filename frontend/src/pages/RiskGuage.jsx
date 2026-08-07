import React from 'react'
import { ShieldCheck, Info } from 'lucide-react'

function getRiskLevel(score) {
  if (score > 65)
    return { color: '#ef4444', label: 'HIGH RISK', badgeBg: 'bg-red-500/15 text-red-400 border-red-500/30' }

  if (score > 40)
    return { color: '#f59e0b', label: 'MEDIUM RISK', badgeBg: 'bg-amber-500/15 text-amber-400 border-amber-500/30' }

  return { color: '#10b981', label: 'LOW RISK', badgeBg: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' }
}

export default function RiskGauge({ score }) {
  const numericScore = typeof score === 'number' ? score : parseFloat(score) || 0
  const { color, label, badgeBg } = getRiskLevel(numericScore)

  const clampedScore = Math.min(Math.max(numericScore, 0), 100)
  const angle = (clampedScore / 100) * 180 - 90

  return (
    <div className="flex flex-col items-center justify-center h-full w-full pt-2">
      <div className="relative w-full max-w-[250px] aspect-[2/1] my-2 mx-auto flex justify-center overflow-hidden">
        <svg viewBox="0 0 200 110" className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="50%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>

          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#1a1e38"
            strokeWidth="16"
            strokeLinecap="round"
          />

          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="16"
            strokeLinecap="round"
          />

          <g transform={`rotate(${angle}, 100, 100)`}>
            <line x1="100" y1="100" x2="100" y2="28" stroke={color} strokeWidth="3.5" strokeLinecap="round" className="transition-all duration-500 ease-out" />
            <line x1="100" y1="100" x2="100" y2="32" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
            <circle cx="100" cy="100" r="7" fill="#090c21" stroke={color} strokeWidth="3" />
            <circle cx="100" cy="100" r="3" fill="#ffffff" />
          </g>

          <g transform={`rotate(${angle}, 100, 100)`}>
            <circle cx="100" cy="20" r="7" fill="#ffffff" className="shadow-md" />
            <circle cx="100" cy="20" r="4" fill={color} />
          </g>
        </svg>

        <div className="absolute bottom-0 text-center flex flex-col items-center w-full">
          <span className="text-4xl font-extrabold text-white tracking-tight">{numericScore.toFixed(2)}</span>

          <div className={`mt-2.5 px-3.5 py-1 rounded-full border text-[11px] font-bold tracking-wider uppercase ${badgeBg}`}>
            {label}
          </div>

          <span className="text-gray-500 text-[11px] mt-1.5 font-medium flex items-center gap-1">
            Risk Score <Info size={11} className="text-gray-600" />
          </span>
        </div>
      </div>

      <div className="w-full mt-6 bg-[#0e122b]/90 border border-white/5 rounded-xl px-4 py-3 flex items-center gap-3">
        <ShieldCheck className="text-emerald-400 shrink-0" size={17} />
        <span className="text-xs text-gray-300 font-normal">
          This transcript shows a low risk of evasive language.
        </span>
      </div>
    </div>
  )
}