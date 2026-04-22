import GithubSlugger from 'github-slugger'

export interface TocEntry {
  level: number
  text: string
  slug: string
}

const HEADING_PATTERN = /^(#{1,6})\s+(.+?)\s*#*\s*$/
const CODE_FENCE_PATTERN = /^(```|~~~)/

export function extractTableOfContents(
  markdown: string,
  maxLevel = 3,
): TocEntry[] {
  // IMPORTANT: run the slugger over EVERY heading rehype-slug would see
  // (h1-h6), not just the levels we display. rehype-slug shares one slugger
  // across the whole tree and appends `-1`, `-2` for duplicate text. If we
  // skip h4+ before slugging, our slugs drift from the real DOM ids.
  const slugger = new GithubSlugger()
  const everyHeading: TocEntry[] = []
  let insideCodeFence = false

  for (const rawLine of markdown.split('\n')) {
    const trimmed = rawLine.trim()
    if (CODE_FENCE_PATTERN.test(trimmed)) {
      insideCodeFence = !insideCodeFence
      continue
    }
    if (insideCodeFence) continue

    const match = HEADING_PATTERN.exec(trimmed)
    if (!match) continue

    const level = match[1].length
    const text = stripInlineMarkdown(match[2])
    if (!text) continue

    everyHeading.push({ level, text, slug: slugger.slug(text) })
  }

  return everyHeading.filter((entry) => entry.level <= maxLevel)
}

function stripInlineMarkdown(text: string): string {
  // Match rehype-slug's view of the heading tree: strip only the syntactic
  // delimiters (`$`, `` ` ``, `*`, `_`, `[...](url)`, HTML tags) so the
  // surviving text fed to github-slugger mirrors hast-util-to-string's output.
  return text
    .replace(/\$+/g, '')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/<[^>]+>/g, '')
    .trim()
}
