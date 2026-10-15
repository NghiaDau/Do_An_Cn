"""Đọc dataset JD, embed trường 'Long Description' và nạp vào ChromaDB.

Chạy (từ thư mục back_end):
    python scripts/embed_jd.py --limit 10000
    python scripts/embed_jd.py            # toàn bộ dataset

Có thể chạy lại: các id đã nạp sẽ được bỏ qua (resume).
"""
import argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.chroma import get_collection, reset_collection  # noqa: E402
from app.core.embedding import DOC_PREFIX, load_model  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data_set" / "job_descriptions" / "job_descriptions_clean.csv"



ENGLISH_LEVELS = {"basic": 1, "pre": 2, "intermediate": 3, "upper": 4, "fluent": 5}


def parse_exp_years(value):
    """'3y' -> 3, 'no_exp' -> 0."""
    digits = "".join(c for c in str(value) if c.isdigit())
    return int(digits) if digits else 0


def build_metadata(row):
    """Trường tĩnh đính kèm vector: dạng chữ để hiển thị, dạng số để lọc theo khoảng."""
    level = str(row["English Level"]).strip().lower()
    return {
        "position": str(row["Position"]),
        "company": str(row["Company Name"]),
        "keyword": str(row["Primary Keyword"]),
        "exp_years": parse_exp_years(row["Exp Years"]),
        "english_level": level,
        "english_level_num": ENGLISH_LEVELS.get(level, 0),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(CSV_PATH))
    ap.add_argument("--limit", type=int, default=None, help="số JD tối đa cần nạp")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--reset", action="store_true", help="xóa collection cũ rồi nạp lại")
    ap.add_argument("--chunksize", type=int, default=5000, help="số dòng đọc mỗi lần")
    args = ap.parse_args()

    model = load_model()
    col = reset_collection() if args.reset else get_collection()

    done = 0
    reader = pd.read_csv(args.csv, chunksize=args.chunksize)
    for chunk in reader:
        if args.limit is not None and done >= args.limit:
            break
        if args.limit is not None:
            chunk = chunk.head(args.limit - done)

        chunk = chunk.dropna(subset=["id", "Long Description"])
        chunk = chunk.drop_duplicates(subset="id")

        # bỏ qua id đã có trong DB
        existing = set(col.get(ids=chunk["id"].tolist(), include=[])["ids"])
        chunk = chunk[~chunk["id"].isin(existing)]
        done += len(chunk)
        if chunk.empty:
            continue

        for start in tqdm(range(0, len(chunk), args.batch), desc="embed", leave=False):
            part = chunk.iloc[start:start + args.batch]
            texts = part["Long Description"].astype(str).tolist()
            vectors = model.encode(
                [DOC_PREFIX + t for t in texts], normalize_embeddings=True
            ).tolist()
            col.add(
                ids=part["id"].tolist(),
                embeddings=vectors,
                documents=texts,
                metadatas=[build_metadata(r) for _, r in part.iterrows()],
            )
        print(f"Đã nạp {done} JD, tổng trong DB: {col.count()}")

    print("Xong. Tổng:", col.count())


if __name__ == "__main__":
    main()
