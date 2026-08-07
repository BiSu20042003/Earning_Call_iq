import React from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { Smile, Meh, Frown } from 'lucide-react'
 
const COLORS = {
  positive: '#10b981',
  neutral: '#f59e0b',
  negative: '#ef4444'
}
 
// Picks whichever sentiment has the highest share, positive wins ties over negative
function getDominantSentiment(pos, neu, neg) {
  if (pos >= neu && pos >= neg) return { label: 'Mostly Positive', Icon: Smile }
  if (neg >= pos && neg >= neu) return { label: 'Mostly Negative', Icon: Frown }
  return { label: 'Mostly Neutral', Icon: Meh }
}
 
export default function SentimentChart({ data }) {
  const pos = Math.round((data.positive || 0) * 100)
  const neu = Math.round((data.neutral || 0) * 100)
  const neg = Math.round((data.negative || 0) * 100)
 
  const chartData = [
    { name: 'Neutral', value: neu, color: COLORS.neutral },
    { name: 'Negative', value: neg, color: COLORS.negative },
    { name: 'Positive', value: pos, color: COLORS.positive }
  ]
 
  const { label: dominantLabel, Icon: DominantIcon } = getDominantSentiment(pos, neu, neg)
 
  return (
    <div className="flex flex-col items-center justify-center h-full w-full pt-1">
      <div className="relative w-full h-[190px] flex items-center justify-center mx-auto">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={78}
              innerRadius={54}
              startAngle={90}
              endAngle={-270}
              stroke="none"
            >
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
 
            <Tooltip
              contentStyle={{
                backgroundColor: '#0c0f28',
                borderColor: '#1e2548',
                borderRadius: '10px',
                color: '#fff',
                fontSize: '12px',
                boxShadow: '0 10px 25px -5px rgba(0,0,0,0.5)'
              }}
              formatter={(value) => [`${value}%`, 'Percentage']}
            />
          </PieChart>
        </ResponsiveContainer>
 
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
          <DominantIcon size={22} className="text-gray-300 mb-0.5" />
          <p className="text-xs font-semibold text-gray-200">{dominantLabel}</p>
        </div>
      </div>
 
      <div className="grid grid-cols-3 w-full text-center pt-3 border-t border-white/5 mt-2">
        <div>
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <span className="text-xs text-gray-400">Negative</span>
          </div>
          <p className="text-lg font-bold text-white">{neg}%</p>
        </div>
        <div>
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span className="text-xs text-gray-400">Neutral</span>
          </div>
          <p className="text-lg font-bold text-white">{neu}%</p>
        </div>
        <div>
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-xs text-gray-400">Positive</span>
          </div>
          <p className="text-lg font-bold text-white">{pos}%</p>
        </div>
      </div>
    </div>
  )
}