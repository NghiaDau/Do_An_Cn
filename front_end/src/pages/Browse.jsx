import { useSearchParams } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import JobRow from '../components/JobRow.jsx'
import { Empty, ErrorNotice, SkeletonRows } from '../components/States.jsx'
import { listJobs } from '../api.js'
import { useAsync } from '../lib/useAsync.js'
import { KEYWORDS } from '../lib/labels.js'

const PAGE_SIZE = 15

export default function Browse() {
  const [params, setParams] = useSearchParams()
  const keyword = params.get('keyword') ?? ''
  const page = Math.max(1, Number(params.get('page')) || 1)

  const { data, error, loading } = useAsync(
    (signal) => listJobs({ limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE, keyword }, signal),
    [keyword, page],
  )

  const update = (next) => {
    const p = new URLSearchParams(params)
    for (const [k, v] of Object.entries(next)) {
      if (v) p.set(k, v)
      else p.delete(k)
    }
    setParams(p)
  }

  const from = data ? (page - 1) * PAGE_SIZE + 1 : 0
  const to = data ? (page - 1) * PAGE_SIZE + data.items.length : 0
  const hasNext = data ? data.items.length === PAGE_SIZE : false

  return (
    <div className="page">
      <header className="page-head">
        <h1 className="h1">Danh sách việc làm</h1>
        <p className="muted">Duyệt toàn bộ JD đã nạp vào hệ thống.</p>
      </header>

      <div className="field" style={{ maxWidth: 280 }}>
        <label htmlFor="b-keyword">Lĩnh vực</label>
        <select id="b-keyword" className="select" value={keyword} onChange={(e) => update({ keyword: e.target.value, page: '' })}>
          <option value="">Tất cả</option>
          {KEYWORDS.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
      </div>

      <section className="list" aria-live="polite">
        {loading ? (
          <SkeletonRows count={6} />
        ) : error ? (
          <div style={{ padding: 'var(--space-4)' }}><ErrorNotice message={error} onRetry={() => update({})} /></div>
        ) : data.items.length === 0 ? (
          <Empty title="Không có JD nào" hint="Thử chọn lĩnh vực khác." />
        ) : (
          <>
            <div className="list-head">
              <span>Hiển thị {from}-{to}{!keyword && ` trong ${data.total.toLocaleString('vi-VN')} JD`}</span>
            </div>
            {data.items.map((job) => <JobRow key={job.id} job={job} />)}
            <div className="pager">
              <span>Trang {page}</span>
              <div className="pager-actions">
                <button type="button" className="btn" disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}>
                  <Icon name="arrowLeft" /> Trước
                </button>
                <button type="button" className="btn" disabled={!hasNext} onClick={() => update({ page: String(page + 1) })}>
                  Sau <Icon name="arrowRight" />
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  )
}
