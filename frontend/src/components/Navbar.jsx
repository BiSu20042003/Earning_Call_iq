import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { TrendingUp, History, Upload } from 'lucide-react'

export default function Navbar() {
  const location = useLocation()

  const links = [
    { to: '/', label: 'Upload', icon: Upload },
    { to: '/history', label: 'History', icon: History }
  ]

  return (
    <nav className="border-b border-white/10 bg-[#060814] px-6 md:px-10 py-5">
      <div className="w-full max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Logo Section */}
        <Link to="/" className="flex items-center gap-2.5">
          <TrendingUp className="text-purple-500" size={26} />
          <span className="text-xl font-bold text-white tracking-tight">
            EarningsIQ
          </span>
          <span className="text-[11px] font-bold text-white bg-[#7c3aed] px-2 py-0.5 rounded-md uppercase tracking-wider">
            AI
          </span>
        </Link>

        {/* Buttons Section */}
        <div className="flex items-center gap-3">
          {links.map(({ to, label, icon: Icon }) => {
            const isActive = location.pathname === to

            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-[#2563eb] to-[#9333ea] text-white shadow-md'
                    : 'bg-transparent text-gray-300 border border-white/20 hover:text-white hover:border-white/40'
                }`}
              >
                <Icon size={18} />
                <span>{label}</span>
              </Link>
            )
          })}
        </div>

      </div>
    </nav>
  )
}