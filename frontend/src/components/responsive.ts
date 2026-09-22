import { useCallback, useEffect, useRef, useSyncExternalStore } from 'react'

export function useMediaQuery(query: string) {
  const subscribe = useCallback(
    (update: () => void) => {
      const media = window.matchMedia(query)
      media.addEventListener('change', update)
      return () => media.removeEventListener('change', update)
    },
    [query],
  )
  const snapshot = useCallback(() => window.matchMedia(query).matches, [query])
  return useSyncExternalStore(subscribe, snapshot)
}

// Keep navigation and shipment details usable with touch or an external keyboard.
export function useModal(active: boolean, close: () => void) {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    if (!active || !ref.current) return
    const container = ref.current
    const previousFocus = document.activeElement as HTMLElement | null
    const scrollY = window.scrollY
    const previousHash = window.location.hash
    const saved = {
      position: document.body.style.position,
      top: document.body.style.top,
      width: document.body.style.width,
    }
    Object.assign(document.body.style, { position: 'fixed', top: `-${scrollY}px`, width: '100%' })
    const focusable = () =>
      Array.from(
        container.querySelectorAll<HTMLElement>(
          'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), [tabindex="0"]',
        ),
      ).filter((element) => element.getClientRects().length > 0)
    ;(container.querySelector<HTMLElement>('[data-modal-close]') ?? focusable()[0])?.focus()
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        close()
      }
      if (event.key !== 'Tab') return
      const items = focusable()
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last?.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first?.focus()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      Object.assign(document.body.style, saved)
      window.scrollTo({
        top: window.location.hash === previousHash ? scrollY : 0,
        behavior: 'instant',
      })
      if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true })
    }
  }, [active, close])
  return ref
}
