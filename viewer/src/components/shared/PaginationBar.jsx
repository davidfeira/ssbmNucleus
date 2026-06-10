/**
 * PaginationBar - footer controls for a paginated card list.
 * Renders nothing when everything fits on one page.
 * Takes the object returned by usePagination as `pager`.
 */
import { playSound, playHoverSound } from '../../utils/sounds'

export default function PaginationBar({ pager }) {
  const { page, pageCount, start, end, totalItems, setPage } = pager
  if (pageCount <= 1) return null

  const go = (p) => {
    const next = Math.max(0, Math.min(pageCount - 1, p))
    if (next !== page) {
      playSound('boop')
      setPage(next)
    }
  }

  return (
    <div className="pagination-bar">
      <button
        className="pagination-btn"
        onMouseEnter={playHoverSound}
        onClick={() => go(0)}
        disabled={page === 0}
        title="First page"
      >
        «
      </button>
      <button
        className="pagination-btn"
        onMouseEnter={playHoverSound}
        onClick={() => go(page - 1)}
        disabled={page === 0}
        title="Previous page"
      >
        ‹
      </button>
      <span className="pagination-info">
        {start + 1}–{end} of {totalItems}
      </span>
      <button
        className="pagination-btn"
        onMouseEnter={playHoverSound}
        onClick={() => go(page + 1)}
        disabled={page >= pageCount - 1}
        title="Next page"
      >
        ›
      </button>
      <button
        className="pagination-btn"
        onMouseEnter={playHoverSound}
        onClick={() => go(pageCount - 1)}
        disabled={page >= pageCount - 1}
        title="Last page"
      >
        »
      </button>
    </div>
  )
}
