"""Đọc dataset JD, embed trường 'Long Description' và nạp vào ChromaDB.

Chạy (từ thư mục back_end):
    python scripts/embed_jd.py --limit 10000
    python scripts/embed_jd.py            # toàn bộ dataset

Có thể chạy lại: các id đã nạp sẽ được bỏ qua (resume).
Mỗi lần chạy ghi log vào logs/embed_<thời gian>.log (đồng thời in ra màn hình).
"""
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.chroma import get_collection, reset_collection  # noqa: E402
from app.core.embedding import DOC_PREFIX, MAX_SEQ_LENGTH, MODEL_NAME, load_model  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data_set" / "job_descriptions" / "job_descriptions_20k.csv"
LOG_DIR = ROOT / "logs"

log = logging.getLogger("embed_jd")


def setup_logging():
    """Ghi log ra file riêng cho mỗi lần chạy và ra màn hình."""
    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / f"embed_{datetime.now():%Y%m%d_%H%M%S}.log"
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    console = logging.StreamHandler()
    for h in (file_handler, console):
        h.setFormatter(fmt)
        log.addHandler(h)
    log.setLevel(logging.INFO)
    return log_path


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

    log_path = setup_logging()
    log.info("Bắt đầu nạp | log: %s", log_path)
    log.info("Tham số: %s", vars(args))

    model = load_model()
    log.info("Model: %s | device: %s | max_seq_length: %d",
             MODEL_NAME, model.device, MAX_SEQ_LENGTH)
    col = reset_collection() if args.reset else get_collection()
    log.info("Collection: %s | đã reset: %s | số JD hiện có: %d",
             col.name, args.reset, col.count())

    started = time.time()
    done = 0
    added = 0
    skipped = []  # (id, position, số token) của các JD dài quá giới hạn model
    reader = pd.read_csv(args.csv, chunksize=args.chunksize)
    for chunk_no, chunk in enumerate(reader, start=1):
        if args.limit is not None and done >= args.limit:
            break
        if args.limit is not None:
            chunk = chunk.head(args.limit - done)

        n_raw = len(chunk)
        chunk = chunk.dropna(subset=["id", "Long Description"])
        chunk = chunk.drop_duplicates(subset="id")
        n_invalid = n_raw - len(chunk)

        # bỏ qua id đã có trong DB
        existing = set(col.get(ids=chunk["id"].tolist(), include=[])["ids"])
        chunk = chunk[~chunk["id"].isin(existing)]
        done += len(chunk)
        if chunk.empty:
            log.info("Chunk %d: %d dòng, đã có trong DB hết -> bỏ qua", chunk_no, n_raw)
            continue

        # bỏ qua JD dài hơn giới hạn token của model (nếu không sẽ bị cắt khi embed)
        texts = (DOC_PREFIX + chunk["Long Description"].astype(str)).tolist()
        n_tokens = pd.Series(
            [len(ids) for ids in model.tokenizer(texts)["input_ids"]], index=chunk.index
        )
        too_long = chunk[n_tokens > MAX_SEQ_LENGTH]
        for idx, row in too_long.iterrows():
            log.warning("BỎ QUA id=%s | %s | %d token > %d",
                        row["id"], row["Position"], n_tokens[idx], MAX_SEQ_LENGTH)
            skipped.append((row["id"], row["Position"], int(n_tokens[idx])))
        chunk = chunk[n_tokens <= MAX_SEQ_LENGTH]
        n_tokens = n_tokens[chunk.index]
        log.info("Chunk %d: %d dòng | thiếu id/mô tả hoặc trùng: %d | đã có trong DB: %d | "
                 "quá dài: %d | cần nạp: %d | token min=%s trung bình=%.0f max=%s",
                 chunk_no, n_raw, n_invalid, len(existing), len(too_long), len(chunk),
                 n_tokens.min(), n_tokens.mean() if len(n_tokens) else 0, n_tokens.max())
        if chunk.empty:
            continue

        # sắp xếp theo độ dài để mỗi batch gồm JD dài gần bằng nhau -> ít padding hơn
        chunk = chunk.iloc[chunk["Long Description"].astype(str).str.len().argsort()]

        chunk_started = time.time()
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
        added += len(chunk)
        log.info("Chunk %d xong: nạp %d JD trong %.1fs | tổng trong DB: %d",
                 chunk_no, len(chunk), time.time() - chunk_started, col.count())

    log.info("Xong sau %.1f phút | nạp mới: %d | tổng trong DB: %d",
             (time.time() - started) / 60, added, col.count())
    log.info("Bỏ qua %d JD dài hơn %d token", len(skipped), MAX_SEQ_LENGTH)
    for jd_id, position, n in skipped:
        log.info("  - id=%s | %s | %d token", jd_id, position, n)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Dừng bởi người dùng (Ctrl+C). Chạy lại để nạp tiếp.")
    except Exception:
        log.exception("Lỗi khi nạp dữ liệu")
        raise
