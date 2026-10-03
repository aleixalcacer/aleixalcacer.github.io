"""
sync.py — Descarga el CVN desde FECYT y genera src/data/cv.json para Astro.

Uso:
    python scripts/sync.py
"""

from __future__ import annotations

import json
import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STOP = {"a", "an", "the", "and", "or", "of", "in", "on", "for", "to", "by",
         "vs", "via", "with", "from", "at", "el", "la", "de", "en", "y"}
_ACRONYMS = {"ieee", "plos", "acm", "mit", "uji", "ods", "ai", "ml", "hpc",
             "sdg", "sdgs", "tfg", "tfm", "stem", "ict"}


def _titlecase(s: str) -> str:
    words = s.split()
    out = []
    for i, w in enumerate(words):
        low = w.lower()
        if low in _ACRONYMS:
            out.append(w.upper())
        elif i == 0 or low not in _STOP:
            out.append(w.capitalize())
        else:
            out.append(low)
    return " ".join(out)


def _fix_caps(s: str) -> str:
    """Convert ALL-CAPS titles to title case; leave mixed-case strings untouched."""
    if not s:
        return s
    alpha = [c for c in s if c.isalpha()]
    if not alpha:
        return s
    if sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.75:
        return _titlecase(s)
    return s


_TITLE_FIELDS: dict[str, list[str]] = {
    "articles":            ["title"],
    "chapters":            ["title"],
    "conferences":         ["title"],
    "teaching_articles":   ["title"],
    "teaching_conferences": ["title"],
    "teaching_others":     ["title"],
    "research_lines":      ["title"],
    "projects":            ["title"],
    "contracts":           ["title"],
    "teaching_projects":   ["title"],
    "theses":              ["title"],
    "awards":              ["title"],
    "accreditations":      ["title"],
}


def normalize_titles(data: dict) -> dict:
    """Apply _fix_caps to title fields across all sections."""
    result = {}
    for section, items in data.items():
        fields = _TITLE_FIELDS.get(section)
        if fields is None or not isinstance(items, list):
            result[section] = items
            continue
        normalized = []
        for item in items:
            item = dict(item)
            for field in fields:
                val = item.get(field, "")
                if val and isinstance(val, str):
                    item[field] = _fix_caps(val)
            normalized.append(item)
        result[section] = normalized
    return result


def _text(elem: ET.Element | None, *path: str) -> str:
    if elem is None:
        return ""
    node = elem
    for tag in path:
        node = node.find(tag)
        if node is None:
            return ""
    return (node.text or "").strip()


def _find_link(item: ET.Element, code: str) -> ET.Element | None:
    for link in item.findall("Link"):
        c = _text(link, "CvnItemID", "CodeCVNItem", "Item")
        if c == code:
            return link
    return None


def _items(root: ET.Element, code: str):
    """Yield CvnItem elements matching the given CVN code."""
    for item in root.findall("CvnItem"):
        if _text(item, "CvnItemID", "CVNPK", "Item") == code:
            yield item


def _institution(item: ET.Element) -> str:
    """Return the first Entity name, or empty string."""
    entities = item.findall("Entity")
    return _text(entities[0], "EntityName", "Item") if entities else ""


def _hours(item: ET.Element) -> str:
    """Parse PT{n}H duration from Date/Duration/Item, return hours string."""
    raw = _text(item, "Date", "Duration", "Item")
    if raw:
        m = re.match(r"PT(\d+)H", raw)
        if m:
            return m.group(1)
    return ""


def _format_authors(item: ET.Element) -> str:
    authors = []
    for a in item.findall("Author"):
        order_el = a.find("SignatureOrder/Item")
        order = int(order_el.text) if order_el is not None and (order_el.text or "").strip() else 99
        gn = _text(a, "GivenName", "Item")
        fn = _text(a, "FirstFamilyName", "Item")
        if fn and gn:
            authors.append((order, f"{fn}, {gn[0]}."))
    authors.sort(key=lambda x: x[0])
    names = [n for _, n in authors]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " & " + names[-1]


def _doi_from_url(url: str) -> str:
    m = re.search(r"doi\.org/(.+)", url)
    return m.group(1) if m else ""


def _to_year(raw: str) -> str:
    return raw[:4] if raw else ""


def _date_start(item: ET.Element) -> str:
    raw = (_text(item, "Date", "StartDate", "DayMonthYear", "Item")
           or _text(item, "Date", "OnlyDate", "DayMonthYear", "Item")
           or _text(item, "Date", "OnlyDate", "Year", "Item"))
    return _to_year(raw)


