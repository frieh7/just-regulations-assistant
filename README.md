# JUST Regulations Assistant

An assistant for bachelor students at Jordan University of Science and Technology (JUST),
all majors. Students ask in Arabic and the assistant answers in Arabic, using only the
official JUST documents in this repository, and cites the document and article in every
answer. If a question needs a personal record or a committee decision, or the answer is
not in the documents, it answers "لا أعرف" ["I don't know"] and names the responsible office.

Course: *Building LLM Systems: From Models to Production*, team project.
Current status: **Phase 1, Problem and Data.**

## Team (Phase 1 roles)

| Member | Role |
|---|---|
| Hamza Moeen Rasheed Essa | Product lead + Evaluation lead |
| Mohammad Ziad Abdelmajeed Al Rousan | Data lead |
| A'sem Zakariya Ali Elfrieh | Engineering lead |

Roles rotate at the start of each phase.

## Phase 1 submission

| Item | File |
|---|---|
| Proposal (2 pages) | `docs/proposal.pdf` |
| Data card (1 page) | `docs/data_card.pdf` |
| Seed test set (30 rows) | `eval/seed_test_set.csv` |
| Data sample | `data/samples/` (5 PDFs) |

## Repository layout

```
data/raw/       36 official JUST PDFs (24 student rules, 12 staff rules), 107 pages
data/samples/   5 sample PDFs referenced by the data card
data/text/      clean UTF-8 text, one file per PDF (+ _report.csv: method and quality)
data/SOURCES.md every document with its Arabic title, page count and official link
eval/           seed_test_set.csv (id,question,expected_answer,source,difficulty)
                score.py: answer, citation and refusal accuracy for a predictions file
src/            extract_text.py: PDF -> clean text (lam-alef fix, OCR for scans)
tests/          checks for the test set and the data (run: pytest)
docs/           proposal and data card (PDF), with their HTML source in docs/source/
```

## Rebuild the text

```
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-ara
pip install -r requirements.txt
python3 src/extract_text.py data/raw data/text
pytest
```

The text-layer PDFs draw "لا / لأ / لإ" as one glyph that the font maps in the wrong
order, so normal copying gives words like "األول" instead of "الأول" (895 places).
The script swaps only those pairs (the alef has zero width), removes invisible direction
marks, converts Arabic-Indic digits, and uses OCR for scans and broken fonts
(17 of 36 files). OCR can misread numbers: check important numbers against the PDF.

## Test set

`eval/seed_test_set.csv` has 30 Arabic questions written in students' own style, with
expected answers written from the documents before any model was run: 15 easy, 10 medium,
5 hard. Questions 28 to 30 are out of scope and must be answered with "لا أعرف"
["I don't know"]. The `source` column gives the file in `data/raw/`, the article and
the page. The file is UTF-8 with BOM so Excel shows the Arabic correctly.

## Score a model

```
python3 eval/score.py predictions.csv
```

`predictions.csv` has the columns `id,answer,citation,correct` (`correct` = 1/0 from a
human reviewer). The script reports answer accuracy, citation accuracy (right document
and article) and refusal accuracy, overall and by difficulty.

## Planned data (Phase 2)

Study plans and course catalogs for all bachelor majors are published on
www.just.edu.jo but are not downloaded yet. They are the next planned collection.

---

# Phase 2 — Train a small model and evaluate it

A small model (Qwen2.5-0.5B base) trained in two stages (CPT then SFT) on the JUST **bachelor study plans** (78 plans), scored on 30 new test questions (`tests/test_questions.csv`). Phase 2 uses a different scope from Phase 1 (study plans, not regulations); the Phase 1 test set stays in `eval/` for Phase 3.

## Checkpoints (not in Git)
Private Hugging Face repos, organization `llm-course-just-plans` (reader access: `a-mustafa`):
- CPT: https://huggingface.co/llm-course-just-plans/just-plans-cpt
- SFT: https://huggingface.co/llm-course-just-plans/just-plans-sft

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env     # only needed to push to the Hub; use Kaggle/Colab Secrets otherwise
```
Training was run on a Kaggle T4. Settings are in `config.yaml`; seed is 42.

## Train
```bash
python train_cpt.py                  # -> cpt_model/ , results/cpt/
python train_sft.py --start cpt      # -> sft_from_cpt/ , results/sft_cpt/
python train_sft.py --start base     # optional comparison (not run in Phase 2)
```
CPT corpus (cleaned text of the study plans, train/held-out split by document) goes in `data/cpt/`
(`cpt_plans_train.jsonl`: 404,228 tokens, `cpt_plans_heldout.jsonl`: 30,660 tokens; a sample is in the repo if large).

## Score
```bash
python score.py run                  # base, cpt, sft on the same 30 questions -> results/scores_<model>.csv
# two graders fill grader_1 / grader_2 (1, 0.5, 0) for manual rows; agreed value goes in `score`
python score.py summarize            # accuracy, refusal accuracy, agreement -> SCOREBOARD.md
```
All three models are called through the same function (`ask` in `score.py`).

## Data
- `data/sft_pairs.jsonl`: 1,930 pairs (1,869 plan questions + 61 refusals on 21 topics). `split` column: train/val, split by fact.
- `tests/test_questions.csv`: 30 test questions (15 easy / 10 medium / 5 hard, 3 refusals).
- No test question appears in the SFT data (checked for exact and near-text overlap).

## Results
See `SCOREBOARD.md` and `results/`.
