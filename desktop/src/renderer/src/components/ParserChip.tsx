export default function ParserChip({ parser }: { parser: string }): JSX.Element {
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border border-accent/30 bg-accent/10 text-accent text-[11px] font-medium">
      {parser}
    </span>
  )
}
