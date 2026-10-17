"""Đồ thị taxonomy ngành IT trong bộ nhớ (NetworkX) và các hàm suy luận phân cấp kỹ năng/vị trí.

- Dữ liệu: app/data/taxonomy.json (cây lồng nhau; cạnh đi từ chung -> cụ thể, vd Blockchain -> Blockchain Node -> Masternode).
- Một nút xuất hiện ở nhiều nhánh (cùng tên) được gộp thành một nút, nên đồ thị là DAG chứ không nhất thiết là cây.
- Mỗi nút có `name` và `aliases`; mọi tra cứu đều qua `resolve()` (không phân biệt hoa thường).
- Module độc lập: không phụ thuộc Chroma hay model embedding.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import json
import re

import networkx as nx

TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "data" / "taxonomy.json"

# Ứng viên có kỹ năng CỤ THỂ hơn yêu cầu (vd yêu cầu Java, ứng viên biết Spring): coi như đáp ứng,
# giảm nhẹ theo mỗi cấp cách xa. Cấp 1 = 1.0, cấp 2 = 0.9, ...
SPECIALIZATION_DECAY = 0.9
# Ứng viên chỉ biết kỹ năng CHUNG hơn yêu cầu (vd yêu cầu Spring, ứng viên biết Java): đáp ứng một phần,
# giảm mạnh theo mỗi cấp. Cấp 1 = 0.5, cấp 2 = 0.25, ...
GENERALIZATION_DECAY = 0.5
# Hai kỹ năng khác nhánh nhưng chung tổ tiên (không tính gốc): điểm = RELATED_BASE / tổng số bước qua tổ tiên chung.
RELATED_BASE = 0.5


def normalize(term: str) -> str:
    return " ".join(str(term).lower().split())


def load_taxonomy(path: Path = TAXONOMY_PATH) -> nx.DiGraph:
    """Đọc file JSON và dựng đồ thị có hướng (cha -> con)."""
    with open(path, encoding="utf-8") as f:
        root = json.load(f)

    g = nx.DiGraph()
    aliases: dict[str, str] = {}  # alias/tên đã chuẩn hóa -> id nút

    def claim(key: str, node_id: str) -> None:
        owner = aliases.setdefault(key, node_id)
        if owner != node_id:
            raise ValueError(f"Alias/tên '{key}' trùng giữa '{owner}' và '{node_id}'")

    def add(item: dict, parent: str | None) -> None:
        node_id = normalize(item["name"])
        if node_id not in g:
            g.add_node(node_id, name=item["name"], aliases=set())
        claim(node_id, node_id)
        for alias in item.get("aliases", []):
            claim(normalize(alias), node_id)
            g.nodes[node_id]["aliases"].add(alias)
        if parent is not None:
            g.add_edge(parent, node_id)
        for child in item.get("children", []):
            add(child, node_id)

    add(root, None)
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError("Taxonomy có vòng lặp: cạnh phải đi từ chung -> cụ thể")
    g.graph["aliases"] = aliases
    g.graph["root"] = normalize(root["name"])
    return g


@lru_cache(maxsize=1)
def get_taxonomy() -> nx.DiGraph:
    """Đồ thị dùng chung, chỉ nạp một lần."""
    return load_taxonomy()


def resolve(term: str, g: nx.DiGraph | None = None) -> str | None:
    """Tên/alias bất kỳ -> id nút chuẩn, hoặc None nếu không có trong taxonomy."""
    g = g or get_taxonomy()
    return g.graph["aliases"].get(normalize(term))


def display_name(node_id: str, g: nx.DiGraph | None = None) -> str:
    return (g or get_taxonomy()).nodes[node_id]["name"]


# Khóa ngắn hoặc trùng từ tiếng Anh thông thường thì chỉ nhận khi viết đúng dạng trong văn bản,
# tránh khớp nhầm ("it", "go", "r", "c", "less", "spring"...).
_UPPER_ONLY_EXTRA = {"it", "go", "obs", "apl"}  # cộng thêm mọi khóa chữ cái dài <= 2 -> chỉ nhận dạng IN HOA
_CAPITALIZED = {"less", "salt", "absorb", "swift", "spring", "spark", "oracle", "unity", "rails", "maven",
                "puppet", "groovy", "pascal"}  # nhận dạng Viết hoa đầu hoặc IN HOA, không nhận chữ thường
_BEFORE = r"(?<![\w.&])"
_AFTER = r"(?![\w&])(?!\.\w)"


def _alternation(keys) -> re.Pattern | None:
    keys = sorted(set(keys), key=len, reverse=True)
    if not keys:
        return None
    return re.compile(_BEFORE + "(?:" + "|".join(re.escape(k).replace(r"\ ", r"\s+") for k in keys) + ")" + _AFTER)


def _extractors(g: nx.DiGraph):
    """Dựng (và nhớ) các regex dò thuật ngữ: một cho khóa an toàn, một cho khóa nhạy cảm chữ hoa/thường."""
    if "_extractors" not in g.graph:
        aliases = g.graph["aliases"]
        upper_only = {k for k in aliases if k.isalpha() and len(k) <= 2} | (_UPPER_ONLY_EXTRA & aliases.keys())
        capitalized = _CAPITALIZED & aliases.keys()
        safe = set(aliases) - upper_only - capitalized
        safe_re = _alternation(safe)
        safe_re = re.compile(safe_re.pattern, re.IGNORECASE) if safe_re else None
        # khóa nhạy cảm: liệt kê sẵn các dạng chấp nhận được, khớp phân biệt hoa thường
        forms = {k.upper(): k for k in upper_only}
        for k in capitalized:
            forms[k.upper()] = k
            forms[k.capitalize()] = k
        g.graph["_extractors"] = (safe_re, _alternation(forms), forms)
    return g.graph["_extractors"]


def extract_terms(text: str, g: nx.DiGraph | None = None) -> list[str]:
    """Tách các thuật ngữ trong taxonomy ra khỏi văn bản tự do (position, description...).

    Trả về tên chuẩn của nút, theo thứ tự xuất hiện lần đầu, không trùng. Khớp theo cụm dài nhất
    và không chồng lấn ("Node.js" không bị tách thành "Node" + "js"); không khớp giữa từ
    ("javascript" không cho "Java"). Khóa ngắn/dễ nhầm xem `_UPPER_ONLY_EXTRA` và `_CAPITALIZED`.
    Chỉ phát hiện thuật ngữ có đúng tên hoặc alias trong taxonomy, không suy luận ngữ nghĩa.
    """
    g = g or get_taxonomy()
    aliases = g.graph["aliases"]
    safe_re, strict_re, forms = _extractors(g)

    spans = []  # (bắt đầu, kết thúc, id nút)
    if safe_re:
        spans += [(m.start(), m.end(), aliases[normalize(m.group())]) for m in safe_re.finditer(text)]
    if strict_re:
        spans += [(m.start(), m.end(), aliases[forms[m.group()]]) for m in strict_re.finditer(text)]

    taken, picked = [], []
    for start, end, node in sorted(spans, key=lambda s: (s[0] - s[1], s[0])):  # dài nhất trước, rồi đến sớm nhất
        if all(end <= a or start >= b for a, b in taken):
            taken.append((start, end))
            picked.append((start, node))
    names = []
    for _, node in sorted(picked):
        name = display_name(node, g)
        if name not in names:
            names.append(name)
    return names


def ancestors(term: str, g: nx.DiGraph | None = None) -> list[str]:
    """Các khái niệm chung hơn, từ gần đến xa (không gồm gốc). Rỗng nếu không biết `term`."""
    g = g or get_taxonomy()
    node = resolve(term, g)
    if node is None:
        return []
    dist = {a: nx.shortest_path_length(g, a, node) for a in nx.ancestors(g, node) if a != g.graph["root"]}
    return [display_name(a, g) for a in sorted(dist, key=dist.get)]


def descendants(term: str, g: nx.DiGraph | None = None) -> list[str]:
    """Các khái niệm cụ thể hơn, từ gần đến xa. Rỗng nếu không biết `term`."""
    g = g or get_taxonomy()
    node = resolve(term, g)
    if node is None:
        return []
    dist = nx.single_source_shortest_path_length(g, node)
    dist.pop(node)
    return [display_name(d, g) for d in sorted(dist, key=dist.get)]


@dataclass(frozen=True)
class Relation:
    """Quan hệ của `a` so với `b`.

    kind:
      same        - cùng một nút
      ancestor    - `a` chung hơn `b` (b nằm dưới a), `steps` cấp
      descendant  - `a` cụ thể hơn `b` (a nằm dưới b), `steps` cấp
      related     - khác nhánh, chung tổ tiên `via` (không phải gốc); `steps` = tổng số bước qua `via`
      unrelated   - cùng taxonomy nhưng chỉ gặp nhau ở gốc
      unknown     - ít nhất một thuật ngữ không có trong taxonomy
    """
    kind: str
    steps: int = 0
    via: str | None = None


def relation(a: str, b: str, g: nx.DiGraph | None = None) -> Relation:
    g = g or get_taxonomy()
    na, nb = resolve(a, g), resolve(b, g)
    if na is None or nb is None:
        return Relation("unknown")
    if na == nb:
        return Relation("same")
    if nx.has_path(g, na, nb):
        return Relation("ancestor", nx.shortest_path_length(g, na, nb))
    if nx.has_path(g, nb, na):
        return Relation("descendant", nx.shortest_path_length(g, nb, na))

    root = g.graph["root"]
    common = (nx.ancestors(g, na) & nx.ancestors(g, nb)) - {root}
    if not common:
        return Relation("unrelated")
    best = min(common, key=lambda c: nx.shortest_path_length(g, c, na) + nx.shortest_path_length(g, c, nb))
    steps = nx.shortest_path_length(g, best, na) + nx.shortest_path_length(g, best, nb)
    return Relation("related", steps, display_name(best, g))


def skill_match_score(required: str, candidate: str, g: nx.DiGraph | None = None) -> float:
    """Mức ứng viên có `candidate` đáp ứng yêu cầu `required`, trong [0, 1]."""
    rel = relation(candidate, required, g)  # quan hệ của ứng viên so với yêu cầu
    if rel.kind == "same":
        return 1.0
    if rel.kind == "descendant":  # ứng viên cụ thể hơn yêu cầu
        return SPECIALIZATION_DECAY ** (rel.steps - 1)
    if rel.kind == "ancestor":  # ứng viên chỉ biết khái niệm chung hơn
        return GENERALIZATION_DECAY ** rel.steps
    if rel.kind == "related":
        return RELATED_BASE / rel.steps
    return 0.0


def match_skills(required: list[str], candidate: list[str], g: nx.DiGraph | None = None) -> dict:
    """So khớp danh sách kỹ năng yêu cầu với kỹ năng ứng viên.

    Mỗi kỹ năng yêu cầu lấy điểm cao nhất trong số kỹ năng ứng viên (kỹ năng khác có thể bù trừ).
    `coverage` là trung bình điểm của các kỹ năng yêu cầu nằm trong taxonomy; kỹ năng lạ nằm ở `unknown`.
    """
    g = g or get_taxonomy()
    details, unknown = [], []
    for req in required:
        if resolve(req, g) is None:
            unknown.append(req)
            continue
        scored = [(skill_match_score(req, c, g), c) for c in candidate]
        score, best = max(scored, default=(0.0, None))
        details.append({
            "required": req,
            "score": round(score, 4),
            "matched_by": best if score > 0 else None,
            "relation": relation(best, req, g).kind if score > 0 else None,
        })
    coverage = sum(d["score"] for d in details) / len(details) if details else 0.0
    return {"coverage": round(coverage, 4), "details": details, "unknown": unknown}
