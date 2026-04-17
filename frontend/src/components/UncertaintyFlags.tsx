import { AlertTriangle } from 'lucide-react'

export function UncertaintyFlags({ flags }: { flags: string[] }) {
  if (flags.length === 0) return null
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-800">Uncertainty Flags</h3>
      <div className="flex flex-wrap gap-2">
        {flags.map((flag) => (
          <span key={flag} className="inline-flex items-center gap-1.5 rounded-full border border-orange-300 px-3 py-1 text-xs font-medium text-orange-600">
            <AlertTriangle size={11} strokeWidth={2.5} />
            {flag}
          </span>
        ))}
      </div>
    </div>
  )
}
