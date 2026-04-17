import { useLocation, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, CircleArrowRight } from 'lucide-react'
import type { AnalyzeHeadlineResponse } from '../types'
import { ReliabilityGauge }    from '../components/ReliabilityGauge'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { LanguageBadge }       from '../components/LanguageBadge'
import { ConfidenceIndicator } from '../components/ConfidenceIndicator'
import { SourceCard }          from '../components/SourceCard'
import { UncertaintyFlags }    from '../components/UncertaintyFlags'
import { ActualNewsCard }      from '../components/ActualNewsCard'

function splitEvidence(text: string): string[] {
  const pts = text.split(/\.\s+/).map((s) => s.trim().replace(/\.$/, '')).filter((s) => s.length > 10)
  return pts.length > 1 ? pts : [text]
}


export function ResultPage() {
  const location = useLocation()
  const navigate  = useNavigate()
  const result    = location.state?.result as AnalyzeHeadlineResponse | undefined

  if (!result) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-24 text-center">
        <p className="mb-4 text-gray-500">No analysis result found.</p>
        <Link to="/" className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">
          <ArrowLeft size={14} /> Analyze a headline
        </Link>
      </main>
    )
  }

  const srcCount       = result.retrieved_sources.length
  const evidencePoints = splitEvidence(result.evidence_summary)
  const showRealNews   =
    (result.actual_news_headline || result.actual_news_description) &&
    result.confidence < 0.6

  return (
    <main className="mx-auto max-w-2xl px-4 py-6 md:py-8 animate-slide-up">
      {/* Back */}
      <button onClick={() => navigate('/')} className="mb-4 flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors">
        <ArrowLeft size={14} /> New Analysis
      </button>

      {/* ── Hero card ── */}
      <div className="mb-3 rounded-2xl border border-gray-200 bg-white p-5">
        <h1 className="mb-2 text-lg font-bold leading-snug text-gray-900">{result.input_headline}</h1>
        <LanguageBadge code={result.detected_language} />
        <div className="mt-4 flex items-center gap-5">
          <ReliabilityGauge score={result.reliability_score} size={120} />
          <div className="flex flex-col gap-2">
            <ClassificationBadge classification={result.classification} />
            <p className="text-xs text-gray-400">
              Reliability Score&nbsp;·&nbsp;Based on {srcCount} {srcCount === 1 ? 'source' : 'sources'}
            </p>
          </div>
        </div>
      </div>

      {/* ── Normalized claim ── */}
      {result.normalized_claim && result.normalized_claim !== result.input_headline && (
        <div className="mb-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3">
          <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-blue-400">Normalized Claim</p>
          <p className="text-sm text-gray-700">{result.normalized_claim}</p>
        </div>
      )}

      {/* ── Evidence summary ── */}
      <div className="mb-3 rounded-xl border border-gray-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-semibold text-gray-800">Evidence Summary</h2>
        <ul className="space-y-2">
          {evidencePoints.map((pt, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
              <CircleArrowRight size={14} className="mt-0.5 shrink-0 text-blue-400" strokeWidth={1.5} />
              {pt}
            </li>
          ))}
        </ul>
      </div>

      {/* ── Confidence ── */}
      <div className="mb-3"><ConfidenceIndicator confidence={result.confidence} /></div>

      {/* ── Uncertainty flags ── */}
      {result.uncertainty_flags.length > 0 && (
        <div className="mb-3"><UncertaintyFlags flags={result.uncertainty_flags} /></div>
      )}

      {/* ── Limitations ── */}
      {result.limitations.length > 0 && (
        <div className="mb-3 rounded-xl border border-gray-200 bg-white px-4 py-3">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-gray-400">Limitations</h3>
          <ul className="space-y-1">
            {result.limitations.map((lim) => (
              <li key={lim} className="text-xs leading-relaxed text-gray-500">· {lim}</li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Sources ── */}
      {result.retrieved_sources.length > 0 && (
        <div className="mb-3">
          <h2 className="mb-2 text-sm font-semibold text-gray-800">Sources Analyzed</h2>
          <div className="grid grid-cols-2 gap-2">
            {result.retrieved_sources.map((src) => <SourceCard key={src.source_id} source={src} />)}
          </div>
        </div>
      )}

      {/* ── Possible real news ── */}
      {showRealNews && (
        <div className="mb-3">
          <ActualNewsCard headline={result.actual_news_headline} description={result.actual_news_description} />
        </div>
      )}

      <div className="mt-6 flex justify-center">
        <button onClick={() => navigate('/')} className="rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700">
          Analyze another headline
        </button>
      </div>
    </main>
  )
}