def _date_end(item: ET.Element) -> str:
    raw = (_text(item, "Date", "EndDate", "DayMonthYear", "Item")
           or _text(item, "Date", "EndDate", "Year", "Item"))
    return _to_year(raw)


def _year(el: ET.Element) -> str:
    raw = (_text(el, "Date", "OnlyDate", "Year", "Item")
           or _text(el, "Date", "StartDate", "DayMonthYear", "Item")
           or _text(el, "Date", "OnlyDate", "DayMonthYear", "Item"))
    return _to_year(raw)


# ---------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------

def extract_personal(root: ET.Element) -> dict:
    agent = root.find("Agent")
    if agent is None:
        return {}
    name_parts = [
        _text(agent, "Identification", "PersonalIdentification", "GivenName", "Item"),
        _text(agent, "Identification", "PersonalIdentification", "FirstFamilyName", "Item"),
        _text(agent, "Identification", "PersonalIdentification", "SecondFamilyName", "Item"),
    ]
    orcid = ""
    for ext in agent.findall(".//ExternalPK"):
        if _text(ext, "Type", "Item") == "140":
            orcid = _text(ext, "Code", "Item")
    return {
        "name": " ".join(p for p in name_parts if p),
        "orcid": orcid,
        "web": _text(agent, "Contact", "PersonalWeb", "Item"),
    }


def extract_experience(root: ET.Element) -> list[dict]:
    results = []
    for code in ("010.010.000.000", "010.020.000.000"):
        for item in _items(root, code):
            results.append({
                "current": code == "010.010.000.000",
                "role": _text(item, "Title", "Name", "Item"),
                "institution": _institution(item),
                "start": _date_start(item),
                "end": _date_end(item),
            })
    results.sort(key=lambda x: x["start"], reverse=True)
    return results


def extract_education(root: ET.Element) -> list[dict]:
    order = {"020.010.020.000": 0, "020.010.030.000": 1, "020.010.010.000": 2}
    results = []
    for item in root.findall("CvnItem"):
        code = _text(item, "CvnItemID", "CVNPK", "Item")
        if code not in order:
            continue
        thesis = ""
        if code == "020.010.020.000":
            link = _find_link(item, "010")
            if link is not None:
                thesis = _text(link, "Title", "Name", "Item")
        end = (_date_end(item)
               or _to_year(_text(item, "Date", "OnlyDate", "Year", "Item"))
               or _to_year(_text(item, "Date", "EndDate", "OnlyDate", "Year", "Item")))
        results.append({
            "_order": order[code],
            "degree": _text(item, "Title", "Name", "Item"),
            "institution": _institution(item),
            "end": end,
            "thesis": thesis,
        })
    results.sort(key=lambda x: x["_order"])
    for r in results:
        del r["_order"]
    return results


def extract_projects(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "050.020.010.000"):
        budget_el = item.find("EconomicDimension")
        budget = ""
        if budget_el is not None:
            val = _text(budget_el, "Value", "Item")
            cur = _text(budget_el, "CurrencyType", "Item") or "EUR"
            if val:
                budget = f"{int(float(val)):,} {cur}"
        results.append({
            "title": _text(item, "Title", "Name", "Item"),
            "institution": _institution(item),
            "start": _date_start(item),
            "end": _date_end(item),
            "budget": budget,
        })
    results.sort(key=lambda x: x["start"], reverse=True)
    return results


