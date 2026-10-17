"""Test cho app/core/taxonomy.py.

- Phần chấm điểm dùng một taxonomy nhỏ dựng riêng trong test, nên điểm kỳ vọng không phụ thuộc
  nội dung taxonomy.json (file này được sinh lại từ ESCO + JD_TREE và có thể đổi).
- Phần cuối kiểm tra taxonomy.json thật ở mức cần thiết cho dự án (chuỗi Blockchain, tách position).
"""
import json

import pytest

from app.core import taxonomy as tx

SMALL = {
    "name": "IT",
    "children": [
        {"name": "Blockchain", "aliases": ["block-chain"], "children": [
            {"name": "Blockchain Node", "children": [{"name": "Masternode"}]},
        ]},
        {"name": "Backend", "children": [
            {"name": "Java", "children": [{"name": "Spring"}]},
            {"name": "Python"},
        ]},
        {"name": "Frontend", "children": [{"name": "JavaScript", "children": [{"name": "Node.js"}]}]},
        {"name": "Backend2", "aliases": ["server side"], "children": [{"name": "Node.js"}]},  # Node.js có hai cha
        {"name": "Marketing"},
    ],
}


@pytest.fixture(scope="module")
def g(tmp_path_factory):
    path = tmp_path_factory.mktemp("tax") / "taxonomy.json"
    path.write_text(json.dumps(SMALL), encoding="utf-8")
    return tx.load_taxonomy(path)


# ---------- nạp đồ thị ----------

def test_load_builds_directed_graph(g):
    assert g.has_edge("blockchain", "blockchain node")
    assert g.has_edge("blockchain node", "masternode")
    assert not g.has_edge("masternode", "blockchain node")


def test_same_name_in_two_branches_merges_into_one_node(g):
    assert sorted(g.predecessors("node.js")) == ["backend2", "javascript"]


def test_load_rejects_cycle(tmp_path):
    # Hai nút trùng tên tạo cạnh ngược: a -> b -> a
    data = {"name": "IT", "children": [{"name": "A", "children": [{"name": "B", "children": [{"name": "A"}]}]}]}
    path = tmp_path / "t.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="vòng lặp"):
        tx.load_taxonomy(path)


def test_load_rejects_alias_shared_by_two_nodes(tmp_path):
    data = {"name": "IT", "children": [{"name": "A", "aliases": ["x"]}, {"name": "B", "aliases": ["X"]}]}
    path = tmp_path / "t.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="trùng"):
        tx.load_taxonomy(path)


# ---------- resolve / ancestors / descendants ----------

def test_resolve_ignores_case_and_whitespace_and_knows_aliases(g):
    assert tx.resolve("  BLOCKCHAIN ", g) == "blockchain"
    assert tx.resolve("Block-Chain", g) == "blockchain"
    assert tx.resolve("cobol", g) is None


def test_ancestors_nearest_first_and_exclude_root(g):
    assert tx.ancestors("Masternode", g) == ["Blockchain Node", "Blockchain"]
    assert tx.ancestors("Blockchain", g) == []


def test_descendants_nearest_first(g):
    assert tx.descendants("Blockchain", g) == ["Blockchain Node", "Masternode"]
    assert tx.ancestors("Cobol", g) == tx.descendants("Cobol", g) == []


# ---------- relation ----------

@pytest.mark.parametrize("a, b, kind, steps, via", [
    ("Java", "java", "same", 0, None),
    ("Blockchain", "Masternode", "ancestor", 2, None),   # a chung hơn b
    ("Masternode", "Blockchain", "descendant", 2, None),  # a cụ thể hơn b
    ("Java", "Python", "related", 2, "Backend"),
    ("Spring", "Python", "related", 3, "Backend"),
    ("Java", "Marketing", "unrelated", 0, None),         # chỉ gặp nhau ở gốc
    ("Java", "Cobol", "unknown", 0, None),
])
def test_relation(g, a, b, kind, steps, via):
    assert tx.relation(a, b, g) == tx.Relation(kind, steps, via)


# ---------- chấm điểm: khóa hành vi và hệ số ----------

@pytest.mark.parametrize("required, candidate, expected", [
    ("Java", "Java", 1.0),
    ("Blockchain", "Blockchain Node", 1.0),      # ứng viên cụ thể hơn 1 cấp
    ("Blockchain", "Masternode", 0.9),           # cụ thể hơn 2 cấp
    ("Blockchain Node", "Blockchain", 0.5),      # ứng viên chung hơn 1 cấp
    ("Masternode", "Blockchain", 0.25),          # chung hơn 2 cấp
    ("Java", "Python", 0.25),                    # cùng nhánh, 2 bước
    ("Spring", "Python", 0.5 / 3),               # cùng nhánh, 3 bước
    ("Java", "Marketing", 0.0),
    ("Java", "Cobol", 0.0),
])
def test_skill_match_score(g, required, candidate, expected):
    assert tx.skill_match_score(required, candidate, g) == pytest.approx(expected)


