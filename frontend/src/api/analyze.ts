import type { AnalyzeHeadlineResponse } from '../types'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function analyzeHeadline(
  headline: string,
): Promise<AnalyzeHeadlineResponse> {
  const response = await fetch('/api/v1/analyze-headline', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ headline }),
  })

  if (!response.ok) {
    const text = await response.text().catch(() => 'Unknown error')
    throw new ApiError(response.status, text)
  }

  return response.json() as Promise<AnalyzeHeadlineResponse>
}
