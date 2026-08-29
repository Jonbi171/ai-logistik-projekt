export type ApiValue = string | number | boolean | null | Record<string, unknown>

export type DashboardResponse = {
  view: string
  summary: Record<string, ApiValue>
  items: Record<string, unknown>[]
}
