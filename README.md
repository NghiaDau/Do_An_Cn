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
│   │   └── routers/           # health.py, jobs.py
│   ├── scripts/make_csv.py    # đổi file parquet đã tải về thành job_descriptions.csv
│   ├── scripts/embed_jd.py    # đọc CSV, embed Long Description, nạp vào ChromaDB
│   ├── data_set/job_descriptions/ # parquet tải về + job_descriptions.csv (không đưa lên git)
│   ├── chroma_db/             # dữ liệu vector (tự sinh, không đưa lên git)
│   └── requirements.txt
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
- `GET /jobs?limit=10&offset=0&keyword=Python`: danh sách JD (trả đủ `description`)
- `GET /jobs/search?q=backend python developer&limit=10`: tìm JD theo ngữ nghĩa (vector), có `score` (cosine, càng gần 1 càng giống). Kết hợp thêm bộ lọc metadata (hybrid search):
  - `keyword`, `company`: lọc đúng giá trị
  - `min_exp`, `max_exp`: khoảng số năm kinh nghiệm
  - `min_english`, `max_english`: khoảng mức tiếng Anh (1=basic, 2=pre, 3=intermediate, 4=upper, 5=fluent)
- `GET /jobs/{job_id}`: chi tiết một JD

Model embedding được nạp khi server khởi động (trước dòng `Application startup complete`) để embed câu truy vấn của `/jobs/search`.

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
