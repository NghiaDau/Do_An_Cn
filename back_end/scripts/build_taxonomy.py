"""Tạo taxonomy.json từ ESCO + JD"""

import argparse
import json
import re
from pathlib import Path

import networkx as nx
import pandas as pd

from jd_tree import JD_TREE

BACK_END = Path(__file__).resolve().parents[1]
ESCO_DIR = BACK_END / "data_set" / "skill_en"
JD_CSV = BACK_END / "data_set" / "job_descriptions" / "job_descriptions_20k.csv"
OUT = BACK_END / "app" / "data" / "taxonomy.json"

ICT_ROOT = "http://data.europa.eu/esco/isced-f/06"
ROOT_NAME = "IT"

# Luôn giữ dù ít xuất hiện trong JD (chuỗi Blockchain -> Node -> Masternode).
FORCE = {"blockchain", "blockchain node", "masternode"}


def norm(s):
    return " ".join(str(s).lower().split())


class Graph:
    """Đồ thị tên -> {name, aliases}; cạnh cha -> con; bỏ cạnh nếu tạo vòng/tự trỏ."""

    def __init__(self):
        self.g = nx.DiGraph()

    def node(self, name, aliases=()):
        key = norm(name)
        if key not in self.g:
            self.g.add_node(key, name=name, aliases=[])
        for a in aliases:
            if a and a not in self.g.nodes[key]["aliases"]:
                self.g.nodes[key]["aliases"].append(a)
        return key

    def edge(self, parent, child):
        if parent == child or self.g.has_edge(parent, child):
            return
        if nx.has_path(self.g, child, parent):  # sẽ tạo vòng
            return
        self.g.add_edge(parent, child)


def load_esco(G, root):
    dg = pd.read_csv(ESCO_DIR / "digitalSkillsCollection_en.csv")
    rel = pd.read_csv(ESCO_DIR / "broaderRelationsSkillPillar_en.csv")

    parents, children, label = {}, {}, {}
    for c, cl, b, bl in zip(rel.conceptUri, rel.conceptLabel, rel.broaderUri, rel.broaderLabel):
        parents.setdefault(c, []).append(b)
        children.setdefault(b, []).append(c)
        label[c], label[b] = cl, bl

    # các URI nằm dưới nhóm ICT (kể cả chính nó)
    ict, stack = {ICT_ROOT}, [ICT_ROOT]
    while stack:
        for ch in children.get(stack.pop(), []):
            if ch not in ict:
                ict.add(ch)
                stack.append(ch)

    skills = dg[(dg.skillType == "knowledge") & dg.conceptUri.isin(ict)]
    keep = set(skills.conceptUri)
    stack = list(keep)
    while stack:  # thêm các nhóm cha trong ICT
        for p in parents.get(stack.pop(), []):
            if p in ict and p not in keep:
                keep.add(p)
                stack.append(p)

    alt = {u: [a.strip() for a in str(a_).split("\n") if a.strip() and str(a_) != "nan"]
           for u, a_ in zip(skills.conceptUri, skills.altLabels)}
    for u in keep:
        G.node(label[u], alt.get(u, []))
    G.node(label[ICT_ROOT])
    for u in keep:
        for p in parents.get(u, []):
            if p in keep:
                G.edge(norm(label[p]), norm(label[u]))
    G.edge(root, norm(label[ICT_ROOT]))
    return len(skills), len(keep) - len(skills)


def add_curated(G, root, items, parent):
    for it in items:
        key = G.node(it["name"], it["aliases"])
        G.g.nodes[key]["name"] = it["name"]  # ưu tiên cách viết soạn tay hơn ESCO
        G.edge(parent, key)
        add_curated(G, root, it["children"], key)


def count_docs(G, curated_keys, texts):
    """Số JD chứa tên/alias của từng nút soạn tay."""
    counts = {}
    for key in curated_keys:
        names = [G.g.nodes[key]["name"]] + G.g.nodes[key]["aliases"]
        pat = "|".join(re.escape(n.lower()) for n in names)
        rx = re.compile(r"(?<![a-z0-9+#.])(?:" + pat + r")(?![a-z0-9+#])")
        counts[key] = sum(1 for t in texts if rx.search(t))
    return counts


def prune(G, curated_keys, counts, min_count):
    """Bỏ nút soạn tay ít xuất hiện và không còn con nào sống sót."""
    dead = set()
    for key in reversed(list(nx.topological_sort(G.g))):  # con trước cha
        if key not in curated_keys:
            continue
        has_child = any(c not in dead for c in G.g.successors(key))
        if not (key in FORCE or counts[key] >= min_count or has_child):
            dead.add(key)
    G.g.remove_nodes_from(dead)
    return dead


def clean_aliases(G):
    """Alias không được trùng tên/alias của nút khác (taxonomy.py sẽ báo lỗi)."""
    owner = {k: k for k in G.g}
    for key in G.g:
        kept = []
        for a in G.g.nodes[key]["aliases"]:
            na = norm(a)
            if na == key or owner.setdefault(na, key) != key:
                continue
            kept.append(a)
        G.g.nodes[key]["aliases"] = kept


def to_tree(G, root):
    seen = set()

    def build(key):
        n = G.g.nodes[key]
        d = {"name": n["name"]}
        if n["aliases"]:
            d["aliases"] = n["aliases"]
        if key not in seen:  # nút nhiều cha: chỉ mở con ở lần gặp đầu
            seen.add(key)
            kids = sorted(G.g.successors(key), key=lambda k: G.g.nodes[k]["name"].lower())
            if kids:
                d["children"] = [build(k) for k in kids]
        return d

    return build(root)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-count", type=int, default=5, help="số JD tối thiểu để giữ thuật ngữ")
    ap.add_argument("--show-counts", action="store_true",
                    help="chỉ in số JD chứa từng thuật ngữ (để chọn ngưỡng), không ghi file")
    args = ap.parse_args()

    G = Graph()
    root = G.node(ROOT_NAME)

    n_skill, n_group = load_esco(G, root)
    esco_keys = set(G.g.nodes)
    add_curated(G, root, JD_TREE, root)
    curated_keys = set(G.g.nodes) - esco_keys | {
        norm(n["name"]) for n in _flatten(JD_TREE)}

    df = pd.read_csv(JD_CSV, usecols=["Position", "Long Description"])
    texts = (df["Position"].astype(str) + "\n" + df["Long Description"].astype(str)).str.lower().tolist()
    counts = count_docs(G, curated_keys, texts)
    if args.show_counts:
        for key, c in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
            print(f"{c:6d}  {G.g.nodes[key]['name']}")
        return
    dead = prune(G, curated_keys, counts, args.min_count)
    clean_aliases(G)

    tree = to_tree(G, root)
    OUT.write_text(json.dumps(tree, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ESCO: {n_skill} kỹ năng + {n_group} nhóm | JD: bỏ {len(dead)} thuật ngữ ít xuất hiện "
          f"(<{args.min_count} JD) | tổng {G.g.number_of_nodes()} nút -> {OUT}")


def _flatten(items):
    for it in items:
        yield it
        yield from _flatten(it["children"])


if __name__ == "__main__":
    main()
