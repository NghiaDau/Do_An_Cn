import { useEffect, useState } from 'react'

// Chạy fn(signal) mỗi khi deps đổi; huỷ request cũ. Trả về { data, error, loading }.
export function useAsync(fn, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  useEffect(() => {
    const ctrl = new AbortController()
    setState((s) => ({ ...s, loading: true, error: null }))
    fn(ctrl.signal)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((err) => {
        if (err.name !== 'AbortError') setState({ data: null, error: err.message, loading: false })
      })
    return () => ctrl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return state
}
