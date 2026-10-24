# Do_An_Cn

Backend FastAPI + ChromaDB để lưu và truy vấn Job Description (JD) đã được vector hóa.

## Cấu trúc

```
project_dacn/
├── back_end/
│   ├── app/
│   │   ├── main.py            # app FastAPI
│   │   ├── core/chroma.py     # cấu hình ChromaDB
│   │   ├── core/embedding.py  # cấu hình model embedding
│   │   ├── core/taxonomy.py   # đồ thị taxonomy IT (NetworkX) + hàm Graph Matching
│   │   ├── data/taxonomy.json # taxonomy ngành IT phân cấp (chung -> cụ thể)
│   │   └── routers/           # health.py, jobs.py, cv.py
│   ├── scripts/make_csv.py    # đổi file parquet đã tải về thành job_descriptions.csv
│   ├── scripts/embed_jd.py    # đọc CSV, embed Long Description, nạp vào ChromaDB
│   ├── data_set/job_descriptions/ # parquet tải về + job_descriptions.csv (không đưa lên git)
│   ├── chroma_db/             # dữ liệu vector (tự sinh, không đưa lên git)
│   └── requirements.txt
└── front_end/                 # giao diện React (Vite), xem mục 5
```

## Yêu cầu

- Python 3.12
- File parquet dataset đã tải về, đặt tại `back_end/data_set/job_descriptions/` (vd `train-00000-of-00001.parquet`)

## Cài đặt

Chạy trong thư mục `back_end`:

```bash
cd back_end
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

> Lần cài đầu khá lâu vì có PyTorch. Trên macOS/Linux dùng `.venv/bin/python` thay cho `.venv/Scripts/python`.

## 1. Tạo file CSV từ dataset

Chạy trong `back_end`:

```bash
.venv/Scripts/python scripts/make_csv.py
```

- Đọc file `.parquet` trong `data_set/job_descriptions/`, giữ các cột `id, Position, Company Name, Primary Keyword, Exp Years, English Level, Long Description`.
- Loại các dòng có trường bị null/rỗng và trùng `id`.
- Ghi ra `data_set/job_descriptions/job_descriptions.csv`.

## 2. Nạp dữ liệu (embed JD)

Thử với ít dòng trước:

```bash
.venv/Scripts/python scripts/embed_jd.py --limit 1000
```

Nạp nhiều hơn, hoặc toàn bộ dataset nếu bỏ `--limit`:

```bash
.venv/Scripts/python scripts/embed_jd.py --limit 10000
```

Xóa dữ liệu cũ rồi nạp lại từ đầu:

```bash
.venv/Scripts/python scripts/embed_jd.py --reset
```

- Mỗi vector được đính kèm metadata: `position, company, keyword, exp_years, english_level, english_level_num`.
- Có thể chạy lại, các JD đã nạp sẽ được bỏ qua.
- Lần chạy đầu sẽ tải model `Alibaba-NLP/gte-modernbert-base` (~600MB).
- Dữ liệu lưu tại `back_end/chroma_db/`.

## 3. Chạy API

```bash
cd back_end
python run.py
.venv/Scripts/python run.py
```

- Swagger UI: http://localhost:8000/docs
- `GET /health`: kiểm tra server và kết nối ChromaDB, trả số JD hiện có (`total_jobs`); lỗi kết nối trả 503
- `GET /jobs?page=1&page_size=10&keyword=Python`: danh sách JD phân trang (trả đủ `description`, kèm `total`, `total_pages`)
- `GET /jobs/search?q=backend python developer&page=1&page_size=10`: tìm JD theo ngữ nghĩa (vector), có `score` (cosine, càng gần 1 càng giống). Kết hợp thêm bộ lọc metadata (hybrid search):
  - `keyword`, `company`: lọc đúng giá trị
  - `min_exp`, `max_exp`: khoảng số năm kinh nghiệm
  - `min_english`, `max_english`: khoảng mức tiếng Anh (1=basic, 2=pre, 3=intermediate, 4=upper, 5=fluent)
- `GET /jobs/{job_id}`: chi tiết một JD

Model embedding được nạp khi server khởi động (trước dòng `Application startup complete`) để embed câu truy vấn của `/jobs/search`.

### Phân tích CV (PDF -> CandidateProfile)

`POST /cv/parse` nhận file PDF (form-data, trường `file`, tối đa 10MB), đọc text bằng PyMuPDF rồi gọi LLM (Groq hoặc Gemini Flash) **một lần** để trả về `CandidateProfile`. LLM bị ép chuẩn hóa theo đúng định dạng metadata của JD, nên kết quả đưa thẳng vào bộ lọc của `/jobs/search` được:

| Trường | Chuẩn hóa | Ví dụ |
|---|---|---|
| `exp_years` | số nguyên năm, làm tròn xuống | "24 months" -> `2`, "1.5 years" -> `1` |
| `english_level` | `basic` / `pre` / `intermediate` / `upper` / `fluent` (hoặc `null` nếu CV không nêu) | "IELTS 6.0" -> `intermediate` |
| `english_level_num` | tự suy ra bằng code từ `english_level` (1-5, `0` nếu không có) | `intermediate` -> `3` |
| `keyword` | một trong các Primary Keyword của JD | `Python`, `Java`, `Other`... |
| `position`, `skills`, `summary` | tiếng Anh; `summary` dùng làm câu truy vấn `q` | |

Cấu hình: sao chép `back_end/.env.example` thành `back_end/.env` rồi điền `GROQ_API_KEY` (lấy tại console.groq.com/keys) hoặc `GEMINI_API_KEY` (file `.env` không đưa lên git). Chọn nhà cung cấp bằng `LLM_PROVIDER=groq|gemini`; bỏ trống thì dùng Groq nếu có `GROQ_API_KEY`, ngược lại dùng Gemini. Đổi model bằng `GROQ_MODEL` (mặc định `openai/gpt-oss-120b`) hoặc `GEMINI_MODEL` (mặc định `gemini-2.5-flash`). Sau khi sửa `.env` phải khởi động lại server, vì `--reload` không theo dõi file `.env`.

Mã lỗi: `422` file không phải PDF hoặc PDF không có text (bản scan), `413` quá 10MB, `503` chưa đặt API key, `502` lỗi khi gọi LLM.

Code: `app/core/cv_pdf.py` (đọc PDF), `app/core/cv_profile.py` (schema `CandidateProfile`, prompt và lời gọi Gemini), `app/routers/cv.py` (endpoint).

### Taxonomy kỹ năng (Graph Matching)

`app/data/taxonomy.json` mô tả phân cấp kỹ năng/vị trí IT (vd `Blockchain -> Blockchain Node -> Masternode`). `app/core/taxonomy.py` nạp file này thành đồ thị có hướng NetworkX trong RAM và cung cấp các hàm chạy độc lập (chưa gắn vào API):

```python
from app.core.taxonomy import relation, skill_match_score, match_skills, ancestors, descendants

