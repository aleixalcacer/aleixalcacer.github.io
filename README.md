# aleixalcacer.github.io

Personal academic website built with [Astro](https://astro.build). CV data is fetched automatically from the FECYT CVN portal and translated to English via the Anthropic API.

## Pipeline

```
FECYT CVN portal (PDF) → scripts/cvn.py → scripts/sync.py → src/data/cv.json → Astro
```

`scripts/sync.py` downloads the CVN PDF from FECYT, extracts the embedded XML, parses every section into structured JSON, and runs `translate.py` to translate Spanish/Catalan fields to English (cached in `translations.json`). The output is written to `src/data/cv.json`, which the Astro pages consume at build time.

Software projects displayed on the Projects page are maintained manually in `src/data/projects.json`.

## Commands

| Command              | Action                                         |
| :------------------- | :--------------------------------------------- |
| `npm install`        | Install dependencies                           |
| `npm run sync`       | Fetch CVN and regenerate `src/data/cv.json`    |
| `npm run dev`        | Start dev server at `localhost:4321`           |
| `npm run build`      | Build to `./dist/`                             |
| `npm run preview`    | Preview the production build locally           |

## Requirements

- Node ≥ 22.12
- Python ≥ 3.11 with `uv` (dependencies in `pyproject.toml`)
- `ANTHROPIC_API_KEY` env var for translating new CV entries (existing translations are cached and do not require the key)