def extract_articles(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "060.010.010.000"):
        url = _text(item, "Url", "Value", "Item")
        results.append({
            "authors": _format_authors(item),
            "year": _text(item, "Date", "OnlyDate", "Year", "Item"),
            "title": _text(item, "Title", "Name", "Item"),
            "journal": _titlecase(_text(item, "Link", "Title", "Name", "Item")),
            "volume": _text(item, "Location", "Volume", "Item"),
            "number": _text(item, "PhysicalDimension", "Value", "Item"),
            "doi": _doi_from_url(url),
        })
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def extract_chapters(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "060.010.030.000"):
        link = _find_link(item, "110")
        book = _text(link, "Title", "Name", "Item") if link else ""
        url = _text(item, "Url", "Value", "Item")
        year = (_text(item, "Date", "OnlyDate", "Year", "Item")
                or _text(item, "Date", "OnlyDate", "DayMonthYear", "Item")[:4])
        results.append({
            "authors": _format_authors(item),
            "year": year,
            "title": _text(item, "Title", "Name", "Item"),
            "book": book,
            "doi": _doi_from_url(url),
        })
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def extract_conferences(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "060.010.020.000"):
        link = _find_link(item, "110")
        year = conf_name = city = ""
        if link is not None:
            conf_name = _text(link, "Title", "Name", "Item")
            year = _year(link)
            city = _text(link, "Place", "City", "Item")
        results.append({
            "authors": _format_authors(item),
            "year": year,
            "title": _text(item, "Title", "Name", "Item"),
            "conference": conf_name,
            "location": city,
        })
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def extract_teaching(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "030.010.000.000"):
        end = _date_end(item)
        results.append({
            "course": _text(item, "Title", "Name", "Item"),
            "degree": _text(item, "Link", "Title", "Name", "Item"),
            "credits": _text(item, "PhysicalDimension", "Value", "Item"),
            "year": end[:4] if end else "",
        })
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def extract_awards(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "060.030.080.000"):
        date = _date_start(item)
        results.append({
            "title": _text(item, "Title", "Name", "Item"),
            "description": _text(item, "Description", "Item"),
            "institution": _institution(item),
            "year": date[:4] if date else "",
        })
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def extract_research_stays(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "060.010.050.000"):
        results.append({
            "institution": _institution(item),
            "start": _date_start(item),
            "end": _date_end(item),
            "description": _text(item, "Description", "Item"),
        })
    results.sort(key=lambda x: x["start"], reverse=True)
    return results


def extract_grants(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "060.030.010.000"):
        if _text(item, "Filter", "Value", "Item") != "710":
            continue
        date = _text(item, "Date", "OnlyDate", "DayMonthYear", "Item")
        results.append({
            "reference": _text(item, "Title", "Name", "Item"),
            "institution": _institution(item),
            "year": date[:4] if date else "",
        })
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def extract_reviews(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "060.020.060.000"):
        role_el = item.find("Roll")
        role = ""
        if role_el is not None:
            role = _text(role_el, "Others", "Item") or _text(role_el, "Value", "Item")
        results.append({
            "institution": _institution(item),
            "role": role,
        })
    return results


def extract_accreditations(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "060.030.090.000"):
        date = _text(item, "Date", "OnlyDate", "DayMonthYear", "Item")
        results.append({
            "title": _text(item, "Title", "Name", "Item"),
            "institution": _institution(item),
            "year": date[:4] if date else "",
        })
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def extract_teaching_training(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "020.050.000.000"):
        results.append({
            "title": _text(item, "Title", "Name", "Item"),
            "institution": _institution(item),
            "hours": _hours(item),
        })
    return results


def extract_languages(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "020.060.000.000"):
        name = _text(item, "Title", "Name", "Item")
        if name:
            results.append({
                "name": name,
                "level": _text(item, "Quality", "Measure", "Item"),
            })
    return results


def extract_research_lines(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "050.010.000.000"):
        supervisor = ""
        for author in item.findall("Author"):
            gn = _text(author, "GivenName", "Item")
            fn = _text(author, "FirstFamilyName", "Item")
            sn = _text(author, "SecondFamilyName", "Item")
            if fn:
                supervisor = f"{gn} {fn} {sn}".strip()
                break
        results.append({
            "title": _text(item, "Title", "Name", "Item"),
            "description": _text(item, "Description", "Item"),
            "institution": _institution(item),
            "supervisor": supervisor,
            "since": _date_start(item),
        })
    return results


def extract_theses(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "030.040.000.000"):
        results.append({
            "title": _text(item, "Title", "Name", "Item"),
            "institution": _institution(item),
            "start": _date_start(item),
            "end": _date_end(item),
        })
    results.sort(key=lambda x: (x["start"], x["end"]), reverse=True)
    return results


def extract_teaching_projects(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "030.080.000.000"):
        results.append({
            "title": _text(item, "Title", "Name", "Item"),
            "institution": _institution(item),
            "start": _date_start(item),
            "end": _date_end(item),
        })
    results.sort(key=lambda x: x["end"], reverse=True)
    return results


def extract_contracts(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "050.020.020.000"):
        results.append({
            "title": _text(item, "Title", "Name", "Item"),
            "description": _text(item, "Description", "Item"),
            "institution": _institution(item),
            "start": _date_start(item),
            "end": _date_end(item),
        })
    results.sort(key=lambda x: x["start"], reverse=True)
    return results


