import type { ApiEndpoint } from './endpoints'
import type { DashboardResponse } from './types'

export async function fetchDashboard(
  url: ApiEndpoint,
  signal?: AbortSignal,
): Promise<DashboardResponse> {
  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
    signal,
  })

  if (!response.ok) {
    throw new Error(`The API returned ${response.status} ${response.statusText}`)
  }

  return response.json() as Promise<DashboardResponse>
}
