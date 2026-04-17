import { useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, CircleArrowRight, ChevronRight } from 'lucide-react'
import type { AnalyzeHeadlineResponse } from '../types'
import { ReliabilityGauge }    from '../components/ReliabilityGauge'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { LanguageBadge }       from '../components/LanguageBadge'
import { ConfidenceIndicator } from '../components/ConfidenceIndicator'
import { SourceCard }          from '../components/SourceCard'
import { UncertaintyFlags }    from '../components/UncertaintyFlags'
import { ActualNewsCard }      from '../components/ActualNewsCard'

function splitEvidence(text: string): string[] {
  const pts = text
    .split(/\.\s+/)
    .map(s => s.trim().replace(/\.$/, ''))
    .filter(s => s.length > 10)
  return pts.length > 1 ? pts : [text]
}

export function ResultPage() {
  const location  = useLocation()
  const navigate  = useNavigate()
  const result    = location.state?.result as AnalyzeHeadlineResponse | undefined
  const [showSources, setShowSources] = useState(false)

  if (!result) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-24 text-center">
        <p className="mb-4 text-gray-500">No analysis result found.</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
        >
          <ArrowLeft size={14} /> Analyze a headline
        </Link>
      </main>
    )
  }

  const srcCount       = result.retrieved_sources.length
  const evidencePoints = splitEvidence(result.evidence_summary)
  const showRealNews   =
    (result.actual_news_headline || result.actual_news_description) &&
    result.reliability_score <= 6

  return (
    <main
      className="mx-auto px-6 py-6 md:py-8 animate-slide-up"
      style={{
        maxWidth: showSources ? 'calc(100vw - 48px)' : '72rem',
        transition: 'max-width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >

      {/* Back */}
      <button
        onClick={() => navigate('/')}
        className="mb-4 flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
      >
        <ArrowLeft size={14} /> New Analysis
      </button>

      {/* ── Root flex row: main content | sources panel ── */}
      <div className="flex items-start gap-4">

        {/* ═══ Main content column (Sections 1 · 2 · 3) ═══ */}
        <div
          className="min-w-0 flex flex-col gap-3"
          style={{
            width: showSources ? 'calc(60% - 8px)' : '100%',
            transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >

          {/* ── Top row: Section 1 + Section 2 ── */}
          {/*
            Default:  3fr / 2fr side-by-side
            Expanded: single column (inner layout snaps; outer slide is the hero animation)
          */}
          <div
            className={`grid gap-3 ${showSources ? 'grid-cols-1' : 'grid-cols-[3fr_2fr]'}`}
          >
            {/* ── Section 1 · Headline + Reliability Score ── */}
            <div className="rounded-2xl border border-gray-200 bg-white p-5">
              <h1 className="mb-2 text-lg font-bold leading-snug text-gray-900">
                {result.input_headline}
              </h1>
              <LanguageBadge code={result.detected_language} />
              <div className="mt-4 flex items-center gap-5">
                <ReliabilityGauge score={result.reliability_score} size={110} />
                <div className="flex flex-col gap-2">
                  <ClassificationBadge classification={result.classification} />
                  <p className="text-xs text-gray-400">
                    Reliability Score&nbsp;·&nbsp;Based on {srcCount}&nbsp;
                    {srcCount === 1 ? 'source' : 'sources'}
                  </p>
                </div>
              </div>
            </div>

            {/* ── Section 2 · Normalized Claim + Evidence Summary ── */}
            <div className="flex flex-col gap-3">
              {result.normalized_claim &&
                result.normalized_claim !== result.input_headline && (
                  <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3">
                    <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-blue-400">
                      Normalized Claim
                    </p>
                    <p className="text-sm text-gray-700">{result.normalized_claim}</p>
                  </div>
                )}

              <div className="flex-1 rounded-xl border border-gray-200 bg-white p-4">
                <h2 className="mb-3 text-sm font-semibold text-gray-800">Evidence Summary</h2>
                <ul className="space-y-2">
                  {evidencePoints.map((pt, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <CircleArrowRight
                        size={14}
                        className="mt-0.5 shrink-0 text-blue-400"
                        strokeWidth={1.5}
                      />
                      {pt}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* ── Section 3 · Context + Actions ── */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5">
            <div className="space-y-4">

              {/* Possible real news */}
              {showRealNews && (
                <ActualNewsCard
                  headline={result.actual_news_headline}
                  description={result.actual_news_description}
                />
              )}

              {/* Confidence */}
              <ConfidenceIndicator confidence={result.confidence} />

              {/* Uncertainty flags */}
              {result.uncertainty_flags.length > 0 && (
                <UncertaintyFlags flags={result.uncertainty_flags} />
              )}

              {/* Limitations */}
              {result.limitations.length > 0 && (
                <div className="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3">
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-gray-400">
                    Limitations
                  </h3>
                  <ul className="space-y-1">
                    {result.limitations.map(lim => (
                      <li key={lim} className="text-xs leading-relaxed text-gray-500">
                        · {lim}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* ── Action buttons ── */}
            <div className="mt-5 flex items-center justify-center gap-3">
              <button
                onClick={() => navigate('/')}
                className="rounded-xl border border-gray-200 bg-white px-5 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 active:bg-gray-100"
              >
                Analyze Another Headline
              </button>

              <button
                onClick={() => setShowSources(v => !v)}
                className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 active:bg-blue-800"
              >
                {showSources ? 'Hide Sources' : 'Check Sources'}
                <ChevronRight
                  size={14}
                  style={{
                    transform: showSources ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.4s ease-in-out',
                  }}
                />
              </button>
            </div>
          </div>
        </div>

        {/* ═══ Section 4 · Sources panel (slides in from right) ═══ */}
        <div
          className="shrink-0 overflow-hidden"
          style={{
            width:      showSources ? 'calc(40% - 8px)' : '0%',
            opacity:    showSources ? 1 : 0,
            transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.4s ease-in-out',
          }}
        >
          {/*
            Fixed min-width prevents source cards from reflowing as the panel
            slides in. The parent overflow-hidden clips the content cleanly.
          */}
          <div style={{ minWidth: '380px' }}>
            <div className="rounded-2xl border border-gray-200 bg-white p-5">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-800">
                Sources Analyzed
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                  {srcCount}
                </span>
              </h2>

              <div className="flex flex-col gap-3">
                {result.retrieved_sources.map(src => (
                  <SourceCard key={src.source_id} source={src} />
                ))}
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>
  )
}
