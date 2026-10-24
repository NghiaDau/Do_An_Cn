import { useRef, useState } from 'react'
import Icon from '../components/Icon.jsx'
import JobRow from '../components/JobRow.jsx'
import { Empty, ErrorNotice, SkeletonRows } from '../components/States.jsx'
import { parseCv, searchJobs } from '../api.js'
import { useAsync } from '../lib/useAsync.js'
import { englishLabel, expLabel } from '../lib/labels.js'

const MAX_BYTES = 10 * 1024 * 1024

export default function Cv() {
  const inputRef = useRef(null)
  const [over, setOver] = useState(false)
  const [file, setFile] = useState(null)
  const [fileError, setFileError] = useState('')
  const [parsing, setParsing] = useState(false)
  const [parseError, setParseError] = useState('')
  const [profile, setProfile] = useState(null)
  const [useKeyword, setUseKeyword] = useState(true)
  const [useExp, setUseExp] = useState(true)
  const [useEnglish, setUseEnglish] = useState(false)

  const pick = (f) => {
    setFileError('')
    if (!f) return
    if (f.type !== 'application/pdf' && !f.name.toLowerCase().endsWith('.pdf')) {
      setFileError('Chỉ nhận file PDF.')
      return
    }
    if (f.size > MAX_BYTES) {
      setFileError('File vượt quá 10MB.')
      return
    }
    setFile(f)
  }

  const analyze = async () => {
    setParsing(true)
    setParseError('')
    try {
      setProfile(await parseCv(file))
    } catch (e) {
      setParseError(e.message)
      setProfile(null)
    } finally {
      setParsing(false)
    }
  }

  const matchKey = profile ? JSON.stringify([profile, useKeyword, useExp, useEnglish]) : ''
  const matches = useAsync(
    (signal) => {
      if (!profile) return Promise.resolve(null)
      const params = { q: profile.summary || profile.position, limit: 20 }
      if (useKeyword) params.keyword = profile.keyword
      if (useExp) params.max_exp = profile.exp_years + 1
      if (useEnglish && profile.english_level_num > 0) params.max_english = profile.english_level_num
      return searchJobs(params, signal)
    },
    [matchKey],
  )

  const reset = () => {
    setFile(null)
    setProfile(null)
    setParseError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="page">
      <header className="page-head">
        <h1 className="h1">Phân tích CV</h1>
        <p className="muted">Tải CV PDF để trích xuất hồ sơ và tìm các JD phù hợp. CV chỉ dùng cho lần phân tích này.</p>
      </header>

      <div className={`cv-layout${profile ? ' has-result' : ''}`}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <label
            className={`dropzone${over ? ' is-over' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setOver(true) }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => { e.preventDefault(); setOver(false); pick(e.dataTransfer.files[0]) }}
          >
            <span className="drop-ico"><Icon name="upload" size={24} /></span>
            <span style={{ fontWeight: 500 }}>{file ? file.name : 'Kéo thả CV vào đây hoặc bấm để chọn'}</span>
            <span className="faint">{file ? `${(file.size / 1024).toFixed(0)} KB` : 'PDF, tối đa 10MB'}</span>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="sr-only"
              style={{ position: 'absolute', width: 1, height: 1, opacity: 0 }}
              onChange={(e) => pick(e.target.files[0])}
            />
          </label>

          {fileError && <ErrorNotice message={fileError} />}
          {parseError && <ErrorNotice message={parseError} onRetry={file ? analyze : undefined} />}

          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button type="button" className="btn btn-primary" disabled={!file || parsing} onClick={analyze}>
              {parsing && <Icon name="loader" className="spin" />}
              {parsing ? 'Đang phân tích' : 'Phân tích CV'}
            </button>
            {(file || profile) && !parsing && (
              <button type="button" className="btn btn-ghost" onClick={reset}>Chọn CV khác</button>
            )}
          </div>

          {profile && (
            <section className="panel" aria-label="Hồ sơ trích xuất">
              <div>
                <p className="panel-title">Vị trí</p>
                <p className="profile-name">{profile.position}</p>
              </div>
              <div className="tags">
                <span className="tag tag-accent">{profile.keyword}</span>
                <span className="tag">{expLabel(profile.exp_years)}</span>
                <span className="tag">Tiếng Anh: {englishLabel(profile.english_level)}</span>
              </div>
              <div>
                <p className="panel-title" style={{ marginBottom: 'var(--space-2)' }}>Kỹ năng ({profile.skills.length})</p>
                <div className="tags">
                  {profile.skills.map((s) => <span key={s} className="tag tag-accent">{s}</span>)}
                </div>
              </div>
              <div>
                <p className="panel-title">Tóm tắt (dùng làm câu truy vấn)</p>
                <p className="muted">{profile.summary}</p>
              </div>
            </section>
          )}
        </div>

        {profile && (
          <section style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }} aria-live="polite">
            <div className="filter-card">
              <span className="panel-title">Bộ lọc gợi ý</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', columnGap: 'var(--space-5)' }}>
                <label className="check">
                  <input type="checkbox" checked={useKeyword} onChange={(e) => setUseKeyword(e.target.checked)} />
                  Cùng lĩnh vực ({profile.keyword})
                </label>
                <label className="check">
                  <input type="checkbox" checked={useExp} onChange={(e) => setUseExp(e.target.checked)} />
                  Yêu cầu kinh nghiệm tối đa {profile.exp_years + 1} năm
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={useEnglish}
                    disabled={!profile.english_level_num}
                    onChange={(e) => setUseEnglish(e.target.checked)}
                  />
                  Tiếng Anh không vượt mức của bạn
                </label>
              </div>
            </div>

            {matches.error ? (
              <ErrorNotice message={matches.error} />
            ) : matches.loading || !matches.data ? (
              <div className="list"><SkeletonRows /></div>
            ) : (
              <div className="list">
                <div className="list-head"><span>{matches.data.count} việc làm phù hợp</span></div>
                {matches.data.items.length === 0 ? (
                  <Empty title="Chưa có JD khớp" hint="Bỏ bớt bộ lọc phía trên để mở rộng kết quả." />
                ) : (
                  matches.data.items.map((job) => <JobRow key={job.id} job={job} />)
                )}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  )
}
