import React, { useState, useEffect, useRef } from 'react'
import { MessageSquare, Send, Loader2 } from 'lucide-react'
import { chatWithDocument, getChatHistory } from '../services/api'

export default function ChatPanel({ docId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    async function fetchChatHistory() {
      try{
        const history = await getChatHistory(docId)
        setMessages(history)
      }
      catch{
        console.log("No history available!")
      }
    }
    fetchChatHistory();
  }, [docId])



  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage() {
    if (!input.trim() || loading) return

    const question = input.trim()
    setInput('')
    setLoading(true)

    // Show the question immediately with a pending answer, then fill it in once the reply arrives
    setMessages(prev => [...prev, { question, answer: null, sources: [] }])

    try {
      const reply = await chatWithDocument(docId, question)
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = reply
        return updated
      })
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          question,
          answer: 'Error getting response. Please try again.',
          sources: []
        }
        return updated
      })
    }

    setLoading(false)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-[600px] px-1">
      <div className="flex-1 overflow-y-auto space-y-6 pr-3 pb-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <MessageSquare className="text-gray-600 mb-3" size={36} />
            <p className="text-gray-400 font-medium text-sm">Ask anything about this transcript</p>
            <p className="text-gray-500 text-xs mt-1">
              e.g. "What did the CFO say about margins?"
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className="space-y-4 my-3">
            <div className="flex justify-end">
              <div className="bg-[#ffeadb] border border-[#fdba74] rounded-2xl rounded-tr-md px-6 py-4 max-w-[75%] shadow-md">
                <p className="text-[#7c2d12] font-semibold text-sm leading-relaxed whitespace-pre-wrap">{msg.question}</p>
              </div>
            </div>

            <div className="flex justify-start">
              <div className="bg-[#dcfce7] border border-[#86efac] rounded-2xl rounded-tl-md px-6 py-4.5 max-w-[80%] shadow-md">
                {msg.answer === null ? (
                  <div className="flex items-center gap-3 py-1 text-[#14532d] font-semibold text-sm">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#16a34a] animate-bounce [animation-delay:-0.3s]" />
                      <span className="w-2.5 h-2.5 rounded-full bg-[#16a34a] animate-bounce [animation-delay:-0.15s]" />
                      <span className="w-2.5 h-2.5 rounded-full bg-[#16a34a] animate-bounce" />
                    </div>
                    <span className="italic tracking-wide">getting response...</span>
                  </div>
                ) : (
                  <>
                    <p className="text-[#14532d] text-sm leading-relaxed font-normal whitespace-pre-wrap">{msg.answer}</p>
                    {msg.sources?.length > 0 && (
                      <div className="mt-3.5 space-y-2 border-t border-[#bbf7d0] pt-3">
                        {msg.sources.map((src, j) => (
                          <div
                            key={j}
                            className="text-xs text-[#166534] bg-[#bbf7d0]/60 rounded-lg px-3 py-2 font-medium"
                          >
                            📄 Page {src.page_num} — {src.text_preview?.slice(0, 80)}...
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="mt-2 pt-3 border-t border-white/10 flex gap-3 items-end">
        <textarea
          rows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask your query about this transcript"
          className="flex-1 bg-[#0b0e24] border border-white/20 rounded-2xl px-5 py-3.5 text-white text-sm placeholder-gray-400 focus:outline-none focus:border-indigo-500/80 shadow-inner resize-none leading-relaxed"
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-white/5 disabled:text-gray-600 text-white px-5 py-4 rounded-2xl transition-all h-[92px] flex items-center justify-center shrink-0 cursor-pointer"
        >
          {loading ? <Loader2 size={22} className="animate-spin" /> : <Send size={22} />}
        </button>
      </div>
    </div>
  )
}