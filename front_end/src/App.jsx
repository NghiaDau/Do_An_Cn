import { NavLink, Route, Routes, Link } from 'react-router-dom'
import Icon from './components/Icon.jsx'
import Home from './pages/Home.jsx'
import Search from './pages/Search.jsx'
import Browse from './pages/Browse.jsx'
import JobDetail from './pages/JobDetail.jsx'
import Cv from './pages/Cv.jsx'

const NAV = [
  { to: '/', label: 'Tổng quan', icon: 'home', end: true },
  { to: '/tim-kiem', label: 'Tìm kiếm', icon: 'search' },
  { to: '/viec-lam', label: 'Danh sách việc làm', icon: 'list', end: true },
  { to: '/cv', label: 'Phân tích CV', icon: 'file' },
]

export default function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <Link to="/" className="brand">
          <span className="brand-mark"><Icon name="search" size={14} /></span>
          Tìm việc IT
        </Link>
        <nav className="nav" aria-label="Điều hướng chính">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}>
              <Icon name={n.icon} />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <p className="sidebar-foot faint">Đồ án chuyên ngành</p>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/tim-kiem" element={<Search />} />
          <Route path="/viec-lam" element={<Browse />} />
          <Route path="/viec-lam/:id" element={<JobDetail />} />
          <Route path="/cv" element={<Cv />} />
          <Route path="*" element={<div className="page"><h1 className="h1">Không tìm thấy trang</h1><Link to="/" className="btn" style={{ alignSelf: 'flex-start' }}>Về tổng quan</Link></div>} />
        </Routes>
      </main>
    </div>
  )
}
