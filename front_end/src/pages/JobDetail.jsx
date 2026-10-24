import { Link, useNavigate, useParams } from 'react-router-dom'
import Avatar from '../components/Avatar.jsx'
import Icon from '../components/Icon.jsx'
import { ErrorNotice } from '../components/States.jsx'
import { getJob } from '../api.js'
import { useAsync } from '../lib/useAsync.js'
import { englishLabel, expLabel } from '../lib/labels.js'

export default function JobDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: job, error, loading } = useAsync((signal) => getJob(id, signal), [id])

  return (
    <div className="page">
      <article className="doc">
        <button type="button" className="btn btn-ghost back" onClick={() => navigate(-1)}>
          <Icon name="arrowLeft" /> Quay lại
        </button>

        {loading && (
          <div role="status" aria-label="Đang tải" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div className="skeleton" style={{ height: 40, width: '70%' }} />
            <div className="skeleton" style={{ height: 16, width: '30%' }} />
            <div className="skeleton" style={{ height: 160 }} />
          </div>
        )}

        {error && <ErrorNotice message={error} />}

        {job && (
          <>
            <header className="doc-head">
              <Avatar name={job.company} large />
              <div className="page-head">
                <h1 className="doc-title">{job.position}</h1>
                <p className="muted">{job.company}</p>
              </div>
            </header>

            <dl className="props">
              <dt>Lĩnh vực</dt>
              <dd><Link className="tag tag-accent" to={`/viec-lam?keyword=${encodeURIComponent(job.keyword)}`}>{job.keyword}</Link></dd>
              <dt>Kinh nghiệm</dt>
              <dd>{expLabel(job.exp_years)}</dd>
              <dt>Tiếng Anh</dt>
              <dd>{englishLabel(job.english_level)}</dd>
              <dt>Mã JD</dt>
              <dd className="mono">{job.id}</dd>
            </dl>

            <section>
              <h2 className="h2" style={{ marginBottom: 'var(--space-3)' }}>Mô tả công việc</h2>
              <div className="prose">{job.description}</div>
            </section>

            <div>
              <Link
                className="btn"
                to={`/tim-kiem?q=${encodeURIComponent(`${job.position} ${job.keyword}`)}&keyword=${encodeURIComponent(job.keyword)}`}
              >
                Xem việc tương tự
              </Link>
            </div>
          </>
        )}
      </article>
    </div>
  )
}
