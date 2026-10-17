"""Chuyển dataset parquet đã tải về thành job_descriptions.csv để nạp vào ChromaDB"""
import argparse
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data_set" / "job_descriptions"
COLUMNS = ["id", "Position", "Company Name", "Primary Keyword",
           "Exp Years", "English Level", "Long Description"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(next(DATA_DIR.glob("*.parquet"), DATA_DIR / "data.parquet")))
    ap.add_argument("--out", default=str(DATA_DIR / "job_descriptions.csv"))
    args = ap.parse_args()

    df = pd.read_parquet(args.src)
    print("Đọc:", len(df), "dòng")

    df = df[COLUMNS]
    df["Long Description"] = df["Long Description"].astype("string").str.strip()
    df = df.replace(r"^\s*$", pd.NA, regex=True)  # chuỗi rỗng coi như null
    df = df.dropna(subset=COLUMNS)  # bỏ dòng có bất kỳ trường cần lấy bị null
    df = df.drop_duplicates(subset="id")

    df.to_csv(args.out, index=False, encoding="utf-8")
    print("Đã ghi", len(df), "dòng ->", args.out)


if __name__ == "__main__":
    main()
