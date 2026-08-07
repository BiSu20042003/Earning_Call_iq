import React from 'react'

const COLOR_STYLES = {
  purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20'
}

export default function FeatureCard({ icon, color, title, description }) {
  return (
    <div className="p-4 rounded-2xl bg-[#090c21]/80 border border-white/5 backdrop-blur-md flex items-start gap-3.5">
      <div className={`p-2.5 rounded-xl border shrink-0 ${COLOR_STYLES[color]}`}>
        {icon}
      </div>
      <div>
        <h3 className="text-white text-sm font-semibold mb-0.5">{title}</h3>
        <p className="text-gray-400 text-xs leading-relaxed">{description}</p>
      </div>
    </div>
  )
}