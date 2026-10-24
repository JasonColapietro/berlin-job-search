from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from _common import json_text, markdown_table, strip_html, write_output


STOPWORDS = set(
    "a about above after again all also am an and any are as at be because been before being "
    "below between both but by can could did do does doing down during each few for from further "
    "had has have having he her here hers herself him himself his how i if in into is it its itself "
    "just me more most my myself no nor not of off on once only or other our ours ourselves out over "
    "own same she should so some such than that the their theirs them themselves then there these "
    "they this those through to too under until up very was we were what when where which while who "
    "whom why will with would you your yours yourself yourselves "
    "aber als am an auch auf aus bei das dass dem den der des die doch durch ein eine einem einen "
    "einer eines für gegen hat im in ist mit nach nicht oder sein sie sind und von vor wie zu zum zur "
    "über unter die das der den dem des ein eine einer einem eines auf für mit ohne bei nach seit "
    "und oder aber nicht kein keine keinen keinem keiner"
    .split()
)
TOKEN_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9][A-Za-zÄÖÜäöüß0-9+#./-]*")
GENDER_TAG = re.compile(
    r"\(\s*(?:m\s*/\s*w\s*/\s*d|w\s*/\s*m\s*/\s*d|f\s*/\s*m\s*/\s*x|all\s+genders?)\s*\)",
    re.I,
)
MONTH_DATE = r"(?:0?[1-9]|1[0-2])([/.])(\d{4})"
YEAR_DATE = r"\d{4}"
PERIOD_RE = re.compile(
    r"(?<!\d)(?P<start>" + MONTH_DATE + "|" + YEAR_DATE + r")\s*[–—-]\s*"
    r"(?P<end>" + MONTH_DATE + "|" + YEAR_DATE + r"|heute|present|today|now)(?!\d)",
    re.I,
)
EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
PHONE_RE = re.compile(r"(?<!\w)(?:\+\s?\d{1,3}[\s()./-]*)?(?:\d[\s()./-]*){7,}\d(?!\w)")


def extract_pdf_text(path: Path) -> tuple[str, Optional[int]]:
    try:
        from pypdf import PdfReader
    except ImportError:
        PdfReader = None
    if PdfReader is not None:
        try:
            reader = PdfReader(str(path))
            pages = list(reader.pages)
            text = "\n".join(page.extract_text() or "" for page in pages)
            has_image = False
            for page in pages:
                try:
                    has_image = has_image or bool(page.images)
                except Exception:
                    pass
            if has_image:
                text += "\nPhoto: present"
            return text, len(pages)
        except Exception as error:
            pdf_error = str(error)
        else:
            pdf_error = ""
    else:
        pdf_error = ""

    executable = shutil.which("pdftotext")
    if executable:
        result = subprocess.run(
            [executable, "-layout", str(path), "-"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or "pdftotext failed"
            raise ValueError(detail)
        pages = result.stdout.split("\f")
        if pages and not pages[-1].strip():
            pages.pop()
        return result.stdout, len(pages)
    message = "install pypdf or poppler-utils, or check the HTML instead"
    if pdf_error:
        message = "{} (PDF extraction failed: {})".format(message, pdf_error)
    raise ValueError(message)


def strip_markdown(text: str) -> str:
    lines = text.splitlines()
    metadata_text = []
    if lines and lines[0].strip() == "---":
        end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
        if end is not None:
            for line in lines[1:end]:
                key, separator, value = line.partition(":")
                if separator and value.strip():
                    metadata_text.append("{}: {}".format(key.strip().replace("_", " "), value.strip().replace("\\n", " ")))
            lines = lines[end + 1:]
    text = "\n".join(metadata_text + lines)
    has_markdown_photo = bool(re.search(r"!\[[^\]]*\]\([^)]+\)", text))
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"^\s*\|?[\s:|-]+\|?\s*$", " ", text, flags=re.M)
    text = text.replace("|", " ")
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda match: match.group(1) or match.group(2), text)
    text = re.sub(r"(?<!\w)(\*|_)(.+?)\1(?!\w)", r"\2", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    result = strip_html(html.unescape(text))
    return result + ("\nPhoto: present" if has_markdown_photo else "")


def extract_text(path: Path) -> tuple[str, Optional[int]]:
    suffix = path.suffix.casefold()
    if suffix == ".pdf":
        return extract_pdf_text(path)
    text = path.read_text(encoding="utf-8")
    if suffix in {".html", ".htm"}:
        has_photo = bool(re.search(r"<\s*img\b", text, re.I))
        extracted = strip_html(text)
        return extracted + ("\nPhoto: present" if has_photo else ""), None
    if suffix == ".md":
        return strip_markdown(text), None
    raise ValueError("document must have an .md, .html, or .pdf extension")


def parse_endpoint(value: str, *, is_end: bool) -> tuple[int, str]:
    value = value.strip()
    folded = value.casefold()
    current = dt.date.today()
    if folded in {"heute", "present", "today", "now"}:
        return current.year * 12 + current.month - 1, "current"
    month_match = re.fullmatch(r"(0?[1-9]|1[0-2])([/.])(\d{4})", value)
    if month_match:
        month = int(month_match.group(1))
        year = int(month_match.group(3))
        return year * 12 + month - 1, "MM" + month_match.group(2) + "YYYY"
    if re.fullmatch(YEAR_DATE, value):
        year = int(value)
        return year * 12 + (11 if is_end else 0), "YYYY"
    raise ValueError("invalid period endpoint")


def find_periods(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    periods = []
    formats = set()
    for match in PERIOD_RE.finditer(text):
        start_text, end_text = match.group("start"), match.group("end")
        try:
            start, start_format = parse_endpoint(start_text, is_end=False)
            end, end_format = parse_endpoint(end_text, is_end=True)
        except ValueError:
            continue
        if end < start:
            continue
        periods.append({
            "start": start,
            "end": end,
            "label": match.group(0),
            "formats": (start_format, end_format),
        })
        formats.update(value for value in (start_format, end_format) if value != "current")
    periods.sort(key=lambda item: (item["start"], item["end"]))
    gaps = []
    for previous, following in zip(periods, periods[1:]):
        silent_months = following["start"] - previous["end"] - 1
        if silent_months > 2:
            gaps.append("{} → {} ({} months)".format(
                previous["label"], following["label"], silent_months,
            ))
    return periods, gaps + (["mixed date formats: {}".format(", ".join(sorted(formats)))] if len(formats) > 1 else [])


def derive_keywords(text: str, limit: int = 25) -> list[str]:
    cleaned = GENDER_TAG.sub(" ", text)
    cleaned = re.sub(r"(?<!\d)\d{1,2}[/.]\d{4}(?!\d)", " ", cleaned)
    first_seen: dict[str, int] = {}
    spellings: dict[str, str] = {}
    tokens = []
    for match in TOKEN_RE.finditer(cleaned):
        raw = match.group(0).strip("./-")
        if not raw:
            continue
        folded = raw.casefold()
        if folded in STOPWORDS or re.fullmatch(r"(?:m|w|d|f|x)(?:/(?:m|w|d|f|x)){1,2}", folded):
            continue
        first_seen.setdefault(folded, len(tokens))
        spellings.setdefault(folded, raw)
        tokens.append((folded, raw, match.start(), match.end()))

    frequencies = collections.Counter(token for token, _, _, _ in tokens)
    tech = {
        folded for folded, raw, _, _ in tokens
        if any(char.isupper() for char in raw) or any(char.isdigit() for char in raw)
        or any(char in "+#." for char in raw)
    }
    candidates: dict[str, tuple[int, int, bool, str]] = {}
    for folded, count in frequencies.items():
        if count >= 2 or folded in tech:
            candidates[folded] = (
                count, first_seen[folded], folded in tech, spellings[folded],
            )

    bigrams = []
    for left, right in zip(tokens, tokens[1:]):
        separator = cleaned[left[3]:right[2]]
        if separator and separator.isspace():
            bigrams.append("{} {}".format(left[0], right[0]))
    bigram_counts = collections.Counter(bigrams)
    for phrase, count in bigram_counts.items():
        if count >= 2:
            candidates[phrase] = (count, first_seen.get(phrase.split()[0], 0), False, phrase)

    ordered = sorted(
        candidates.items(),
        key=lambda item: (-int(item[1][2]), -item[1][0], item[1][1], item[0]),
    )
    return [value[3] for _, value in ordered[:limit]]


def keyword_check(text: str, keywords: list[str]) -> dict[str, Any]:
    if not keywords:
        return {
            "check": "keywords",
            "status": "info",
            "detail": {"coverage_pct": None, "found": [], "missing": [], "message": "No keywords or JD supplied."},
        }
    found, missing = [], []
    for keyword in keywords:
        words = [part for part in keyword.split() if part]
        pattern = r"(?<!\w)" + r"\s+".join(re.escape(word) for word in words) + r"(?!\w)"
        (found if re.search(pattern, text, re.I) else missing).append(keyword)
    coverage = round(100 * len(found) / len(keywords))
    return {
        "check": "keywords",
        "status": "ok" if not missing else "warn",
        "detail": {
            "coverage_pct": coverage,
            "found": found,
            "missing": missing,
        },
    }


def check_contact(text: str) -> dict[str, Any]:
    without_dates = PERIOD_RE.sub(" ", text)
    without_dates = re.sub(r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b", " ", without_dates)
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(without_dates)
    missing = []
    if not emails:
        missing.append("email")
    if not phones:
        missing.append("phone")
    return {
        "check": "contact",
        "status": "ok" if not missing else "fail",
        "detail": {
            "email_present": bool(emails),
            "phone_present": bool(phones),
            "missing": missing,
        },
    }


def check_sections(text: str) -> dict[str, Any]:
    required = {
        "experience": r"\b(?:berufserfahrung|berufliche\s+erfahrung|experience|work\s+experience)\b",
        "education": r"\b(?:ausbildung|bildung|education|academic\s+background)\b",
        "skills": r"\b(?:kenntnisse|fähigkeiten|faehigkeiten|skills|technical\s+skills)\b",
    }
    missing = [name for name, pattern in required.items() if not re.search(pattern, text, re.I)]
    return {
        "check": "sections",
        "status": "ok" if not missing else "fail",
        "detail": {"required": list(required), "missing": missing},
    }


def check_dates(text: str) -> dict[str, Any]:
    periods, problems = find_periods(text)
    format_problem = any(item.startswith("mixed date formats") for item in problems)
    gap_problems = [item for item in problems if not item.startswith("mixed date formats")]
    if not periods:
        status = "warn"
    elif problems:
        status = "warn"
    else:
        status = "ok"
    return {
        "check": "dates",
        "status": status,
        "detail": {
            "periods": [item["label"] for item in periods],
            "mixed_formats": format_problem,
            "gaps": gap_problems,
            "message": "No employment periods found." if not periods else "",
        },
    }


def check_length(document_type: str, words: int, pages: Optional[int]) -> dict[str, Any]:
    threshold = 900 if document_type == "cv" else 400
    if pages is not None:
        page_limit = 2 if document_type == "cv" else 1
        status = "warn" if pages > page_limit else "ok"
        detail = {"pages": pages, "recommended_max": page_limit}
    else:
        status = "warn" if words > threshold else "ok"
        detail = {"words": words, "recommended_max": threshold, "basis": "word count"}
    return {"check": "length", "status": status, "detail": detail}


def check_personal_data(text: str) -> dict[str, Any]:
    patterns = {
        "photo": r"\b(?:photo|foto|portrait|bild)\b|<\s*img\b",
        "birth_date": r"\b(?:birth\s*date|date\s+of\s+birth|geburtsdatum|geboren\s+am)\b",
        "marital_status": r"\b(?:marital\s+status|familienstand|married|ledig|verheiratet)\b",
        "nationality": r"\b(?:nationality|staatsangehörigkeit|staatsangehoerigkeit|citizenship)\b",
    }
    present = [name for name, pattern in patterns.items() if re.search(pattern, text, re.I)]
    return {
        "check": "personal_data",
        "status": "info",
        "detail": {
            "present": present,
            "message": "Common for traditional German employers; optional for international/startup roles.",
        },
    }


def check_letter(text: str, pages: Optional[int]) -> list[dict[str, Any]]:
    checks = []
    subject = bool(re.search(r"\b(?:betreff|subject|re)\s*:", text, re.I))
    salutation = bool(re.search(r"\b(?:sehr geehrte[rs]?|guten tag|dear)\b", text, re.I))
    closing = bool(re.search(
        r"\b(?:mit freundlichen grüßen|mit freundlichen gruessen|kind regards|best regards)\b",
        text,
        re.I,
    ))
    checks.extend([
        {
            "check": "letter_subject",
            "status": "ok" if subject else "fail",
            "detail": {"present": subject},
        },
        {
            "check": "letter_salutation",
            "status": "ok" if salutation else "fail",
            "detail": {"present": salutation},
        },
        {
            "check": "letter_closing",
            "status": "ok" if closing else "fail",
            "detail": {"present": closing},
        },
    ])
    if pages is None:
        status = "warn"
        detail = {"pages": None, "recommended_max": 1, "message": "Page count unavailable."}
    else:
        status = "ok" if pages <= 1 else "fail"
        detail = {"pages": pages, "recommended_max": 1}
    checks.append({"check": "letter_pages", "status": status, "detail": detail})
    return checks


def analyze_document(
    text: str,
    document_type: str,
    pages: Optional[int],
    keywords: list[str],
) -> dict[str, Any]:
    words = len(re.findall(r"\b[\w+#./-]+\b", text, re.UNICODE))
    checks = [check_length(document_type, words, pages), keyword_check(text, keywords)]
    if document_type == "cv":
        checks.extend([check_contact(text), check_sections(text), check_dates(text), check_personal_data(text)])
    else:
        checks.extend(check_letter(text, pages))
    scored = [item for item in checks if item["status"] != "info"]
    score = round(100 * sum(item["status"] == "ok" for item in scored) / len(scored)) if scored else 100
    return {"score": score, "checks": checks}


def format_markdown(summary: dict[str, Any]) -> str:
    rows = [
        [item["check"], item["status"], json_text(item["detail"], indent=None, sort_keys=True)]
        for item in summary["checks"]
    ]
    return "\n".join([
        "# ATS check",
        "",
        "**Score:** {}%".format(summary["score"]),
        "",
        markdown_table(["Check", "Status", "Detail"], rows),
    ])


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check an application document for ATS readability and completeness.")
    parser.add_argument("document", metavar="DOC(.md|.html|.pdf)")
    parser.add_argument("--type", choices=("cv", "letter"), default="cv")
    parser.add_argument("--jd", help="Fictional or target job-description file for keyword derivation")
    parser.add_argument("--keywords", help="Comma-separated target keywords")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args(argv)
    try:
        text, pages = extract_text(Path(args.document))
        keywords = [item.strip() for item in (args.keywords or "").split(",") if item.strip()]
        if args.jd:
            jd_text, _ = extract_text(Path(args.jd))
            if not keywords:
                keywords = derive_keywords(jd_text)
        summary = analyze_document(text, args.type, pages, keywords)
        output = json_text(summary) if args.format == "json" else format_markdown(summary)
        write_output(output)
        return 0
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as error:
        print("error: {}".format(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
