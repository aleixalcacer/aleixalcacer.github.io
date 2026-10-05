# aleixalcacer.github.io

Personal website. Plain HTML + CSS, no framework.

Content lives in `data.yaml`. After editing it, regenerate the page:

```bash
python build.py   # needs pyyaml
```

Commit `data.yaml` and `index.html`. GitHub Pages serves the repo root.

`simplex.js` animates the rotating polyhedron in the header (no dependencies); `style.css` holds all the styling.

A pre-commit hook in `.githooks/` regenerates `index.html` automatically. Enable it once per clone:

```bash
git config core.hooksPath .githooks
```
