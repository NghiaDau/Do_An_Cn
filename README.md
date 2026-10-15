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
│   ├── scripts/embed_jd.py    # đọc CSV, embed Long Description, nạp vào ChromaDB
│   ├── chroma_db/             # dữ liệu vector (tự sinh, không đưa lên git)
│   └── requirements.txt
└── data_set/job_descriptions/ # dataset CSV (không đưa lên git)
```

## Yêu cầu

- Python 3.12
- File dữ liệu `data_set/job_descriptions/job_descriptions_clean.csv`

## Cài đặt

Chạy trong thư mục `back_end`:

```bash
cd back_end
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

> Lần cài đầu khá lâu vì có PyTorch. Trên macOS/Linux dùng `.venv/bin/python` thay cho `.venv/Scripts/python`.

## 1. Nạp dữ liệu (embed JD)

Thử với ít dòng trước:

```bash
.venv/Scripts/python scripts/embed_jd.py --limit 1000
```

Nạp nhiều hơn, hoặc toàn bộ dataset nếu bỏ `--limit`:

```bash
.venv/Scripts/python scripts/embed_jd.py --limit 10000
```

- Có thể chạy lại, các JD đã nạp sẽ được bỏ qua.
- Lần chạy đầu sẽ tải model `BAAI/bge-small-en-v1.5` (~130MB).
- Dữ liệu lưu tại `back_end/chroma_db/`.

## 2. Chạy API

```bash
cd back_end
.venv/Scripts/python -m uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- `GET /health`: kiểm tra server
- `GET /jobs?limit=10&offset=0&keyword=Python&full=false`: danh sách JD
- `GET /jobs/{job_id}`: chi tiết một JD

## 3. Xem dữ liệu trên Chroma UI (tùy chọn)

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
