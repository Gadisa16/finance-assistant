import { useEffect, useMemo, useRef, useState } from 'react'
import { askChat, ChatMessage, ChatStatus, fetchChatStatus } from '../services/api'

interface ChatWidgetProps {
  month: string
}

export default function ChatWidget({ month }: Readonly<ChatWidgetProps>) {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const inputRef = useRef<HTMLInputElement | null>(null)
  const storageKey = useMemo(() => `finance-chat:${month}`, [month])
  const [status, setStatus] = useState<ChatStatus | null>(null)

  // Load from localStorage when month changes
  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed)) setMessages(parsed)
        else setMessages([])
      } else {
        setMessages([])
      }
    } catch {
      setMessages([])
    }
  }, [storageKey])

  // Persist to localStorage on change
  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(messages))
    } catch {
      // ignore quota/security errors
    }
  }, [messages, storageKey])

  // Load chat status (mode/model)
  useEffect(() => {
    fetchChatStatus().then(setStatus).catch(() => setStatus(null))
  }, [])

  async function send() {
    if (!input.trim() || loading) return
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: input.trim() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    try {
      const answer = await askChat(month, userMsg.content)
      const assistant: ChatMessage = { id: crypto.randomUUID(), role: 'assistant', content: answer }
      setMessages(prev => [...prev, assistant])
    } catch (e: any) {
      const errMsg: ChatMessage = { id: crypto.randomUUID(), role: 'assistant', content: 'Error: ' + (e?.message || 'Failed to get answer') }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function clearChat() {
    setMessages([])
    try { localStorage.removeItem(storageKey) } catch { /* ignore */ }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 text-sm">
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="rounded-full shadow-lg bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 flex items-center gap-2"
          aria-label="Open Chat"
        >
          <span>💬 Chat</span>
        </button>
      )}
      {open && (
        <div className="w-80 h-96 bg-white border border-gray-300 rounded-lg shadow-xl flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 bg-indigo-600 text-white text-xs">
            <span className="font-semibold">Finance Chat (Month {month})</span>
            <div className="flex items-center gap-2">
              {messages.length > 0 && (
                <button onClick={clearChat} className="px-2 py-0.5 rounded bg-indigo-500 hover:bg-indigo-400" aria-label="Clear chat">Clear</button>
              )}
              <button onClick={() => setOpen(false)} aria-label="Close" className="hover:opacity-80">✕</button>
            </div>
          </div>
          <div className="flex-1 p-3 overflow-y-auto space-y-3 bg-gray-50">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center text-gray-600">
                <div className="text-4xl mb-2">🤖</div>
                <div className="text-sm mb-1">Ask anything about the ingested data for month {month}.</div>
                {status && (
                  <div className="text-xs text-gray-500" title={status.api_url || ''}>
                    {status.mode === 'groq' ? (
                      <>LLM mode: Groq — model <span className="font-medium">{status.model || 'unknown'}</span></>
                    ) : (
                      <>LLM mode: Stub (offline)</>
                    )}
                  </div>
                )}
              </div>
            )}
            {messages.map(m => (
              <div
                key={m.id}
                className={`rounded-md px-2 py-1 whitespace-pre-wrap break-words ${m.role === 'user' ? 'bg-indigo-600 text-white self-end ml-10' : 'bg-gray-200 text-gray-900 mr-10'}`}
              >
                {m.content}
              </div>
            ))}
            {loading && <div className="text-xs text-gray-500 animate-pulse">Thinking…</div>}
          </div>
          <form
            onSubmit={(e) => { e.preventDefault(); send(); }}
            className="border-t border-gray-200 p-2 flex gap-2"
          >
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type a question"
              className="flex-1 px-2 py-1 rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-3 py-1 rounded bg-indigo-600 text-white text-xs disabled:opacity-50"
            >Send</button>
          </form>
        </div>
      )}
    </div>
  )
}
