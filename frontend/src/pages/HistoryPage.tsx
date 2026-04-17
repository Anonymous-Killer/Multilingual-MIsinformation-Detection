import { useNavigate } from 'react-router-dom'
import { Clock, Trash2 } from 'lucide-react'
import { useHistory }          from '../hooks/useHistory'
import { ReliabilityGauge }    from '../components/ReliabilityGauge'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { LanguageBadge }       from '../components/LanguageBadge'

function relativeTime(iso: string): string {
  try {
    const m = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000)
    if (m < 1)  return 'Just now'
    if (m < 60) return `${m} minute${m !== 1 ? 's' : ''} ago`
    const h = Math.floor(m / 60)
    if (h < 24) return `about ${h} hour${h !== 1 ? 's' : ''} ago`
    const d = Math.floor(h / 24)
    return `${d} day${d !== 1 ? 's' : ''} ago`
  } catch { return '' }
}

export function HistoryPage() {
  const navigate = useNavigate()
  const { history, clearHistory } = useHistory()

  return (
    <main className="mx-auto max-w-5xl px-6 py-8 animate-fade-in">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analysis History</h1>
          <p className="mt-1 text-sm text-gray-500">Review your past fact-checks</p>
        </div>
        {history.length > 0 && (
          <button
            onClick={() => { if (confirm('Clear all history?')) clearHistory() }}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-500 hover:border-red-200 hover:text-red-500 transition-colors"
          >
            <Trash2 size={12} strokeWidth={2} /> Clear all
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-gray-300 bg-white py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-100">
            <Clock size={22} className="text-gray-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-700">No analyses yet</p>
            <p className="mt-1 text-xs text-gray-400">Results will appear here after you analyze a headline.</p>
          </div>
          <button onClick={() => navigate('/')} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors">
            Analyze a headline
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {history.map((entry) => {
            const n = entry.result.retrieved_sources.length
            return (
              <button
                key={entry.id}
                onClick={() => navigate('/results', { state: { result: entry.result } })}
                className="group flex flex-col rounded-xl border border-gray-200 bg-white p-4 text-left transition-all hover:border-blue-300 hover:shadow-sm"
              >
                <div className="flex items-start gap-3">
                  <ReliabilityGauge score={entry.reliability_score} size={88} animate={false} />
                  <div className="flex min-w-0 flex-1 flex-col gap-2 pt-1">
                    <p className="line-clamp-2 text-sm font-semibold leading-snug text-gray-900 group-hover:text-blue-700 transition-colors">
                      {entry.headline}
                    </p>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <ClassificationBadge classification={entry.classification} size="sm" />
                      <LanguageBadge code={entry.detected_language} />
                    </div>
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between border-t border-gray-100 pt-3">
                  <span className="flex items-center gap-1 text-xs text-gray-400">
                    <Clock size={11} strokeWidth={2} />{relativeTime(entry.timestamp)}
                  </span>
                  <span className="text-xs text-gray-400">{n} {n === 1 ? 'source' : 'sources'}</span>
                </div>
              </button>
            )
          })}
        </div>
      )}
    </main>
  )
}