def test_score_is_asymmetric_specialist_beats_generalist(g):
    assert tx.skill_match_score("Java", "Spring", g) > tx.skill_match_score("Spring", "Java", g)


def test_score_always_within_0_and_1(g):
    terms = ["Java", "Spring", "Python", "Blockchain", "Masternode", "Node.js", "Marketing", "Cobol"]
    for r in terms:
        for c in terms:
            assert 0.0 <= tx.skill_match_score(r, c, g) <= 1.0


def test_score_constants_have_expected_values():
    # Đổi hệ số là đổi toàn bộ điểm: nếu cố ý đổi thì sửa test này cùng lúc.
    assert (tx.SPECIALIZATION_DECAY, tx.GENERALIZATION_DECAY, tx.RELATED_BASE) == (0.9, 0.5, 0.5)


# ---------- match_skills ----------

def test_match_skills_takes_best_candidate_per_requirement(g):
    res = tx.match_skills(["Blockchain", "Java"], ["Masternode", "Python", "Spring"], g)
    by_req = {d["required"]: d for d in res["details"]}
    assert by_req["Blockchain"]["matched_by"] == "Masternode"
    assert by_req["Blockchain"]["relation"] == "descendant"
    assert by_req["Java"]["matched_by"] == "Spring"
    assert res["coverage"] == pytest.approx((0.9 + 1.0) / 2)


def test_match_skills_reports_unknown_separately_and_excludes_them_from_coverage(g):
    res = tx.match_skills(["Java", "Cobol"], ["Java"], g)
    assert res["unknown"] == ["Cobol"]
    assert res["coverage"] == 1.0


def test_match_skills_with_no_candidate_skills(g):
    res = tx.match_skills(["Java"], [], g)
    assert res["coverage"] == 0.0
    assert res["details"][0]["matched_by"] is None


def test_match_skills_with_no_known_requirements(g):
    assert tx.match_skills(["Cobol"], ["Java"], g)["coverage"] == 0.0


# ---------- extract_terms ----------

@pytest.mark.parametrize("text, expected", [
    ("Senior Java and Python engineer", ["Java", "Python"]),
    ("Java-based Spring dev", ["Java", "Spring"]),
    ("Team Leader (Java+Python)", ["Java", "Python"]),
    ("Python, python, PYTHON", ["Python"]),                  # không trùng lặp
    ("Node.js developer", ["Node.js"]),                      # cụm dài nhất, không tách "Node" + "js"
    ("Block-chain engineer", ["Blockchain"]),                # alias -> tên chuẩn
    ("Javascript and server side", ["JavaScript", "Backend2"]),
    ("Master node", []),                                     # không khớp giữa từ
    ("", []),
])
def test_extract_terms(g, text, expected):
    assert tx.extract_terms(text, g) == expected


def test_extract_terms_does_not_match_inside_words(g):
    assert tx.extract_terms("Javascripting and Pythonic", g) == []


# ---------- taxonomy.json thật ----------

@pytest.fixture(scope="module")
def real():
    return tx.load_taxonomy()


def test_real_taxonomy_loads_as_dag(real):
    import networkx as nx
    assert nx.is_directed_acyclic_graph(real)
    assert real.number_of_nodes() > 100


def test_real_taxonomy_has_blockchain_chain(real):
    assert tx.relation("Blockchain", "Masternode", real).kind == "ancestor"
    assert tx.skill_match_score("Blockchain", "Masternode", real) > tx.skill_match_score("Masternode", "Blockchain", real)


@pytest.mark.parametrize("position, expected", [
    ("Senior/Lead Backend Developer (Python)", {"Backend", "Python"}),
    ("DevOps Engineer (AWS, Kubernetes, CI/CD)", {"DevOps", "AWS", "Kubernetes", "CI/CD"}),
    ("Senior C++ and C# engineer", {"C++", "C#"}),
])
def test_real_taxonomy_extracts_job_positions(real, position, expected):
    assert expected <= set(tx.extract_terms(position, real))


@pytest.mark.parametrize("text", ["Go to market manager", "We value it less in spring", "R&D engineer"])
def test_real_taxonomy_ignores_ambiguous_common_words(real, text):
    assert tx.extract_terms(text, real) == []
