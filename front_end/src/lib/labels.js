// Giá trị phải khớp metadata JD trong ChromaDB (xem back_end/app/core/cv_profile.py).
export const KEYWORDS = [
  '.NET', 'Android', 'Artist', 'Block-chain', 'Business Analyst', 'C++', 'Data Analyst',
  'Data Engineer', 'Data Science', 'Design', 'DevOps', 'Flutter', 'Golang', 'HR', 'Java',
  'JavaScript', 'Lead', 'Lead Generation', 'Marketing', 'Node.js', 'Other', 'PHP',
  'Product Manager', 'Product Owner', 'Project Manager', 'Python', 'QA', 'QA Automation',
  'React', 'Recruiter', 'Ruby', 'Rust', 'SAP', 'SEO', 'SQL', 'Sales', 'Salesforce', 'Scala',
  'Scrum Master', 'Security', 'Support', 'Sysadmin', 'Technical Writing', 'Unity', 'iOS',
]

export const ENGLISH_LEVELS = [
  { value: 1, key: 'basic', label: 'Cơ bản' },
  { value: 2, key: 'pre', label: 'Sơ trung cấp' },
  { value: 3, key: 'intermediate', label: 'Trung cấp' },
  { value: 4, key: 'upper', label: 'Trên trung cấp' },
  { value: 5, key: 'fluent', label: 'Thành thạo' },
]

export const englishLabel = (key) => ENGLISH_LEVELS.find((e) => e.key === key)?.label ?? 'Không nêu'

export const expLabel = (n) => (n === 0 ? 'Chưa cần kinh nghiệm' : `${n}+ năm kinh nghiệm`)

export const QUICK_KEYWORDS = ['Python', 'React', 'Java', 'DevOps', 'QA', 'Data Analyst']
