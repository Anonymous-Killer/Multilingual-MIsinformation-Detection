import type { ReactNode } from 'react'
import { CheckCircle, XCircle, AlertTriangle, HelpCircle, MinusCircle } from 'lucide-react'
import type { ClassificationLabel } from '../types'

interface Cfg { label: string; icon: ReactNode; cls: string }

const MAP: Record<ClassificationLabel, Cfg> = {
  true:                 { label: 'Reliable',              icon: <CheckCircle   size={12} strokeWidth={2.5} />, cls: 'bg-green-100  text-green-700  ring-green-200'  },
  false:                { label: 'Likely False',          icon: <XCircle       size={12} strokeWidth={2.5} />, cls: 'bg-red-100    text-red-700    ring-red-200'    },
  misleading:           { label: 'Questionable',          icon: <AlertTriangle size={12} strokeWidth={2.5} />, cls: 'bg-amber-100  text-amber-700  ring-amber-200'  },
  unverifiable:         { label: 'Unverifiable',          icon: <HelpCircle   size={12} strokeWidth={2.5} />, cls: 'bg-gray-100   text-gray-600   ring-gray-200'   },
  insufficient_evidence:{ label: 'Insufficient Evidence', icon: <MinusCircle  size={12} strokeWidth={2.5} />, cls: 'bg-gray-100   text-gray-600   ring-gray-200'   },
}

export function ClassificationBadge({ classification, size = 'md' }: { classification: ClassificationLabel; size?: 'sm' | 'md' }) {
  const { label, icon, cls } = MAP[classification]
  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium ring-1 ${cls} ${size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'}`}>
      {icon}{label}
    </span>
  )
}
