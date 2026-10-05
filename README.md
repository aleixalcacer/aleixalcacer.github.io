# aleixalcacer.github.io

Personal website, built with [Quarto](https://quarto.org). No theme or framework: `style.css` holds all the styling and `simplex.js` animates the polyhedron in the header.

The home page is `index.qmd`; a Python cell in it renders the content from `data.yaml`. After editing, preview or rebuild into `docs/`:

```bash
uv sync                 # once: creates .venv from pyproject.toml
uv run quarto preview   # live preview
uv run quarto render    # build into docs/
```

GitHub Pages serves the `docs/` folder (Settings → Pages → Deploy from a branch → `/docs`). Commit `docs/` and `_freeze/` too.

A pre-commit hook in `.githooks/` re-renders automatically. Enable it once per clone:

```bash
git config core.hooksPath .githooks
```
