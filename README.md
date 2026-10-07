# aleixalcacer.github.io

Personal website, built with [Quarto](https://quarto.org). No theme or framework: `style.css` holds all the styling and `simplex.js` animates the polyhedron in the header.

The home page is `index.qmd`; a Python cell in it renders the content from `data.yaml`. After editing, preview or rebuild into `docs/`:

```bash
uv sync                 # once: creates .venv from pyproject.toml
uv run quarto preview   # live preview
uv run quarto render    # build into docs/
```

GitHub Actions builds and publishes the site on every push to `main` (`.github/workflows/publish.yml`), so `docs/` is not committed. In Settings → Pages, set Source to **GitHub Actions**. Commit `_freeze/`: it holds the executed output of the notes, so the build does not need to re-run them.