def extract_specialized_training(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "020.020.000.000"):
        raw_year = (_text(item, "Date", "EndDate", "Year", "Item")
                    or _text(item, "Date", "EndDate", "DayMonthYear", "Item")
                    or _text(item, "Date", "StartDate", "DayMonthYear", "Item"))
        results.append({
            "title": _text(item, "Title", "Name", "Item"),
            "institution": _institution(item),
            "hours": _hours(item),
            "year": _to_year(raw_year),
        })
    return results


def extract_teaching_articles(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "030.070.000.000"):
        if _text(item, "Subtype", "SubType1", "Item") != "123":
            continue
        link = item.find("Link")
        if link is None:
            continue
        doi = ""
        for pk in item.findall("ExternalPK"):
            if _text(pk, "Type", "Item") == "040":
                doi = _text(pk, "Code", "Item")
        results.append({
            "authors": _format_authors(item),
            "year": _year(link),
            "title": _text(link, "Title", "Name", "Item"),
            "journal": _text(link, "Link", "Title", "Name", "Item"),
            "doi": doi,
        })
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def extract_teaching_conferences(root: ET.Element) -> list[dict]:
    results = []

    for item in _items(root, "030.090.000.000"):
        link = item.find("Link")
        if link is None:
            continue
        title = _text(link, "Title", "Name", "Item")
        if not title:
            continue
        results.append({
            "authors": _format_authors(item),
            "year": _year(link) or _date_start(item),
            "title": title,
            "conference": _text(item, "Description", "Item"),
        })

    for item in _items(root, "030.070.000.000"):
        if _text(item, "Subtype", "SubType1", "Item") != "112":
            continue
        link = item.find("Link")
        if link is None:
            continue
        results.append({
            "authors": _format_authors(item),
            "year": _year(link),
            "title": _text(link, "Title", "Name", "Item"),
            "conference": _text(link, "Entity", "EntityName", "Item"),
        })

    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def extract_teaching_others(root: ET.Element) -> list[dict]:
    results = []
    for item in _items(root, "030.070.000.000"):
        if _text(item, "Subtype", "SubType1", "Item") in ("112", "123"):
            continue
        link = item.find("Link")
        if link is None:
            continue
        results.append({
            "authors": _format_authors(item),
            "year": _year(link),
            "title": _text(link, "Title", "Name", "Item"),
            "venue": _text(link, "Entity", "EntityName", "Item"),
        })
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _read_orcid() -> str:
    config = tomllib.loads(Path("pyproject.toml").read_text("utf-8"))
    return config["tool"]["cvn"]["orcid"]


def main() -> None:
    from cvn import fetch_cvn_xml

    orcid = _read_orcid()
    xml_bytes = fetch_cvn_xml(orcid)

    xml_path = Path("cvn.xml")
    xml_path.write_bytes(xml_bytes)
    print(f"  → {xml_path}  ({len(xml_bytes):,} bytes)")

    print("Parsing CVN XML…")
    root = ET.fromstring(xml_bytes.decode("utf-8"))

    data = {
        "personal":          extract_personal(root),
        "experience":        extract_experience(root),
        "education":         extract_education(root),
        "languages":         extract_languages(root),
        "research_lines":    extract_research_lines(root),
        "projects":          extract_projects(root),
        "contracts":         extract_contracts(root),
        "research_stays":    extract_research_stays(root),
        "articles":          extract_articles(root),
        "chapters":          extract_chapters(root),
        "conferences":       extract_conferences(root),
        "reviews":           extract_reviews(root),
        "awards":            extract_awards(root),
        "grants":            extract_grants(root),
        "accreditations":    extract_accreditations(root),
        "research_training":      extract_specialized_training(root),
        "teaching":               extract_teaching(root),
        "theses":                 extract_theses(root),
        "teaching_training":      extract_teaching_training(root),
        "teaching_projects":      extract_teaching_projects(root),
        "teaching_articles":      extract_teaching_articles(root),
        "teaching_conferences":   extract_teaching_conferences(root),
        "teaching_others":        extract_teaching_others(root),
    }

    print("Normalizing title case…")
    data = normalize_titles(data)

    from translate import translate_data
    print("Translating CV data to English…")
    data = translate_data(data)

    out = Path("src/data/cv.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

    print(f"  → {out}")
    for key, val in data.items():
        if isinstance(val, list):
            print(f"     {key}: {len(val)}")


if __name__ == "__main__":
    main()
