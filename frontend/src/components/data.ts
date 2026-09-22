import { useEffect, useState } from 'react'
import { api } from '../api/tower'

export const number = (value: number | null | undefined, digits = 0) =>
  value == null
    ? '—'
    : new Intl.NumberFormat('en-GB', { maximumFractionDigits: digits }).format(value)
export const percent = (value: number | null | undefined) =>
  value == null ? '—' : `${number(value * 100, 1)}%`
export const date = (value: string) =>
  new Date(value).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
export function useData<T>(path: string | null) {
  const [state, setState] = useState<{
    data: T | null
    error: string | null
    loading: boolean
    path?: string
    version?: number
  }>({ data: null, error: null, loading: true })
  const [version, setVersion] = useState(0)
  useEffect(() => {
    if (!path) return
    const abort = new AbortController()
    api<T>(path, abort.signal)
      .then((data) => setState({ data, error: null, loading: false, path, version }))
      .catch((e: Error) => {
        if (!abort.signal.aborted)
          setState({ data: null, error: e.message, loading: false, path, version })
      })
    return () => abort.abort()
  }, [path, version])
  return {
    ...state,
    data: state.path === path ? state.data : null,
    loading: !!path && (state.path !== path || state.version !== version),
    error: state.path === path && state.version === version ? state.error : null,
    retry: () => setVersion((v) => v + 1),
  }
}
