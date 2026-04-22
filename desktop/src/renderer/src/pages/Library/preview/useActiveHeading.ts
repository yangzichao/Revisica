import { useEffect, useState } from 'react'

export function useActiveHeading(
  slugs: string[],
  scrollRootRef: React.RefObject<HTMLElement>,
): string | null {
  const [activeSlug, setActiveSlug] = useState<string | null>(null)

  useEffect(() => {
    setActiveSlug(null)
    if (slugs.length === 0) return
    const root = scrollRootRef.current
    if (!root) return

    const visible = new Set<string>()

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const slug = entry.target.id
          if (!slug) continue
          if (entry.isIntersecting) visible.add(slug)
          else visible.delete(slug)
        }
        const firstVisible = slugs.find((slug) => visible.has(slug))
        if (firstVisible) {
          setActiveSlug((prev) => (prev === firstVisible ? prev : firstVisible))
        }
      },
      {
        root,
        rootMargin: '-80px 0px -60% 0px',
        threshold: 0,
      },
    )

    for (const slug of slugs) {
      const el = root.querySelector(`#${CSS.escape(slug)}`)
      if (el) observer.observe(el)
    }

    return () => observer.disconnect()
  }, [slugs, scrollRootRef])

  return activeSlug
}
