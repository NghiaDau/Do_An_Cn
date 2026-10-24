// Icon nét mảnh (kiểu lucide) dùng currentColor, không dùng emoji.
const PATHS = {
  home: 'M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z',
  search: 'm21 21-4.3-4.3M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15z',
  list: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  file: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M9 13h6M9 17h6',
  upload: 'M12 16V4m0 0L7 9m5-5 5 5M4 20h16',
  arrowLeft: 'M19 12H5m0 0 6-6m-6 6 6 6',
  arrowRight: 'M5 12h14m0 0-6-6m6 6-6 6',
  alert: 'M12 9v4m0 4h.01M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z',
  loader: 'M12 2v4m0 12v4M4.9 4.9l2.8 2.8m8.6 8.6 2.8 2.8M2 12h4m12 0h4M4.9 19.1l2.8-2.8m8.6-8.6 2.8-2.8',
  inbox: 'M22 12h-6l-2 3h-4l-2-3H2m20 0-3.5-7.1A2 2 0 0 0 16.7 4H7.3a2 2 0 0 0-1.8.9L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2z',
}

export default function Icon({ name, size = 16, className }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={PATHS[name]} />
    </svg>
  )
}
