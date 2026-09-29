export default function Pager({ page, limit, total, onPage }) {
  const pages = Math.max(1, Math.ceil(total / limit))
  const start = total ? (page - 1) * limit + 1 : 0
  const end = Math.min(page * limit, total)

  return (
    <div className="pager">
      <span className="info">
        Hiển thị {start}–{end} trong tổng {total} bản ghi
      </span>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        <button onClick={() => onPage(page - 1)} disabled={page <= 1}>&#8249;</button>
        <span className="info" style={{ padding: '0 8px' }}>Trang {page}/{pages}</span>
        <button onClick={() => onPage(page + 1)} disabled={page >= pages}>&#8250;</button>
      </div>
    </div>
  )
}
