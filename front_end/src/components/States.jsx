import Icon from './Icon.jsx'

export function ErrorNotice({ message, onRetry }) {
  return (
    <div className="notice notice-error" role="alert">
      <Icon name="alert" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', alignItems: 'flex-start' }}>
        <span>{message}</span>
        {onRetry && (
          <button type="button" className="btn" onClick={onRetry}>
            Thử lại
          </button>
        )}
      </div>
    </div>
  )
}

export function Empty({ title, hint, children }) {
  return (
    <div className="empty">
      <Icon name="inbox" size={28} />
      <p style={{ color: 'var(--color-text)', fontWeight: 500 }}>{title}</p>
      {hint && <p className="faint">{hint}</p>}
      {children}
    </div>
  )
}

export function SkeletonRows({ count = 5 }) {
  return (
    <div role="status" aria-label="Đang tải">
      {Array.from({ length: count }, (_, i) => (
        <div className="skeleton-row" key={i}>
          <div className="skeleton" style={{ height: 16, width: '45%' }} />
          <div className="skeleton" style={{ height: 12, width: '25%' }} />
          <div className="skeleton" style={{ height: 12, width: '80%' }} />
        </div>
      ))}
    </div>
  )
}
