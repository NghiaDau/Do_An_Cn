// Avatar chữ cái đầu của công ty; màu chọn ổn định theo tên (6 cặp token av-0..av-5).
function hash(s) {
  let h = 0
  for (const ch of s) h = (h * 31 + ch.codePointAt(0)) >>> 0
  return h
}

export default function Avatar({ name = '', large = false }) {
  const words = name.trim().split(/\s+/).filter(Boolean)
  const initials = (words.length > 1 ? words[0][0] + words[1][0] : (words[0] ?? '?').slice(0, 2)).toUpperCase()
  return (
    <span className={`av av-${hash(name) % 6}${large ? ' av-lg' : ''}`} aria-hidden="true">
      {initials}
    </span>
  )
}
