"""Checks the seed test set and the data against the Phase 1 rules. Run: pytest"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["id", "question", "expected_answer", "source", "difficulty"]
REFUSAL = "لا أعرف"
ARABIC_LETTER = re.compile(r"[ء-ي]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")


def rows():
    with open(ROOT / "eval" / "seed_test_set.csv", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == COLUMNS, reader.fieldnames
        return list(reader)


def test_exactly_30_rows_numbered_1_to_30():
    r = rows()
    assert len(r) == 30
    assert [int(x["id"]) for x in r] == list(range(1, 31))


def test_no_empty_cells_and_every_row_has_a_source():
    for x in rows():
        for c in COLUMNS:
            assert x[c].strip(), f"row {x['id']}: empty {c}"


def test_difficulty_mix():
    c = Counter(x["difficulty"] for x in rows())
    assert set(c) <= {"easy", "medium", "hard"}
    # about half easy, a third medium, the rest hard
    assert 13 <= c["easy"] <= 17
    assert 8 <= c["medium"] <= 12
    assert c["hard"] >= 3


def test_at_least_three_refusals_in_arabic():
    refusals = [x for x in rows() if x["expected_answer"].startswith(REFUSAL)]
    assert len(refusals) >= 3
    for x in refusals:
        assert x["source"].startswith("Out of scope"), f"row {x['id']}"


def test_questions_and_answers_are_arabic():
    for x in rows():
        for col in ("question", "expected_answer"):
            text = x[col]
            assert ARABIC_LETTER.search(text), f"row {x['id']}: {col} has no Arabic"
            assert not LATIN_WORD.search(text), f"row {x['id']}: {col} contains English"


def test_sources_name_real_documents():
    files = {p.stem for p in (ROOT / "data" / "raw").glob("*.pdf")}
    for x in rows():
        src = x["source"]
        if src.startswith("Out of scope") and ";" not in src:
            continue
        doc = src.split(";")[-1].split()[0].rstrip(",") if src.startswith("Out of scope") else src.split()[0].rstrip(",")
        assert doc in files, f"row {x['id']}: unknown document {doc}"


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


def test_scoring_script_gives_full_marks_to_perfect_answers(tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "eval"))
    import score
    gold = score.read(ROOT / "eval" / "seed_test_set.csv")
    perfect = tmp_path / "pred.csv"
    with open(perfect, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "answer", "citation", "correct"])
        for qid, g in gold.items():
            w.writerow([qid, g["expected_answer"], g["source"], 1])
    groups = score.score(gold, score.read(perfect))
    for key in ("answer", "citation", "refusal"):
        assert all(groups["all"][key]), key
