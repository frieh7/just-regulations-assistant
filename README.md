# JUST Regulations Assistant

A chatbot for the website of Jordan University of Science and Technology (JUST) that
answers students' and staff members' questions about university rules in Arabic or
English, using only the official regulation documents, and cites the document and
article in every answer. If a question needs a personal record, a committee decision or
information that is not in the documents, it says "I don't know" and names the office.

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
data/raw/       36 official JUST PDFs (24 for students, 12 for staff), 107 pages
data/samples/   5 sample PDFs referenced by the data card
data/text/      clean UTF-8 text, one file per PDF (+ _report.csv: method and quality)
data/SOURCES.md every document with its Arabic title, page count and official link
eval/           seed_test_set.csv: id,question,expected_answer,source,difficulty
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

30 questions written from the documents before any model was run: 15 easy, 10 medium,
5 hard; 25 student and 5 staff; 21 Arabic and 9 English. Questions 28 to 30 are
out of scope and must be answered with "I don't know" / "لا أعرف".
The `source` column names the file in `data/raw/` and the article.
