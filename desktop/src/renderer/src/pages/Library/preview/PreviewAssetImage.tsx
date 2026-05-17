import { useState } from 'react'
import { ImageOff } from 'lucide-react'

interface PreviewAssetImageProps {
  apiBase: string
  apiToken: string
  parsedDocumentId: string
  src?: string
  alt?: string
}

export default function PreviewAssetImage({
  apiBase,
  apiToken,
  parsedDocumentId,
  src,
  alt,
}: PreviewAssetImageProps): JSX.Element {
  const [failed, setFailed] = useState(false)

  const resolved = resolveImageUrl({
    apiBase,
    apiToken,
    parsedDocumentId,
    src,
  })

  if (failed || !resolved) {
    return <PreviewAssetImageFallback alt={alt} src={src} />
  }

  return (
    <img
      src={resolved}
      alt={alt || ''}
      onError={() => setFailed(true)}
      className="my-4 max-w-full h-auto rounded-md border border-paper-300 bg-paper-50"
    />
  )
}

function resolveImageUrl({
  apiBase,
  apiToken,
  parsedDocumentId,
  src,
}: {
  apiBase: string
  apiToken: string
  parsedDocumentId: string
  src?: string
}): string | null {
  if (!src) return null

  if (
    src.startsWith('http://') ||
    src.startsWith('https://') ||
    src.startsWith('data:') ||
    src.startsWith('blob:')
  ) {
    return src
  }

  const relative = src.replace(/^\.\//, '').replace(/^\/+/, '')
  if (!relative.startsWith('images/')) {
    return null
  }
  const insideImages = relative.slice('images/'.length)
  if (!insideImages || insideImages.includes('..')) {
    return null
  }

  const encoded = insideImages
    .split('/')
    .map((segment) => encodeURIComponent(segment))
    .join('/')
  const tokenParam = apiToken
    ? `?token=${encodeURIComponent(apiToken)}`
    : ''
  return (
    `${apiBase}/api/parsed-documents/` +
    `${encodeURIComponent(parsedDocumentId)}/images/${encoded}${tokenParam}`
  )
}

function PreviewAssetImageFallback({
  alt,
  src,
}: {
  alt?: string
  src?: string
}): JSX.Element {
  const label = alt?.trim() || basenameFromSrc(src) || 'image'
  return (
    <span className="my-3 inline-block align-middle px-3 py-2 rounded-md border border-dashed border-paper-400 bg-paper-100 text-ink-tertiary text-xs font-sans not-italic">
      <ImageOff size={12} strokeWidth={1.7} className="inline-block mr-1.5 -mt-0.5" />
      <span className="inline truncate max-w-[40ch] align-middle">{label}</span>
    </span>
  )
}

function basenameFromSrc(src?: string): string | null {
  if (!src) return null
  return src.split('/').pop() || null
}
