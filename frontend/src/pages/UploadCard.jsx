import React, { useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadCloud, FileText, AlertCircle, CheckCircle, Loader2, Sparkles, ArrowRight, Lock, TrendingUp, Smile, ShieldAlert } from 'lucide-react'

const STATUS_MESSAGES = {
  idle: null,
  uploading: 'Uploading and indexing transcript...',
  analyzing: 'Running AI analysis — sentiment, evasion, guidance extraction...',
  done: 'Analysis complete! Redirecting...',
  error: null
}

function getDropzoneStyles(dragOver, file) {
  if (dragOver) return 'border-indigo-400 bg-indigo-500/10'
  if (file) return 'border-emerald-500/50 bg-emerald-500/5'
  return 'border-indigo-500/30 bg-[#07091e]/50 hover:border-indigo-400/60 hover:bg-indigo-500/5'
}

export default function UploadCard({ file, status, error, dragOver, onFileSelect, onDrop, onDragOver, onDragLeave, onAnalyze}) {
  const fileInputRef = useRef(null)
  const isButtonDisabled = !file || (status !== 'idle' && status !== 'error')

  return (
    <div className="relative w-full max-w-2xl">

      <div className="hidden lg:flex flex-col gap-3 absolute -left-48 top-6 w-40 pointer-events-none z-0">
        <div className="p-3.5 rounded-xl bg-[#0f132a]/80 border border-blue-500/20 backdrop-blur-md shadow-xl flex flex-col gap-2">
          <TrendingUp size={18} className="text-blue-400" />
          <div className="h-1.5 w-16 bg-blue-500/30 rounded-full" />
          <div className="h-1 w-10 bg-blue-500/20 rounded-full" />
        </div>

        <div className="p-2.5 rounded-xl bg-[#0f132a]/80 border border-emerald-500/20 backdrop-blur-md shadow-xl flex items-center gap-2">
          <Smile size={16} className="text-emerald-400" />
          <div>
            <p className="text-[10px] text-gray-400 font-medium leading-none">Sentiment</p>
            <p className="text-xs font-semibold text-emerald-400">Positive</p>
          </div>
        </div>
      </div>

      <div className="hidden lg:flex flex-col gap-3 absolute -right-48 top-12 w-40 pointer-events-none z-0">
        <div className="p-3.5 rounded-xl bg-[#0f132a]/80 border border-purple-500/20 backdrop-blur-md shadow-xl flex flex-col gap-1.5 items-end">
          <div className="flex gap-1 items-end h-8">
            <div className="w-1.5 h-3 bg-purple-500/30 rounded-t" />
            <div className="w-1.5 h-5 bg-purple-500/50 rounded-t" />
            <div className="w-1.5 h-8 bg-purple-500 rounded-t" />
          </div>
        </div>

        <div className="p-2.5 rounded-xl bg-[#0f132a]/80 border border-amber-500/20 backdrop-blur-md shadow-xl flex items-center gap-2">
          <ShieldAlert size={16} className="text-amber-400" />
          <div>
            <p className="text-[10px] text-gray-400 font-medium leading-none">Evasion</p>
            <p className="text-xs font-semibold text-amber-400">Low Risk</p>
          </div>
        </div>
      </div>

      <div className="relative z-10 p-6 md:p-8 rounded-3xl bg-[#0b0e24]/80 border border-indigo-500/20 backdrop-blur-xl shadow-2xl shadow-indigo-950/50">
        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 md:p-10 text-center cursor-pointer transition-all ${getDropzoneStyles(dragOver, file)}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".json, application/json, .txt, .pdf, .docx"
            className="hidden"
            onChange={(e) => onFileSelect(e.target.files[0])}
          />

          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                key="file"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="flex flex-col items-center gap-3"
              >
                <div className="w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <FileText size={28} />
                </div>

                <p className="text-emerald-400 font-semibold text-base">{file.name}</p>
                <p className="text-gray-400 text-xs">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                <p className="text-gray-500 text-xs mt-1">Click to change file</p>
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="flex flex-col items-center gap-3"
              >
                <div className="w-14 h-14 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <UploadCloud size={28} />
                </div>

                <p className="text-white font-medium text-lg">Drop your transcript here</p>

                <p className="text-gray-400 text-sm">
                  or <span className="text-indigo-400 font-medium">click to browse</span> — PDF or JSON (Upload JSON format for best result)
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center gap-2 text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-left"
          >
            <AlertCircle size={16} className="shrink-0" />
            <span className="text-sm">{error}</span>
          </motion.div>
        )}

        {STATUS_MESSAGES[status] && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-4 flex items-center gap-2 text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 rounded-xl px-4 py-3 text-left"
          >
            {status === 'done'
              ? <CheckCircle size={16} className="text-emerald-400 shrink-0" />
              : <Loader2 size={16} className="animate-spin text-indigo-400 shrink-0" />}

            <span className="text-sm">{STATUS_MESSAGES[status]}</span>
          </motion.div>
        )}

        <motion.button
          onClick={onAnalyze}
          disabled={isButtonDisabled}
          whileTap={{ scale: 0.98 }}
          className={`w-full mt-5 py-3.5 rounded-xl font-medium text-base flex items-center justify-center gap-2 transition-all ${
            isButtonDisabled
              ? 'bg-gray-800/60 text-gray-500 cursor-not-allowed border border-gray-700/30'
              : 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-600/30 border border-indigo-400/30'
          }`}
        >
          {status === 'uploading' && 'Uploading...'}
          {status === 'analyzing' && 'Analyzing...'}
          {status === 'done' && 'Done!'}

          {(status === 'idle' || status === 'error') && (
            <>
              <Sparkles size={16} />
              <span>Analyze Transcript</span>
              <ArrowRight size={16} />
            </>
          )}
        </motion.button>
      </div>

      <div className="flex items-center justify-center gap-2 mt-4 text-gray-500 text-xs">
        <Lock size={12} />
        <span>Your data is encrypted and secure. We never share your transcripts.</span>
      </div>
    </div>
  )
}