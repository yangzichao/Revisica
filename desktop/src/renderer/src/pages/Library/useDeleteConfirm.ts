import { useCallback, useEffect, useRef, useState } from 'react'

interface UseDeleteConfirmOptions {
  perform: () => Promise<void>
  onDeleted?: () => void
}

interface UseDeleteConfirmResult {
  isConfirming: boolean
  isDeleting: boolean
  error: string | null
  request: () => Promise<void>
  cancel: () => void
  clearError: () => void
}

export function useDeleteConfirm({
  perform,
  onDeleted,
}: UseDeleteConfirmOptions): UseDeleteConfirmResult {
  const [isConfirming, setIsConfirming] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mountedRef = useRef(true)
  const inFlightRef = useRef(false)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  const request = useCallback(async (): Promise<void> => {
    // Ref-based re-entry guard: state updates aren't visible to a second
    // synchronous click, so rely on the ref to reject double-fire.
    if (inFlightRef.current) return
    if (!isConfirming) {
      setIsConfirming(true)
      return
    }
    inFlightRef.current = true
    setIsDeleting(true)
    setError(null)
    try {
      await perform()
      if (!mountedRef.current) return
      inFlightRef.current = false
      setIsDeleting(false)
      setIsConfirming(false)
      onDeleted?.()
    } catch (err) {
      inFlightRef.current = false
      if (!mountedRef.current) return
      setIsDeleting(false)
      setIsConfirming(false)
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }, [isConfirming, perform, onDeleted])

  const cancel = useCallback(() => {
    setIsConfirming(false)
    setError(null)
  }, [])

  const clearError = useCallback(() => setError(null), [])

  return { isConfirming, isDeleting, error, request, cancel, clearError }
}
