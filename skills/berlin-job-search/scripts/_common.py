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

CITY_ALIASES = {
    "munich": {
        "key": "munich",
        "canonical": "Munich",
        "ba": "München",
        "linkedin": "Munich, Germany",
        "geo_id": "100495942",
        "variants": ("München", "Munich", "Muenchen"),
    },
    "cologne": {
        "key": "cologne",
        "canonical": "Cologne",
        "ba": "Köln",
        "linkedin": "Cologne, Germany",
        "geo_id": "90009713",
        "variants": ("Köln", "Cologne", "Koeln", "Cologne/Bonn"),
    },
    "nuremberg": {
        "key": "nuremberg",
        "canonical": "Nuremberg",
        "ba": "Nürnberg",
        "linkedin": "Nuremberg, Germany",
        "geo_id": None,
        "variants": ("Nürnberg", "Nuremberg", "Nuernberg"),
    },
    "frankfurt": {
        "key": "frankfurt",
        "canonical": "Frankfurt",
        "ba": "Frankfurt am Main",
        "linkedin": "Frankfurt am Main, Germany",
        "geo_id": "90009714",
        "variants": ("Frankfurt", "Frankfurt am Main", "Frankfurt/Rhine-Main"),
    },
    "dusseldorf": {
        "key": "dusseldorf",
        "canonical": "Düsseldorf",
        "ba": "Düsseldorf",
        "linkedin": "Düsseldorf, Germany",
        "geo_id": None,
        "variants": ("Düsseldorf", "Duesseldorf"),
    },
    "hamburg": {
        "key": "hamburg",
        "canonical": "Hamburg",
        "ba": "Hamburg",
        "linkedin": "Hamburg, Germany",
        "geo_id": "101949806",
        "variants": ("Hamburg",),
    },
    "berlin": {
        "key": "berlin",
        "canonical": "Berlin",
        "ba": "Berlin",
        "linkedin": "Berlin, Germany",
        "geo_id": "103035651",
        "variants": ("Berlin",),
    },
    "stuttgart": {
        "key": "stuttgart",
        "canonical": "Stuttgart",
        "ba": "Stuttgart",
        "linkedin": "Stuttgart, Germany",
        "geo_id": None,
        "variants": ("Stuttgart",),
    },
    "leipzig": {
        "key": "leipzig",
        "canonical": "Leipzig",
        "ba": "Leipzig",
        "linkedin": "Leipzig, Germany",
        "geo_id": None,
        "variants": ("Leipzig",),
    },
    "dresden": {
        "key": "dresden",
        "canonical": "Dresden",
        "ba": "Dresden",
        "linkedin": "Dresden, Germany",
        "geo_id": None,
        "variants": ("Dresden",),
    },
    "hannover": {
        "key": "hannover",
        "canonical": "Hanover",
        "ba": "Hannover",
        "linkedin": "Hanover, Germany",
        "geo_id": None,
        "variants": ("Hannover", "Hanover"),
    },
    "germany": {
        "key": "germany",
        "canonical": "Germany",
        "ba": "Deutschland",
        "linkedin": "Germany",
        "geo_id": "101282230",
        "variants": ("Germany", "Deutschland"),
    },
}


def _normalized_city_text(value: Any) -> str:
    folded = unicodedata.normalize("NFKD", str(value or "").casefold())
    unaccented = "".join(char for char in folded if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", unaccented))


def city_alias(value: Any) -> Optional[dict[str, Any]]:
    normalized = _normalized_city_text(value)
    if not normalized:
        return None
    for alias in CITY_ALIASES.values():
        for variant in alias["variants"]:
            candidate = _normalized_city_text(variant)
            if normalized == candidate or normalized.startswith(candidate + " "):
                return alias
    return None


def ba_location_name(value: Any) -> str:
    alias = city_alias(value)
    return str(alias["ba"]) if alias else str(value or "")


def canonical_location_name(value: Any) -> str:
    alias = city_alias(value)
    if alias:
        return str(alias["canonical"])
    return str(value or "")


def linkedin_location_and_geo_id(value: Any) -> tuple[str, Optional[str]]:
    alias = city_alias(value)
    if alias:
        return str(alias["linkedin"]), alias.get("geo_id")
    return str(value or ""), None


def city_location_matches(query: Any, location: Any) -> bool:
    if not query:
        return True
    alias = city_alias(query)
    variants = alias["variants"] if alias else (str(query),)
    normalized_location = " " + _normalized_city_text(location) + " "
    return any(
        " " + _normalized_city_text(variant) + " " in normalized_location
        for variant in variants
        if _normalized_city_text(variant)
    )


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
