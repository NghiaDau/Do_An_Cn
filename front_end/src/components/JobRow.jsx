import { Link } from 'react-router-dom'
import Avatar from './Avatar.jsx'
import { englishLabel, expLabel } from '../lib/labels.js'

// JD gốc có ký hiệu markdown (** và #); bỏ đi để đoạn trích dễ đọc.
const plain = (s) => s.replace(/[*#_`]+/g, '').replace(/\s+/g, ' ').trim()

export default function JobRow({ job }) {
  const pct = typeof job.score === 'number' ? Math.round(job.score * 100) : null
  return (
    <Link className="row" to={`/viec-lam/${encodeURIComponent(job.id)}`}>
      <Avatar name={job.company} />
      <div className="row-main">
        <span className="row-title">{job.position}</span>
        <span className="row-company">{job.company}</span>
        <p className="row-snippet">{plain(job.description)}</p>
      </div>
      <div className="row-side">
        {pct !== null && (
          <>
            <span className="score" title="Độ tương đồng ngữ nghĩa">{pct}%</span>
            <span className="score-bar" aria-hidden="true"><i style={{ width: `${pct}%` }} /></span>
          </>
        )}
      </div>
      <div className="row-meta tags">
        <span className="tag tag-accent">{job.keyword}</span>
        <span className="tag">{expLabel(job.exp_years)}</span>
        <span className="tag">Tiếng Anh: {englishLabel(job.english_level)}</span>
      </div>
    </Link>
  )
}