skill_match_score("Blockchain", "Masternode")   # 0.9  ứng viên cụ thể hơn yêu cầu -> đáp ứng
skill_match_score("Masternode", "Blockchain")   # 0.25 ứng viên chỉ biết khái niệm chung -> một phần
match_skills(["Blockchain", "Kubernetes"], ["Masternode", "Docker"])

extract_terms("Senior/Lead Backend Developer (Python)")   # ['Backend', 'Python']
```

`extract_terms(text)` tách các thuật ngữ trong taxonomy ra khỏi văn bản tự do (position, description) để đưa JD và ứng viên về cùng tập nút, rồi đưa kết quả vào `match_skills`. Nó khớp theo cụm dài nhất (`Node.js` không bị tách thành `Node` + `js`), không khớp giữa từ (`JavaScript` không cho `Java`), và với khóa ngắn/dễ nhầm (`IT`, `R`, `C`, `QA`, `Spring`...) chỉ nhận khi viết đúng dạng IN HOA hoặc Viết hoa đầu. Nó chỉ nhận đúng tên hoặc alias có trong taxonomy, không suy luận nghĩa.

Tên và alias không phân biệt hoa thường (`Block-chain` -> `Blockchain`). Trùng alias hoặc có vòng lặp sẽ báo lỗi khi nạp.

#### Dựng lại `taxonomy.json`

`taxonomy.json` được tạo bằng script, nên sửa script rồi chạy lại thay vì sửa tay file JSON (chạy sẽ **ghi đè hoàn toàn** file cũ). Từ thư mục `back_end`:

```bash
.venv/Scripts/python scripts/build_taxonomy.py
.venv/Scripts/python scripts/build_taxonomy.py --min-count 10   # chỉ giữ thuật ngữ JD xuất hiện >= 10 lần
```

Nguồn dữ liệu:

- **ESCO** (`data_set/skill_en`): các kỹ năng kiến thức (knowledge) trong `digitalSkillsCollection` nằm dưới nhóm ICT (`isced-f/06`) cùng các nhóm cha; quan hệ cha-con lấy từ `broaderRelationsSkillPillar`.
- **JD** (`job_descriptions_20k.csv`): cây thuật ngữ IT soạn tay trong `scripts/jd_tree.py` (`JD_TREE`). Chỉ giữ thuật ngữ xuất hiện trong ít nhất `--min-count` JD, trừ các nút trong `FORCE` (chuỗi Blockchain -> Blockchain Node -> Masternode). Nút trùng tên với ESCO được gộp nên đồ thị là DAG.

Thư mục `data_set/` không nằm trong git, nên cần có sẵn dữ liệu ESCO ở đó trước khi chạy script.

#### Chạy test

Test của taxonomy (cây phân cấp, chấm điểm, `extract_terms`) nằm ở `back_end/tests/test_taxonomy.py`. Điểm chấm được khóa bằng một taxonomy nhỏ dựng riêng trong test, nên đổi hệ số điểm (`SPECIALIZATION_DECAY`, `GENERALIZATION_DECAY`, `RELATED_BASE`) sẽ làm test lỗi cho đến khi cập nhật điểm kỳ vọng. Từ thư mục `back_end`:

```bash
.venv/Scripts/python -m pytest
```

## 4. Xem dữ liệu trên Chroma UI (tùy chọn)

Bật server Chroma trỏ vào thư mục dữ liệu:

```bash
cd back_end
.venv/Scripts/chroma run --path chroma_db
```

Trong UI kết nối với:

- Connection URL: `http://127.0.0.1:8000`
- Tenant: `default_tenant`
- DB Name: `default_database`

