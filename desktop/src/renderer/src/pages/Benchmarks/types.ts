export interface ParserAvailability {
  key: string
  family: string
  requires_format: 'tex' | 'pdf'
  available: boolean
  skip_reason: string | null
}

export interface BenchmarkCellMetrics {
  markdown_length: number
  extracted_title: string
  extracted_authors: string[]
  extracted_abstract_prefix: string
  heading_count: number
  inline_math_count: number
  display_math_count: number
  leftover_latex_commands: string[]
  dirty_heading_titles: string[]
  title_match_ratio: number | null
  title_match_ok: boolean | null
  authors_f1: number | null
  authors_match_ok: boolean | null
  abstract_overlap_ratio: number | null
  abstract_overlap_ok: boolean | null
  has_math: boolean
  clean_heading_titles: boolean
  no_leftover_commands: boolean
}

export interface BenchmarkCell {
  paper_id: string
  parser_key: string
  requires_format: 'tex' | 'pdf'
  success: boolean
  duration_seconds: number
  error_kind: string | null
  error_message: string | null
  metrics: BenchmarkCellMetrics | null
  artifact_path: string | null
}

export interface BenchmarkRunState {
  run_id: string
  status: 'running' | 'succeeded' | 'failed'
  config: {
    parsers: string[]
    limit: number
    paper_ids: string[] | null
    skip_ground_truth: boolean
    no_pdf_download: boolean
    timeout_seconds: number
    fixtures_root: string
    ground_truth_dir: string
  }
  started_at: string
  finished_at: string | null
  output_dir: string
  adapter_keys: string[]
  paper_ids: string[]
  total_cells: number
  completed_cells: number
  current_paper_id: string | null
  current_parser_key: string | null
  current_cell_started_at: string | null
  cells: BenchmarkCell[]
  leaderboard_markdown: string
  per_paper_markdown: string
  error: string | null
}

export interface BenchmarkConfigDraft {
  parserKeys: string[]
  limit: number
  skipGroundTruth: boolean
  noPdfDownload: boolean
}
