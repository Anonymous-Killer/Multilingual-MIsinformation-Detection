import { useState, useCallback } from 'react'
import type { AnalyzeHeadlineResponse, HistoryEntry } from '../types'

const STORAGE_KEY = 'verifai_history'
const MAX_ENTRIES = 50

function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as HistoryEntry[]) : []
  } catch {
    return []
  }
}

function saveHistory(entries: HistoryEntry[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries))
}

export function useHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>(loadHistory)

  const addEntry = useCallback((result: AnalyzeHeadlineResponse) => {
    const entry: HistoryEntry = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      headline: result.input_headline,
      classification: result.classification,
      reliability_score: result.reliability_score,
      confidence: result.confidence,
      detected_language: result.detected_language,
      timestamp: new Date().toISOString(),
      result,
    }
    setHistory((prev) => {
      const updated = [entry, ...prev].slice(0, MAX_ENTRIES)
      saveHistory(updated)
      return updated
    })
  }, [])

  const clearHistory = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setHistory([])
  }, [])

  return { history, addEntry, clearHistory }
}
