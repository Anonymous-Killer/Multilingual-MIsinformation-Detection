import { useEffect, useRef, useState } from 'react'

interface Props {
  score: number // 1–10
  size?: number
  animate?: boolean
}

function scoreColor(score: number): string {
  if (score <= 3) return '#ef4444'
  if (score <= 6) return '#f59e0b'
  if (score <= 8) return '#84cc16'
  return '#10b981'
}

// Arc: 270° sweep, gap centred at the bottom.
// Rotating the circle +135° moves the stroke start from 3 o'clock → 7-8 o'clock
// (bottom-left), so the 90° gap sits at 6 o'clock.
//
// Animation uses requestAnimationFrame with quadratic ease-out.
// dashoffset: arcLength (empty) → arcLength * (1 - score/10) (full).

export function ReliabilityGauge({ score, size = 130, animate = true }: Props) {
  const sw = Math.max(size * 0.09, 8)
  const r = (size - sw) / 2
  const cx = size / 2
  const cy = size / 2
  const circ = 2 * Math.PI * r
  const arcLen = circ * 0.75 // 270°

  const [offset, setOffset] = useState(arcLen)
  const [display, setDisplay] = useState(0)
  const raf = useRef<number | null>(null)

  useEffect(() => {
    // Reset state so StrictMode double-invoke starts clean each time
    setDisplay(0)
    setOffset(arcLen)

    if (!animate) {
      setOffset(arcLen * (1 - score / 10))
      setDisplay(score)
      return
    }

    const duration = 1000
    const t0 = performance.now()

    const tick = (now: number) => {
      const t = Math.min((now - t0) / duration, 1)
      const e = 1 - Math.pow(1 - t, 2) // ease-out quadratic
      setDisplay(Math.round(e * score))
      setOffset(arcLen * (1 - (e * score) / 10))
      if (t < 1) {
        raf.current = requestAnimationFrame(tick)
      } else {
        setDisplay(score)
        setOffset(arcLen * (1 - score / 10))
      }
    }

    raf.current = requestAnimationFrame(tick)
    return () => { if (raf.current !== null) cancelAnimationFrame(raf.current) }
  }, [score, animate, arcLen])

  const color = scoreColor(score)

  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(135deg)', transformOrigin: 'center' }}>
        {/* track */}
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#e5e7eb" strokeWidth={sw}
          strokeDasharray={`${arcLen} ${circ}`} strokeLinecap="round" />
        {/* fill */}
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={sw}
          strokeDasharray={`${arcLen} ${circ}`} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        pointerEvents: 'none',
      }}>
        <span style={{ fontSize: size * 0.28, fontWeight: 800, color, lineHeight: 1, fontFamily: 'inherit' }}>
          {display}
        </span>
        <span style={{ fontSize: size * 0.12, color: '#9ca3af', fontWeight: 500, fontFamily: 'inherit' }}>
          /10
        </span>
      </div>
    </div>
  )
}
