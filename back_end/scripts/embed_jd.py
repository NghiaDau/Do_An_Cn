"""Đọc dataset JD, embed trường 'Long Description' và nạp vào ChromaDB.

Chạy (từ thư mục back_end):
    python scripts/embed_jd.py --limit 10000
    python scripts/embed_jd.py            # toàn bộ dataset

Có thể chạy lại: các id đã nạp sẽ được bỏ qua (resume).
"""
import argparse
from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.chroma import get_collection  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data_set" / "job_descriptions" / "job_descriptions_clean.csv"

MODEL_NAME = "all-MiniLM-L6-v2"
MAX_CHARS = 2000  # model chỉ đọc ~256 token, cắt bớt cho nhanh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(CSV_PATH))
    ap.add_argument("--limit", type=int, default=None, help="số JD tối đa cần nạp")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--chunksize", type=int, default=5000, help="số dòng đọc mỗi lần")
    args = ap.parse_args()

    model = SentenceTransformer(MODEL_NAME)
    col = get_collection()

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
            texts = part["Long Description"].astype(str).str.slice(0, MAX_CHARS).tolist()
            vectors = model.encode(texts, normalize_embeddings=True).tolist()
            col.add(
                ids=part["id"].tolist(),
                embeddings=vectors,
                documents=texts,
                metadatas=[
                    {
                        "position": str(r["Position"]),
                        "company": str(r["Company Name"]),
                        "exp_years": str(r["Exp Years"]),
                        "keyword": str(r["Primary Keyword"]),
                    }
                    for _, r in part.iterrows()
                ],
            )
        print(f"Đã nạp {done} JD, tổng trong DB: {col.count()}")

    print("Xong. Tổng:", col.count())


if __name__ == "__main__":
    main()
