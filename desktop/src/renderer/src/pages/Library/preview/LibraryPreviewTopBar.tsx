import { ArrowLeft, ArrowRight, Download, Loader2, Trash2 } from 'lucide-react'

interface LibraryPreviewTopBarProps {
  onBack: () => void
  onReview: () => void
  onExport: () => void
  onDelete: () => void
  onCancelDelete: () => void
  isExporting: boolean
  isConfirmingDelete: boolean
  isDeleting: boolean
  disabled: boolean
}

export default function LibraryPreviewTopBar({
  onBack,
  onReview,
  onExport,
  onDelete,
  onCancelDelete,
  isExporting,
  isConfirmingDelete,
  isDeleting,
  disabled,
}: LibraryPreviewTopBarProps): JSX.Element {
  return (
    <div className="flex items-center justify-between gap-3 mb-5">
      <button
        type="button"
        onClick={onBack}
        className="btn-ghost px-2.5 py-1.5 text-sm"
      >
        <ArrowLeft size={14} />
        Library
      </button>

      <div className="flex items-center gap-2">
        {isConfirmingDelete ? (
          <>
            <button
              type="button"
              onClick={onDelete}
              disabled={isDeleting}
              className="btn-ghost px-2.5 py-1.5 text-xs text-danger hover:bg-danger/10"
            >
              {isDeleting ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Trash2 size={12} />
              )}
              Confirm delete
            </button>
            <button
              type="button"
              onClick={onCancelDelete}
              disabled={isDeleting}
              className="btn-ghost px-2.5 py-1.5 text-xs"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              onClick={onExport}
              disabled={disabled || isExporting}
              className="btn-ghost px-2.5 py-1.5 text-xs text-ink-secondary hover:text-ink"
              title="Export normalized markdown"
            >
              {isExporting ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Download size={12} />
              )}
              Export
            </button>
            <button
              type="button"
              onClick={onReview}
              disabled={disabled}
              className="btn-ghost px-2.5 py-1.5 text-xs text-accent hover:bg-accent/10"
              title="Start review using this parse"
            >
              Review
              <ArrowRight size={12} />
            </button>
            <button
              type="button"
              onClick={onDelete}
              disabled={disabled}
              className="btn-ghost px-2 py-1.5 text-xs text-ink-tertiary hover:text-danger"
              title="Delete"
            >
              <Trash2 size={12} />
            </button>
          </>
        )}
      </div>
    </div>
  )
}
