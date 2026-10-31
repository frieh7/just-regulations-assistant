"""Extract clean Arabic text from the regulation PDFs in data/raw.

For each PDF:
1. Read the text layer with PyMuPDF and fix the lam-alef bug: these PDFs draw
   "لا / لأ / لإ / لآ" as one glyph that the font maps in the wrong order
   ("األول" instead of "الأول"). In every broken pair the alef has zero
   width, so we swap exactly those pairs and leave words like "مال" alone.
2. Score the text. If the PDF is a scan (almost no text) or the text layer is
   junk (few real Arabic words), read the pages with Tesseract OCR instead.
3. Normalise: NFKC, remove invisible direction marks, tidy whitespace.

Writes data/text/<name>.txt and data/text/_report.csv (method + quality per file).

Usage:  python3 src/extract_text.py [raw_dir] [out_dir]
Needs:  pip install pymupdf ; apt install tesseract-ocr tesseract-ocr-ara poppler-utils
"""
import csv
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

import pymupdf

ALEFS = set("اأإآ")
BIDI = re.compile("[‎‏‪-‮⁦-⁩]")
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_WORD = re.compile(r"[ء-ي]{2,}")
# very common words; a healthy Arabic regulation text is full of them
COMMON = {"في", "من", "على", "إلى", "الجامعة", "أو", "التي", "الذي", "عن", "مع", "الطالب", "الطلبة", "المادة"}


def fix_span(chars) -> str:
    out, i = [], 0
    while i < len(chars):
        c = chars[i]
        if (c["c"] in ALEFS and i + 1 < len(chars) and chars[i + 1]["c"] == "ل"
                and c["bbox"][2] - c["bbox"][0] < 0.05):
            out.append("ل" + c["c"])
            i += 2
            continue
        out.append(c["c"])
        i += 1
    return "".join(out)


def text_layer(pdf: Path) -> str:
    pages = []
    with pymupdf.open(pdf) as doc:
        for page in doc:
            lines = []
            for block in page.get_text("rawdict")["blocks"]:
                for line in block.get("lines", []):
                    lines.append(" ".join(fix_span(s["chars"]) for s in line["spans"]))
            pages.append("\n".join(lines))
    return "\n\n".join(pages)


def ocr(pdf: Path) -> str:
    pages = []
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", "300", "-png", str(pdf), f"{tmp}/pg"], check=True)
        for img in sorted(Path(tmp).glob("pg-*.png")):
            res = subprocess.run(["tesseract", str(img), "-", "-l", "ara+eng", "--psm", "6"],
                                 capture_output=True, text=True, check=True)
            pages.append(res.stdout)
    return "\n\n".join(pages)


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = BIDI.sub("", text)
    text = text.replace("ـ", "")          # tatweel (stretching) character
    text = text.translate(DIGITS)              # ١٤ -> 14, so numbers are searchable
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def quality(text: str) -> float:
    """Share of Arabic words that are very common words (healthy text: > 0.12)."""
    words = ARABIC_WORD.findall(text)
    if len(words) < 50:
        return 0.0
    return sum(w in COMMON for w in words) / len(words)


def main() -> None:
    raw = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/text")
    out.mkdir(parents=True, exist_ok=True)
    report = []
    for pdf in sorted(raw.glob("*.pdf")):
        text = normalise(text_layer(pdf))
        q, method = quality(text), "text layer"
        with pymupdf.open(pdf) as doc:
            per_page = len(text) / max(len(doc), 1)
        english = len(re.findall(r"[A-Za-z]{3,}", text)) > len(ARABIC_WORD.findall(text))
        if (q < 0.08 and not english) or per_page < 500:
            ocr_text = normalise(ocr(pdf))
            if quality(ocr_text) > q:
                text, q, method = ocr_text, quality(ocr_text), "ocr"
        (out / f"{pdf.stem}.txt").write_text(text, encoding="utf-8")
        report.append({"file": pdf.name, "method": method, "quality": round(q, 3), "chars": len(text)})
        print(f"{pdf.name:45s} {method:10s} quality={q:.3f} chars={len(text)}")
    with open(out / "_report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "method", "quality", "chars"])
        w.writeheader()
        w.writerows(report)


if __name__ == "__main__":
    main()
