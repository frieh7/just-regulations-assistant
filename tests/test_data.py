"""Checks the data and the seed test set against the Phase 1 rules. Run: pytest"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["id", "question", "expected_answer", "source", "difficulty"]
REFUSAL = ("لا أعرف", "I don't know")


def rows():
    with open(ROOT / "eval" / "seed_test_set.csv", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == COLUMNS
        return list(reader)


def test_thirty_rows_numbered_no_blanks():
    r = rows()
    assert len(r) >= 30
    assert [int(x["id"]) for x in r] == list(range(1, len(r) + 1))
    for x in r:
        assert all(x[c].strip() for c in COLUMNS), x["id"]


def test_difficulty_mix_and_refusals():
    r = rows()
    c = Counter(x["difficulty"] for x in r)
    assert set(c) <= {"easy", "medium", "hard"}
    assert c["easy"] >= 0.4 * len(r) and c["medium"] >= 0.25 * len(r) and c["hard"] >= 1
    assert sum(x["expected_answer"].startswith(REFUSAL) for x in r) >= 3


def test_sources_point_to_real_documents():
    files = {p.stem for p in (ROOT / "data" / "raw").glob("*.pdf")}
    for x in rows():
        if x["source"].startswith("Out of scope"):
            continue
        assert x["source"].split()[0] in files, f"row {x['id']}: unknown document"


def test_every_pdf_has_text_and_a_source_link():
    sources = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    assert {s["file"] for s in sources} == {p.name for p in (ROOT / "data" / "raw").glob("*.pdf")}
    for s in sources:
        assert s["url"].startswith("https://www.just.edu.jo/")
        text = (ROOT / "data" / "text" / s["file"].replace(".pdf", ".txt")).read_text(encoding="utf-8")
        assert len(text) > 500, s["file"]


def test_arabic_text_is_clean():
    broken = re.compile("األ|اإل|اال")      # flipped lam-alef
    marks = re.compile("[‎‏‪-‮]")
    total = 0
    for f in (ROOT / "data" / "text").glob("*.txt"):
        t = f.read_text(encoding="utf-8")
        total += len(broken.findall(t))
        assert not marks.search(t), f.name
    assert total <= 5
