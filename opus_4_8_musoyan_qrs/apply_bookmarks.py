"""Apply the nested TOC bookmarks from the JSON files onto the Musoyan PDFs and verify.

The JSON page values are 1-based PDF page numbers (vol 1 = printed page + 1,
vol 2 = printed page + 0), which is exactly what PyMuPDF's set_toc expects, so no
offset math happens here. After writing, each output PDF is re-opened and its
outline is read back and compared entry-by-entry against what we set.

Run from anywhere:  python opus_4_8_musoyan_qrs/apply_bookmarks.py
Requires PyMuPDF:   uv pip install pymupdf
"""

import json
import logging
import sys
from pathlib import Path

import fitz  # PyMuPDF

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LOG_DIR = REPO_ROOT / "logs"
OUT_DIR = SCRIPT_DIR / "out_pdf"

# (source pdf, bookmarks json, output pdf)
VOLUMES = [
    ("musoyan_1.pdf", "fixed_bookmarks_1.json", "musoyan_1_bookmarked.pdf"),
    ("musoyan_2.pdf", "fixed_bookmarks_2.json", "musoyan_2_bookmarked.pdf"),
]


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("apply_bookmarks")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # avoid duplicate handlers if imported/re-run
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(LOG_DIR / "apply_bookmarks.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


log = setup_logging()


def build_toc(data: dict, page_count: int) -> list:
    """Flatten the nested JSON into a PyMuPDF TOC list: [[level, title, page], ...].

    Levels: 1 = chapter (or a flat top-level entry like the title page / preface /
    contents), 2 = section, 3 = subsection. Raises loudly on a bad page number.
    """
    toc: list = []

    def add(level: int, title: str, page) -> None:
        if not isinstance(page, int):
            raise TypeError(f"Page for bookmark {title!r} is not an int: {page!r}")
        if not 1 <= page <= page_count:
            raise ValueError(
                f"Bookmark {title!r} points to page {page}, outside 1..{page_count}"
            )
        toc.append([level, title, page])

    for key, value in data.items():
        if isinstance(value, int):
            add(1, key, value)  # flat entry: Տիտղոսաթերթ / Նախաբան / Բովանդակություն
        elif isinstance(value, dict):
            add(1, key, value["page"])  # chapter
            for section_title, section in value["sections"].items():
                add(2, section_title, section["page"])
                for subsection_title, sub_page in section["subsections"].items():
                    add(3, subsection_title, sub_page)
        else:
            raise TypeError(f"Unexpected value type for {key!r}: {type(value).__name__}")
    return toc


def level_counts(toc: list) -> dict:
    counts = {1: 0, 2: 0, 3: 0}
    for level, _title, _page in toc:
        counts[level] += 1
    return counts


def apply_bookmarks(pdf_path: Path, json_path: Path, out_path: Path) -> list:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    doc = fitz.open(pdf_path)
    try:
        toc = build_toc(data, doc.page_count)
        n = doc.set_toc(toc)
        if n != len(toc):
            raise RuntimeError(f"set_toc wrote {n} entries, expected {len(toc)}")
        doc.set_pagemode("UseOutlines")  # show the bookmark panel when the PDF opens
        OUT_DIR.mkdir(exist_ok=True)
        doc.save(out_path, garbage=3, deflate=True)
    finally:
        doc.close()
    return toc


def verify(out_path: Path, expected_toc: list) -> list:
    """Re-open the saved PDF and confirm every bookmark round-trips exactly."""
    doc = fitz.open(out_path)
    try:
        actual = doc.get_toc(simple=True)  # [[level, title, page], ...], pages 1-based
        page_count = doc.page_count
    finally:
        doc.close()

    if len(actual) != len(expected_toc):
        raise AssertionError(
            f"{out_path.name}: TOC length mismatch "
            f"(expected {len(expected_toc)}, read back {len(actual)})"
        )

    mismatches = [
        (i, exp, act)
        for i, (exp, act) in enumerate(zip(expected_toc, actual))
        if exp[:3] != act[:3]
    ]
    if mismatches:
        for i, exp, act in mismatches[:10]:
            log.error(f"  entry {i}: set {exp} -> read {act}")
        raise AssertionError(f"{out_path.name}: {len(mismatches)} bookmark(s) differ")

    for _level, title, page in actual:
        if not 1 <= page <= page_count:
            raise AssertionError(f"{out_path.name}: {title!r} -> page {page} out of range")
    return actual


def main() -> None:
    for pdf_name, json_name, out_name in VOLUMES:
        pdf_path = SCRIPT_DIR / pdf_name
        json_path = SCRIPT_DIR / json_name
        out_path = OUT_DIR / out_name
        for required in (pdf_path, json_path):
            if not required.exists():
                raise FileNotFoundError(f"Missing input: {required}")

        log.info(f"=== {pdf_name} ===")
        toc = apply_bookmarks(pdf_path, json_path, out_path)
        counts = level_counts(toc)
        log.info(
            f"Applied {len(toc)} bookmarks "
            f"(top-level={counts[1]}, sections={counts[2]}, subsections={counts[3]}) "
            f"-> {out_path.relative_to(REPO_ROOT)}"
        )
        verify(out_path, toc)
        log.info(f"Verified: all {len(toc)} bookmarks round-trip correctly")

    log.info("Done: both volumes bookmarked and verified.")


if __name__ == "__main__":
    main()
