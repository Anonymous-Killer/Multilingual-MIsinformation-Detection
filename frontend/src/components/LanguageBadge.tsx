import { Globe } from 'lucide-react'

export function LanguageBadge({ code }: { code: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-gray-300 bg-white px-2 py-0.5 text-xs font-medium text-gray-600">
      <Globe size={11} strokeWidth={2} className="text-gray-400" />
      {code.toUpperCase()}
    </span>
  )
}
