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
