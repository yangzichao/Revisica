import { memo, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Components } from 'react-markdown'
import PreviewAssetImage from './PreviewAssetImage'
import {
  ExternalSafeLink,
  MermaidAwarePre,
  REHYPE_PLUGINS,
  REMARK_PLUGINS,
  StyledTable,
  SubstantiveDetails,
} from './markdownComponents'

interface LibraryPreviewDocumentProps {
  markdown: string
  apiBase: string
  apiToken: string
  parsedDocumentId: string
}

function LibraryPreviewDocument({
  markdown,
  apiBase,
  apiToken,
  parsedDocumentId,
}: LibraryPreviewDocumentProps): JSX.Element {
  // ReactMarkdown re-instantiates components on every render unless we
  // memoize the map — without this, every img/table/a in the document
  // remounts on each parent re-render, which kicks off a fresh image
  // fetch and flickers the page.
  const markdownComponents = useMemo<Components>(
    () => ({
      img: (props) => (
        <PreviewAssetImage
          apiBase={apiBase}
          apiToken={apiToken}
          parsedDocumentId={parsedDocumentId}
          src={props.src}
          alt={props.alt}
        />
      ),
      table: StyledTable,
      a: ExternalSafeLink,
      pre: MermaidAwarePre,
      details: SubstantiveDetails,
    }),
    [apiBase, apiToken, parsedDocumentId],
  )

  return (
    <article className="prose-paper prose-paper-preview max-w-[72ch]">
      <ReactMarkdown
        remarkPlugins={REMARK_PLUGINS}
        rehypePlugins={REHYPE_PLUGINS}
        components={markdownComponents}
      >
        {markdown}
      </ReactMarkdown>
    </article>
  )
}

export default memo(LibraryPreviewDocument)
