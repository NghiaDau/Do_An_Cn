import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import { getHealth } from '../api.js'
import { useAsync } from '../lib/useAsync.js'
import { QUICK_KEYWORDS } from '../lib/labels.js'

export default function Home() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const health = useAsync((signal) => getHealth(signal), [])

  const submit = (e) => {
    e.preventDefault()
    if (q.trim()) navigate(`/tim-kiem?q=${encodeURIComponent(q.trim())}`)
  }

  return (
    <div className="page">
      <section className="hero">
        <h1 className="display">
          Tìm việc IT theo <span className="accent-text">ý nghĩa</span>, không chỉ theo từ khóa
        </h1>
        <p className="lead">
          Mô tả công việc bạn muốn bằng câu tự nhiên, hoặc tải CV lên để hệ thống tự rút ra kỹ năng và gợi ý
          những JD phù hợp nhất.
        </p>
        <form className="searchbar" onSubmit={submit} role="search">
          <Icon name="search" size={20} className="icon-lead" />
          <input
            id="home-q"
            className="input"
            aria-label="Mô tả công việc"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Ví dụ: backend python developer, làm việc với Docker"
          />
          <button type="submit" className="btn btn-primary" disabled={!q.trim()}>Tìm kiếm</button>
        </form>
        <div className="tags" aria-label="Lĩnh vực phổ biến">
          <span className="hero-label">Phổ biến:</span>
          {QUICK_KEYWORDS.map((k) => (
            <Link key={k} className="tag" to={`/tim-kiem?q=${encodeURIComponent(k)}&keyword=${encodeURIComponent(k)}`}>
              {k}
            </Link>
          ))}
        </div>
      </section>

      <section className="entry-grid" aria-label="Chức năng chính">
        <Link to="/cv" className="entry">
          <span className="ico"><Icon name="file" size={22} /></span>
          <h2 className="h2">Phân tích CV và gợi ý việc làm</h2>
          <p className="muted">
            Tải CV dạng PDF. Hệ thống trích xuất vị trí, kinh nghiệm, tiếng Anh, kỹ năng, rồi tìm JD gần nhất.
          </p>
          <span className="go">Tải CV lên <Icon name="arrowRight" /></span>
        </Link>
        <Link to="/viec-lam" className="entry">
          <span className="ico"><Icon name="list" size={22} /></span>
          <h2 className="h2">Duyệt toàn bộ việc làm</h2>
          <p className="muted">Xem danh sách JD, lọc theo lĩnh vực và chuyển trang dễ dàng.</p>
          <span className="go">Xem danh sách <Icon name="arrowRight" /></span>
        </Link>
      </section>

      <section aria-labelledby="how">
        <h2 className="h2" id="how" style={{ marginBottom: 'var(--space-4)' }}>Cách hoạt động</h2>
        <ol className="steps">
          <li>
            <strong>Mô tả hoặc tải CV</strong>
            <span className="muted">Viết câu tự nhiên, hoặc để hệ thống đọc CV PDF và tóm tắt hồ sơ của bạn.</span>
          </li>
          <li>
            <strong>So khớp theo ngữ nghĩa</strong>
            <span className="muted">Câu của bạn được chuyển thành vector rồi so với hàng nghìn JD đã lưu.</span>
          </li>
          <li>
            <strong>Lọc theo điều kiện</strong>
            <span className="muted">Giới hạn lĩnh vực, năm kinh nghiệm và trình độ tiếng Anh ngay trong lần tìm.</span>
          </li>
        </ol>
      </section>

      <section className="stats" aria-label="Trạng thái hệ thống">
        <div className="stat">
          <b>{health.loading ? '...' : health.data ? health.data.total_jobs.toLocaleString('vi-VN') : '-'}</b>
          <span className="faint">JD đã được vector hóa</span>
        </div>
        <div className="stat">
          <span className="status-dot">
            <span
              aria-hidden="true"
              style={{
                width: 10, height: 10, borderRadius: '50%',
                background: health.data ? 'var(--color-success)' : health.error ? 'var(--color-danger)' : 'var(--color-text-faint)',
              }}
            />
            <b style={{ fontSize: 'var(--text-lg)' }}>
              {health.loading ? 'Đang kiểm tra' : health.data ? 'Backend hoạt động' : 'Backend không phản hồi'}
            </b>
          </span>
          <span className="faint">{health.error ?? (health.data ? `Bộ sưu tập ${health.data.collection}` : '')}</span>
        </div>
      </section>
    </div>
  )
}
