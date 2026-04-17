export type ClassificationLabel =
  | 'true'
  | 'false'
  | 'misleading'
  | 'unverifiable'
  | 'insufficient_evidence'

export interface RetrievedSource {
  source_id: string
  source_name: string
  source_type: string
  title: string
  url?: string | null
  language: string
  snippet: string
  claim_text: string
  verdict_label?: string | null
  published_at?: string | null
  credibility_weight: number
  similarity_score: number
  agreement: string
  metadata: Record<string, unknown>
}

export interface EvidenceFeatures {
  fact_check_match_score: number
  support_score: number
  contradiction_score: number
  source_credibility_score: number
  recency_score: number
  coverage_score: number
  uncertainty_penalty: number
}

export interface AnalyzeHeadlineResponse {
  input_headline: string
  detected_language: string
  normalized_claim: string
  classification: ClassificationLabel
  retrieved_sources: RetrievedSource[]
  evidence_summary: string
  reliability_score: number
  confidence: number
  reasoning_trace_summary: string
  limitations: string[]
  uncertainty_flags: string[]
  evidence_features: EvidenceFeatures
  actual_news_headline?: string | null
  actual_news_description?: string | null
}

export interface HistoryEntry {
  id: string
  headline: string
  classification: ClassificationLabel
  reliability_score: number
  confidence: number
  detected_language: string
  timestamp: string
  result: AnalyzeHeadlineResponse
}
