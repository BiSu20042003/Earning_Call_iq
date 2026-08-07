import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Analysis from './pages/Analysis'
import GuidancePage from './pages/GuidancePage'
import History from './pages/History'
import Navbar from './components/Navbar'

export default function App() {
  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analysis/:id" element={<Analysis />} />
        <Route path="/guidance/:doc_id" element={<GuidancePage />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </div>
  )
}