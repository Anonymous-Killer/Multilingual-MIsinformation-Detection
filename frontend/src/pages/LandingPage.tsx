import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Globe, FileText, TrendingUp } from 'lucide-react'
import { analyzeHeadline, ApiError } from '../api/analyze'
import { LoadingSteps } from '../components/LoadingSteps'
import { useHistory } from '../hooks/useHistory'

const FEATURES = [
  { icon: Globe,       label: 'Multilingual detection' },
  { icon: FileText,    label: 'Fact-check sources'     },
  { icon: TrendingUp,  label: 'Reliability scoring'    },
]

export function LandingPage() {
  const navigate = useNavigate()
  const { addEntry } = useHistory()
  const [headline, setHeadline] = useState('')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState<string | null>(null)

  const canSubmit = headline.trim().length >= 5 && !loading

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    setError(null)
    setLoading(true)
    try {
      const result = await analyzeHeadline(headline.trim())
      addEntry(result)
      navigate('/results', { state: { result } })
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.status === 422
            ? 'Headline must be between 5 and 500 characters.'
            : `Server error (${err.status}). Is the backend running on port 8000?`
          : 'Could not reach the server. Check your connection.',
      )
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-lg px-4">
        <LoadingSteps />
      </main>
    )
  }

  return (
    <main className="flex min-h-[calc(100vh-57px)] flex-col items-center justify-center px-4 py-16 animate-fade-in">
      {/* Hero text */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900">
          Check if a headline is real
        </h1>
        <p className="mt-2 text-base text-gray-500">Evidence-based AI analysis</p>
      </div>

      {/* Input card */}
      <form onSubmit={handleSubmit} className="w-full max-w-lg">
        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
          <textarea
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            placeholder="Paste a news headline..."
            rows={4}
            maxLength={500}
            className="w-full resize-none px-4 pt-4 pb-2 text-sm text-gray-800 placeholder-gray-400 outline-none"
          />
          <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3">
            {error
              ? <p className="text-xs text-red-500">{error}</p>
              : <span className="text-xs text-gray-400">{headline.length}/500</span>
            }
            <button
              type="submit"
              disabled={!canSubmit}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Search size={14} strokeWidth={2.5} />
              Analyze
            </button>
          </div>
        </div>
      </form>

      {/* Feature icons */}
      <div className="mt-10 flex items-center gap-10">
        {FEATURES.map(({ icon: Icon, label }) => (
          <div key={label} className="flex flex-col items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100">
              <Icon size={18} className="text-blue-600" strokeWidth={2} />
            </div>
            <span className="text-xs font-medium text-blue-600">{label}</span>
          </div>
        ))}
      </div>
    </main>
  )
}
