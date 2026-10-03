"""
translate.py — LLM-based translation layer for sync.py.

Translates Spanish/Catalan CV fields to English using the Anthropic API.
Maintains a persistent cache in translations.json so:
  • subsequent runs cost no API calls for already-translated strings;
  • the user can hand-edit any entry in translations.json to fix or override.

Called from sync.py:
    from translate import translate_data
    data = translate_data(data)
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Whitelist: section → fields that hold natural-language Spanish/Catalan text.
# Every other field (DOIs, years, author names, journal/conf titles, ORCID…)
# is left untouched.
# ---------------------------------------------------------------------------

TRANSLATABLE: dict[str, list[str]] = {
    "experience":           ["role", "institution"],
    "education":            ["degree", "institution", "thesis"],
    "languages":            ["name"],
    "research_lines":       ["title", "description"],
    "projects":             ["title", "institution"],
    "contracts":            ["title", "description", "institution"],
    "research_stays":       ["institution", "description"],
    "research_training":    ["title", "institution"],
    "awards":               ["title", "description", "institution"],
    "accreditations":       ["title", "institution"],
    "reviews":              ["role", "institution"],
    "teaching":             ["course", "degree"],
    "theses":               ["title", "institution"],
    "teaching_projects":    ["title", "institution"],
    "teaching_training":    ["title", "institution"],
    "teaching_articles":    ["title"],
    "teaching_conferences": ["title"],
    "teaching_others":      ["title"],
}

CACHE_PATH = Path("translations.json")
_ENV_PATH = Path(".env")


def _load_dotenv() -> None:
    """Load KEY=value pairs from .env into os.environ (existing vars take priority)."""
    if not _ENV_PATH.exists():
        return
    for line in _ENV_PATH.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val

# Batch size: number of strings per LLM call (well within token limits).
_CHUNK = 150

_SYSTEM_PROMPT = """\
You are an expert academic CV translator specialised in Spanish and Catalan.

Your task: translate the given strings into natural, professional English.

Rules — follow them strictly:
1. If a string is already English, return it UNCHANGED.
2. Keep proper nouns unchanged: personal names, official institution names,
   journal names, conference names, city names, country names, and acronyms.
3. Translate descriptive/functional text naturally: job titles, degree names,
   course names, project descriptions, award descriptions, language names, etc.
4. Preserve the original capitalisation pattern of the translation (e.g. if the
   source uses title-case, use title-case in English too).
5. Do NOT add explanations, notes, or extra keys.
6. Return a JSON object with a single key "translations" whose value is an object
   mapping EVERY input string to its English form (or itself if already English).
"""


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache() -> dict[str, str]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text("utf-8"))
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True),
        "utf-8",
    )


# ---------------------------------------------------------------------------
# String collection
# ---------------------------------------------------------------------------

def _collect_strings(data: dict) -> set[str]:
    """Walk *data* according to TRANSLATABLE and return all non-empty values."""
    strings: set[str] = set()
    for section, fields in TRANSLATABLE.items():
        for item in data.get(section, []):
            if not isinstance(item, dict):
                continue
            for field in fields:
                val = item.get(field, "")
                if val and isinstance(val, str):
                    strings.add(val)
    return strings


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def _call_llm(strings: list[str]) -> dict[str, str]:
    """
    Send *strings* to Claude and return {source: english_translation}.
    Raises on import/API errors so the caller can decide how to handle.
    """
    import anthropic

    client = anthropic.Anthropic(max_retries=5)

    payload = json.dumps(strings, ensure_ascii=False, indent=2)

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Translate each of the following {len(strings)} strings to English.\n\n"
                    f"{payload}"
                ),
            }
        ],
    )

    raw = response.content[0].text
    result = json.loads(raw)
    return result.get("translations", {})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate_data(data: dict) -> dict:
    """
    Return a copy of *data* with all natural-language fields translated to English.

    - Translations are persisted in ``translations.json`` (keyed by source string).
    - Only strings absent from the cache trigger an LLM call.
    - If ``ANTHROPIC_API_KEY`` is unset, cached translations are still applied;
      new strings are left in their original language (with a printed warning).
    """
    _load_dotenv()
    cache = _load_cache()

    all_strings = _collect_strings(data)
    uncached = sorted(s for s in all_strings if s not in cache)

    if uncached:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print(
                f"  ⚠  ANTHROPIC_API_KEY not set — "
                f"{len(uncached)} new string(s) will not be translated.\n"
                "     Set the key and re-run sync.py to fill in the translations."
            )
        else:
            print(f"  → Translating {len(uncached)} new string(s) via Claude…")
            for i in range(0, len(uncached), _CHUNK):
                batch = uncached[i : i + _CHUNK]
                translations = _call_llm(batch)
                cache.update(translations)
            _save_cache(cache)
            print(f"  → Translation cache updated → {CACHE_PATH}")

    # Apply cache to a deep-ish copy of data (lists of dicts → new list of copied dicts)
    result: dict = {}
    for section, items in data.items():
        fields = TRANSLATABLE.get(section)
        if fields is None or not isinstance(items, list):
            result[section] = items
            continue
        translated: list[dict] = []
        for item in items:
            item = dict(item)  # shallow copy of the dict
            for field in fields:
                val = item.get(field, "")
                if val and isinstance(val, str):
                    item[field] = cache.get(val, val)  # fallback to original
            translated.append(item)
        result[section] = translated

    return result
