import { ExternalLink } from 'lucide-react'
import type { RetrievedSource } from '../types'

function trust(w: number) {
  if (w >= 0.7) return { label: 'High Trust',   cls: 'text-green-600' }
  if (w >= 0.4) return { label: 'Medium Trust', cls: 'text-amber-600' }
  return              { label: 'Low Trust',    cls: 'text-red-500'   }
}

export function SourceCard({ source }: { source: RetrievedSource }) {
  const { label, cls } = trust(source.credibility_weight)
  return (
    <div className="flex flex-col justify-between rounded-xl border border-gray-200 bg-white p-3">
      <div>
        <div className="mb-1.5 flex items-start justify-between gap-2">
          <span className="text-sm font-semibold text-gray-800 leading-tight">{source.source_name}</span>
          {source.url && (
            <a href={String(source.url)} target="_blank" rel="noopener noreferrer" className="shrink-0 text-blue-500 hover:text-blue-600">
              <ExternalLink size={13} strokeWidth={2} />
            </a>
          )}
        </div>
        {(source.snippet || source.title) && (
          <p className="mb-2 line-clamp-2 text-xs leading-relaxed text-gray-500">
            {source.snippet || source.title}
          </p>
        )}
      </div>
      <span className={`text-xs font-medium ${cls}`}>{label}</span>
    </div>
  )
}
