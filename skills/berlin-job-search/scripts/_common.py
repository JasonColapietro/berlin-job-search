from __future__ import annotations

import csv
import datetime as dt
import html
import io
import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Optional

USER_AGENT = "berlin-job-search-skill/0.1 (+https://github.com/umutyesildal/berlin-job-search)"


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def strip_html(text: str) -> str:
    parser = TextExtractor()
    try:
        parser.feed(text)
        return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    except Exception:
        return re.sub(r"<[^>]+>", " ", text)


def unescape_html(text: str) -> str:
    return html.unescape(text)


def clean_html_fragment(markup: str) -> str:
    return unescape_html(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", markup).strip()))


def escape_html(value: Any, *, quote: bool = True) -> str:
    return html.escape(str(value), quote=quote)


def plain(value: Any) -> str:
    return "" if value is None else strip_html(html.unescape(str(value)))


def request_bytes(
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    timeout: float = 20,
) -> tuple[int, bytes]:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/plain, */*"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def request_json(url: str, *, headers: Optional[dict[str, str]] = None) -> Any:
    status, body = request_bytes(url, headers=headers)
    if status < 200 or status >= 300:
        raise RuntimeError("HTTP {}".format(status))
    return json.loads(body.decode("utf-8-sig"))


def salary_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, dict):
        minimum = value.get("minValue") or value.get("min")
        maximum = value.get("maxValue") or value.get("max")
        currency = value.get("currency") or value.get("currencyCode") or "EUR"
        if minimum is not None and maximum is not None:
            value = "{}–{} {}".format(minimum, maximum, currency)
        elif minimum is not None:
            value = "from {} {}".format(minimum, currency)
        else:
            value = value.get("label") or value.get("summary") or ""
    text = plain(value)
    if text.casefold() in {"", "keine_angaben", "keine angaben", "not disclosed", "n/a", "none"}:
        return None
    return text if re.search(r"\d", text) else None


def source_date(value: Any) -> Optional[str]:
    if not value:
        return None
    text = str(value).strip()
    try:
        if re.fullmatch(r"\d{10,13}", text):
            stamp = int(text) // 1000 if len(text) == 13 else int(text)
            return dt.datetime.fromtimestamp(stamp, dt.timezone.utc).date().isoformat()
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", text):
            return dt.datetime.strptime(text, "%d.%m.%Y").date().isoformat()
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def parse_date_or_none(value: Any) -> Optional[dt.date]:
    try:
        return dt.date.fromisoformat(str(value or ""))
    except ValueError:
        return None


def canonical_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_") and key.casefold() not in {"fbclid", "gclid"}
    ]
    return urllib.parse.urlunsplit((
        parsed.scheme.casefold(), parsed.netloc.casefold(), parsed.path.rstrip("/"),
        urllib.parse.urlencode(sorted(query)), "",
    ))


def normalize_identity(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(char for char in folded if not unicodedata.combining(char))
    text = re.sub(r"\((?:m\s*/\s*w\s*/\s*d|f\s*/\s*m\s*/\s*x|all genders)\)", " ", text, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "", text)


def slugify(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")[:60] or "job"


def json_text(value: Any, *, indent: Optional[int] = 2, sort_keys: bool = False) -> str:
    return json.dumps(value, ensure_ascii=False, indent=indent, sort_keys=sort_keys)


def csv_text(rows: list[dict[str, Any]], fields: list[str]) -> str:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def markdown_table(
    headers: list[str],
    rows: list[list[Any]],
    *,
    separators: Optional[list[str]] = None,
    spaced_separator: bool = False,
    normalize_newlines: bool = True,
) -> str:
    divider = separators or ["---"] * len(headers)
    if spaced_separator:
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(divider) + " |"]
    else:
        lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(divider) + "|"]
    for row in rows:
        cells = []
        for value in row:
            cell = str(value or "").replace("|", "\\|")
            if normalize_newlines:
                cell = cell.replace("\n", " ")
            cells.append(cell)
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_output(text: str, path: Optional[str] = None) -> None:
    print(text)
    if path:
        Path(path).write_text(text, encoding="utf-8")
