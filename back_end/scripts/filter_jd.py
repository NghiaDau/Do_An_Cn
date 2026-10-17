"""Lọc JD sạch, đủ thông tin nhất và phủ tất cả title (Primary Keyword)"""
import argparse
import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data_set" / "job_descriptions"
SECTION_RE = re.compile(
    r"requirement|responsibilit|qualification|we offer|benefit|salary|conditions?|"
    r"skills?|experience|about (us|the)|nice to have|must have|tech stack|duties",
    re.I,
)
EXP_RANK = {"no_exp": 0, "1y": 1, "2y": 2, "3y": 3, "5y": 4}
ENG_RANK = {"basic": 0, "pre": 1, "intermediate": 2, "upper": 3, "fluent": 4}


def clean_title(s: str) -> str:
    s = re.sub(r"[​-‏⁠﻿]", "", s)  # ký tự zero-width
    s = re.sub(r"\s*#\d+\s*$", "", s)  # đuôi "#7569"
    return re.sub(r"\s+", " ", s).strip()


def valid_title(s: str) -> bool:
    if not 3 <= len(s) <= 100:
        return False
    letters = sum(c.isalpha() for c in s)
    return letters / len(s) >= 0.6  # loại title toàn ký tự lạ/số


def score(df: pd.DataFrame) -> pd.Series:
    desc = df["Long Description"]
    length = desc.str.len().clip(upper=4000) / 4000  # dài tới ~4000 ký tự là đủ
    sections = desc.apply(lambda d: len(set(m.group(0).lower() for m in SECTION_RE.finditer(d)))).clip(upper=8) / 8
    lines = desc.str.count(r"\n").clip(upper=40) / 40  # có cấu trúc / bullet
    exp = df["Exp Years"].map(EXP_RANK).fillna(0) / 4
    eng = df["English Level"].map(ENG_RANK).fillna(0) / 4
    return 0.45 * length + 0.25 * sections + 0.15 * lines + 0.1 * exp + 0.05 * eng


def allocate(sizes: pd.Series, total: int, min_per: int) -> dict:
    """Mỗi nhóm tối thiểu min_per, phần còn lại chia theo tỉ lệ (water-filling có trần = số JD của nhóm)"""
    quota = {k: min(n, min_per) for k, n in sizes.items()}
    left = total - sum(quota.values())
    while left > 0:
        room = {k: sizes[k] - q for k, q in quota.items() if sizes[k] > q}
        if not room:
            break
        tot = sum(sizes[k] for k in room)
        added = 0
        for k in room:
            add = min(room[k], max(1, int(left * sizes[k] / tot)))
            quota[k] += add
            added += add
        left -= added
        if left < 0:  # làm tròn vượt: bớt từ nhóm lớn nhất
            for k in sorted(quota, key=quota.get, reverse=True):
                if left == 0:
                    break
                quota[k] -= 1
                left += 1
    return quota


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DATA_DIR / "job_descriptions.csv"))
    ap.add_argument("--out", default=str(DATA_DIR / "job_descriptions_20k.csv"))
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--min-per-title", type=int, default=50, help="số JD tối thiểu mỗi Primary Keyword")
    args = ap.parse_args()

    df = pd.read_csv(args.src)
    print("Đọc:", len(df), "dòng")

    df["Position"] = df["Position"].astype(str).map(clean_title)
    df = df[df["Position"].map(valid_title)]
    df = df[df["Long Description"].str.len() >= 300]  # JD quá ngắn
    print("Sau lọc title/độ dài:", len(df))

    # bỏ trùng: cùng description hoặc cùng (position, company)
    df = df.drop_duplicates(subset="Long Description")
    df = df.drop_duplicates(subset=["Position", "Company Name"])
    print("Sau bỏ trùng:", len(df))

    df["score"] = score(df)
    sizes = df["Primary Keyword"].value_counts()
    quota = allocate(sizes, args.n, args.min_per_title)

    parts = [g.nlargest(quota[k], "score") for k, g in df.groupby("Primary Keyword")]
    out = pd.concat(parts).sort_values("score", ascending=False)
    out = out.drop(columns="score")
    out.to_csv(args.out, index=False, encoding="utf-8")

    print("Đã ghi", len(out), "dòng ->", args.out)
    print(out["Primary Keyword"].value_counts().to_string())


if __name__ == "__main__":
    main()
