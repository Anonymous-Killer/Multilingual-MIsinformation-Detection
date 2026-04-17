import { Lightbulb } from 'lucide-react'

export function ActualNewsCard({ headline, description }: { headline?: string | null; description?: string | null }) {
  if (!headline && !description) return null
  return (
    <div className="rounded-xl border border-purple-200 bg-purple-50 p-4">
      <div className="mb-2 flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-200">
          <Lightbulb size={13} className="text-purple-600" strokeWidth={2.5} />
        </div>
        <span className="text-sm font-semibold text-purple-800">Possible Real News</span>
      </div>
      {description && <p className="mb-2 text-xs leading-relaxed text-purple-600">{description}</p>}
      {headline && (
        <div className="rounded-lg border border-purple-200 bg-white px-3 py-2">
          <p className="text-sm font-medium text-gray-800">{headline}</p>
        </div>
      )}
    </div>
  )
}
