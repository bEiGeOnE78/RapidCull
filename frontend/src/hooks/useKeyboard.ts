import { useEffect } from 'react'

type KeyMap = Record<string, (e: KeyboardEvent) => void>

export function useKeyboard(keyMap: KeyMap, enabled = true): void {
  useEffect(() => {
    if (!enabled) return

    function handleKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT'
      ) {
        return
      }

      const handler = keyMap[e.key]
      if (handler) {
        handler(e)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [keyMap, enabled])
}
