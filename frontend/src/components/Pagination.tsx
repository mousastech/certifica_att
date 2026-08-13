import { useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useT } from '@/i18n'

/** Paginação client-side simples. Retorna a fatia da página atual + controles. */
export function usePaged<T>(items: T[], pageSize = 50) {
  const [page, setPage] = useState(1)
  const total = items.length
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  // se a lista encolher (filtro), garante página válida
  const safePage = Math.min(page, totalPages)
  const pageItems = useMemo(
    () => items.slice((safePage - 1) * pageSize, safePage * pageSize),
    [items, safePage, pageSize],
  )
  const from = total === 0 ? 0 : (safePage - 1) * pageSize + 1
  const to = Math.min(safePage * pageSize, total)
  return { page: safePage, setPage, total, totalPages, pageItems, from, to }
}

export default function Pagination({
  page, totalPages, from, to, total, onPage,
}: {
  page: number; totalPages: number; from: number; to: number; total: number
  onPage: (p: number) => void
}) {
  const t = useT()
  if (totalPages <= 1) return null
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      gap: 12, padding: '12px 14px', flexWrap: 'wrap',
    }}>
      <span className="muted" style={{ fontSize: 13 }}>
        {t('common.showing', { a: from, b: to, total })}
      </span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button className="btn" disabled={page <= 1} onClick={() => onPage(page - 1)}
          aria-label={t('common.prev')}>
          <ChevronLeft size={16} /> {t('common.prev')}
        </button>
        <span className="muted" style={{ fontSize: 13, minWidth: 90, textAlign: 'center' }}>
          {t('common.pageOf', { p: page, n: totalPages })}
        </span>
        <button className="btn" disabled={page >= totalPages} onClick={() => onPage(page + 1)}
          aria-label={t('common.next')}>
          {t('common.next')} <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}
