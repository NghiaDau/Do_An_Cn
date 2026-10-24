import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import JobRow from '../components/JobRow.jsx'
import { Empty, ErrorNotice, SkeletonRows } from '../components/States.jsx'
import { searchJobs } from '../api.js'
import { useAsync } from '../lib/useAsync.js'
import { ENGLISH_LEVELS, KEYWORDS } from '../lib/labels.js'

const FIELDS = ['q', 'keyword', 'company', 'min_exp', 'max_exp', 'min_english', 'max_english', 'limit']

export default function Search() {
  const [params, setParams] = useSearchParams()
  const applied = Object.fromEntries(FIELDS.map((f) => [f, params.get(f) ?? '']))
  const [draft, setDraft] = useState(applied)
  const set = (k) => (e) => setDraft((d) => ({ ...d, [k]: e.target.value }))

  const hasQuery = applied.q.trim() !== ''
  const key = params.toString()
  const { data, error, loading } = useAsync(
    (signal) => (hasQuery ? searchJobs({ ...applied, limit: applied.limit || 20 }, signal) : Promise.resolve(null)),
    [key],
  )

  const submit = (e) => {
    e.preventDefault()
    const next = {}
    for (const [k, v] of Object.entries(draft)) if (String(v).trim() !== '') next[k] = String(v).trim()
    setParams(next)
  }
  const reset = () => {
    const blank = Object.fromEntries(FIELDS.map((f) => [f, '']))
    setDraft(blank)
    setParams({})
  }

  return (
    <div className="page">
      <header className="page-head">
        <h1 className="h1">Tìm kiếm việc làm</h1>
        <p className="muted">Tìm theo ngữ nghĩa kết hợp bộ lọc. Kết quả xếp theo độ tương đồng với câu truy vấn.</p>
      </header>

      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }} role="search">
        <div className="searchbar">
          <Icon name="search" size={18} className="icon-lead" />
          <input
            className="input"
            aria-label="Câu truy vấn"
            value={draft.q}
            onChange={set('q')}
            placeholder="Ví dụ: frontend react developer, có kinh nghiệm TypeScript"
          />
          <button type="submit" className="btn btn-primary" disabled={!draft.q.trim()}>Tìm</button>
        </div>

        <div className="filters">
          <div className="field">
            <label htmlFor="f-keyword">Lĩnh vực</label>
            <select id="f-keyword" className="select" value={draft.keyword} onChange={set('keyword')}>
              <option value="">Tất cả</option>
              {KEYWORDS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="f-company">Công ty</label>
            <input id="f-company" className="input" value={draft.company} onChange={set('company')} placeholder="Tên chính xác" />
          </div>
          <div className="field">
            <label htmlFor="f-minexp">Kinh nghiệm từ (năm)</label>
            <input id="f-minexp" className="input" type="number" min="0" value={draft.min_exp} onChange={set('min_exp')} />
          </div>
          <div className="field">
            <label htmlFor="f-maxexp">Kinh nghiệm đến (năm)</label>
            <input id="f-maxexp" className="input" type="number" min="0" value={draft.max_exp} onChange={set('max_exp')} />
          </div>
          <div className="field">
            <label htmlFor="f-minen">Tiếng Anh tối thiểu</label>
            <select id="f-minen" className="select" value={draft.min_english} onChange={set('min_english')}>
              <option value="">Không giới hạn</option>
              {ENGLISH_LEVELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="f-maxen">Tiếng Anh tối đa</label>
            <select id="f-maxen" className="select" value={draft.max_english} onChange={set('max_english')}>
              <option value="">Không giới hạn</option>
              {ENGLISH_LEVELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="f-limit">Số kết quả</label>
            <select id="f-limit" className="select" value={draft.limit || '20'} onChange={set('limit')}>
              {[10, 20, 50, 100].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <div className="field" style={{ justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-ghost" onClick={reset}>Xóa bộ lọc</button>
          </div>
        </div>
      </form>

      <section aria-live="polite">
        {!hasQuery ? (
          <div className="list"><Empty title="Nhập câu truy vấn để bắt đầu" hint="Càng mô tả cụ thể, kết quả càng sát." /></div>
        ) : error ? (
          <ErrorNotice message={error} onRetry={() => setParams(new URLSearchParams(params))} />
        ) : loading || !data ? (
          <div className="list"><SkeletonRows /></div>
        ) : (
          <div className="list">
            <div className="list-head"><span>{data.count} kết quả cho "{data.query}"</span></div>
            {data.items.length === 0 ? (
              <Empty title="Không có JD nào khớp" hint="Thử nới lỏng bộ lọc kinh nghiệm hoặc tiếng Anh." />
            ) : (
              data.items.map((job) => <JobRow key={job.id} job={job} />)
            )}
          </div>
        )}
      </section>
    </div>
  )
}
