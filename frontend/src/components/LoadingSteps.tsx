import { useEffect, useState } from 'react'
import { Check, Loader2 } from 'lucide-react'

const STEPS = [
  { id: 'detect',   label: 'Detecting language'  },
  { id: 'retrieve', label: 'Retrieving evidence' },
  { id: 'score',    label: 'Scoring reliability' },
]

export function LoadingSteps() {
  const [active, setActive] = useState(0)

  useEffect(() => {
    if (active >= STEPS.length - 1) return
    const t = setTimeout(() => setActive((s) => s + 1), 3500)
    return () => clearTimeout(t)
  }, [active])

  return (
    <div className="flex flex-col items-center gap-8 py-20 animate-fade-in">
      <div className="text-center">
        <p className="text-lg font-semibold text-gray-800">Analyzing headline…</p>
        <p className="mt-1 text-sm text-gray-500">This usually takes 10–20 seconds</p>
      </div>
      <div className="w-full max-w-xs space-y-2">
        {STEPS.map((step, i) => {
          const done = i < active
          const cur  = i === active
          return (
            <div key={step.id} className={`flex items-center gap-3 rounded-xl px-4 py-3 transition-all duration-300 ${cur ? 'bg-white shadow-sm ring-1 ring-gray-200' : ''} ${!cur && !done ? 'opacity-40' : ''}`}>
              <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors ${done ? 'bg-green-500 text-white' : cur ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
                {done ? <Check size={12} strokeWidth={3} /> : i + 1}
              </div>
              <span className={`text-sm font-medium ${cur ? 'text-gray-900' : 'text-gray-500'}`}>{step.label}</span>
              {cur && <Loader2 size={14} className="ml-auto animate-spin text-blue-400" />}
            </div>
          )
        })}
      </div>
    </div>
  )
}