Khi dùng server Chroma, các tiến trình khác (script nạp, FastAPI) phải kết nối qua server thay vì mở thẳng thư mục. Đặt biến môi trường `CHROMA_HOST` trước khi chạy:

```powershell
$env:CHROMA_HOST="localhost"
```

Nếu chạy cùng FastAPI, đổi cổng Chroma để tránh trùng cổng 8000: `chroma run --path chroma_db --port 8001`, và đặt thêm `$env:CHROMA_PORT="8001"`.

> Không chạy script nạp và server Chroma cùng ghi vào một thư mục `chroma_db` mà không đặt `CHROMA_HOST`, vì dễ làm hỏng dữ liệu.

## 5. Giao diện web (front_end)

Giao diện React (Vite) cho các API ở trên, viết bằng tiếng Việt, kiểu Linear sáng kết hợp Notion. Cần Node.js 20 trở lên.

### Chạy

Bật backend ở cổng 8000 trước (xem mục chạy API), rồi từ thư mục `front_end`:

```bash
npm install
npm run dev        # http://localhost:5173
```

Khi chạy dev, mọi lời gọi `/api/*` được proxy sang `http://localhost:8000` (cấu hình trong `vite.config.js`), nên không cần bật CORS thêm. Backend ở địa chỉ khác thì đặt `VITE_PROXY_TARGET`:

```powershell
$env:VITE_PROXY_TARGET="http://localhost:8001"
npm run dev
```

Các lệnh khác:

```bash
npm run build      # build ra front_end/dist
npm run preview    # xem thử bản build
npm run lint       # oxlint
```

Khi triển khai bản build, đặt `VITE_API_URL` là địa chỉ đầy đủ của API (mặc định `/api`) trước khi `npm run build`.

### Các màn hình

| Đường dẫn | Màn hình | API dùng |
|---|---|---|
| `/` | Tổng quan: ô tìm nhanh, tình trạng backend | `GET /health` |
| `/tim-kiem` | Tìm theo ngữ nghĩa kết hợp lọc lĩnh vực, công ty, kinh nghiệm, tiếng Anh | `GET /jobs/search` |
| `/viec-lam` | Duyệt toàn bộ JD, lọc lĩnh vực, phân trang | `GET /jobs` |
| `/viec-lam/:id` | Chi tiết một JD | `GET /jobs/{id}` |
| `/cv` | Tải CV PDF, xem hồ sơ trích xuất và JD gợi ý (3 bộ lọc bật/tắt) | `POST /cv/parse`, `GET /jobs/search` |

Phân tích CV cần cấu hình LLM trong `back_end/.env` (`GROQ_API_KEY` hoặc `GEMINI_API_KEY`). Dữ liệu JD bằng tiếng Anh nên câu tìm kiếm cũng nên viết tiếng Anh, ví dụ `backend developer with Python and FastAPI`.

### Cấu trúc

```
front_end/src/
  api.js            gọi backend (một chỗ duy nhất)
  App.jsx           khung ứng dụng và định tuyến
  index.css         toàn bộ token màu, cỡ chữ, khoảng cách và style
  pages/            Home, Search, Browse, JobDetail, Cv
  components/       JobRow, Avatar, Icon, States (lỗi, trống, skeleton)
  lib/              labels.js (giá trị metadata JD), useAsync.js
```

Danh sách lĩnh vực và mức tiếng Anh trong `lib/labels.js` phải khớp metadata JD trong ChromaDB (`back_end/app/core/cv_profile.py`). Đổi bên backend thì cập nhật cả hai.
