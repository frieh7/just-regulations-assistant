"""Score the assistant's answers against the seed test set.

Input: a predictions CSV with columns
    id        - the test question id
    answer    - the assistant's answer (Arabic)
    citation  - the document and article the assistant cited,
                e.g. "degree_regulation_bachelor Art. 12(b)"
    correct   - optional: 1 or 0, filled in by a human reviewer (or an LLM judge
                that a human has checked) after comparing answer and expected_answer

Reports, overall and per difficulty:
    answer accuracy    - share of rows marked correct = 1 (only if the column is filled)
    citation accuracy  - share of answerable questions whose citation names the right
                         document AND one of the right article (or item) numbers
    refusal accuracy   - out-of-scope questions answered with "لا أعرف", and
                         answerable questions NOT refused

Usage:  python3 eval/score.py predictions.csv [eval/seed_test_set.csv]
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

REFUSAL = "لا أعرف"
GOLD_DEFAULT = Path(__file__).with_name("seed_test_set.csv")


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {row["id"]: row for row in csv.DictReader(f)}


def parse_source(text):
    """'degree_regulation_bachelor Art. 9/4 and Art. 8(a), p. 6' -> ('degree_regulation_bachelor', {'9', '8'})"""
    doc = text.split()[0].rstrip(",;") if text.strip() else ""
    articles = set(re.findall(r"(?:Art\.?|item)\s*(\d+)", text))
    return doc, articles


def is_refusal(gold_row):
    return gold_row["expected_answer"].startswith(REFUSAL)


def score(gold, pred):
    groups = defaultdict(lambda: defaultdict(list))
    for qid, g in gold.items():
        p = pred.get(qid, {})
        answer = (p.get("answer") or "").strip()
        for key in ("all", g["difficulty"]):
            bucket = groups[key]
            refused = answer.startswith(REFUSAL)
            bucket["refusal"].append(refused == is_refusal(g))
            if not is_refusal(g):
                gdoc, garts = parse_source(g["source"])
                pdoc, parts = parse_source(p.get("citation") or "")
                # documents without numbered articles (e.g. a one-page policy): the document is enough
                bucket["citation"].append(pdoc == gdoc and (not garts or bool(garts & parts)))
            if (p.get("correct") or "").strip() in ("0", "1"):
                bucket["answer"].append(p["correct"].strip() == "1")
    return groups


def pct(values):
    return f"{100 * sum(values) / len(values):5.1f}% ({sum(values)}/{len(values)})" if values else "   n/a"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gold = read(sys.argv[2] if len(sys.argv) > 2 else GOLD_DEFAULT)
    pred = read(sys.argv[1])
    missing = sorted(set(gold) - set(pred), key=int)
    if missing:
        print(f"warning: no prediction for ids {', '.join(missing)} (counted as wrong)")
    groups = score(gold, pred)
    print(f"{'group':8s} {'answer accuracy':>18s} {'citation accuracy':>20s} {'refusal accuracy':>20s}")
    for key in ("all", "easy", "medium", "hard"):
        if key in groups:
            b = groups[key]
            print(f"{key:8s} {pct(b['answer']):>18s} {pct(b['citation']):>20s} {pct(b['refusal']):>20s}")


if __name__ == "__main__":
    main()
