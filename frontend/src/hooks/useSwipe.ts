import { useRef } from 'react'

interface SwipeHandlers {
  onTouchStart: (e: React.TouchEvent) => void
  onTouchEnd: (e: React.TouchEvent) => void
}

export function useSwipe(
  onSwipeLeft: () => void,
  onSwipeRight: () => void,
  threshold = 50,
): SwipeHandlers {
  const startX = useRef<number | null>(null)

  const onTouchStart = (e: React.TouchEvent) => {
    startX.current = e.touches[0].clientX
  }

  const onTouchEnd = (e: React.TouchEvent) => {
    if (startX.current === null) return
    const endX = e.changedTouches[0].clientX
    const delta = endX - startX.current
    startX.current = null
    if (delta < -threshold) {
      onSwipeLeft()
    } else if (delta > threshold) {
      onSwipeRight()
    }
  }

  return { onTouchStart, onTouchEnd }
}
