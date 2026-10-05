"""Generate index.html from data.yaml.  Usage: python build.py"""
import json
from html import escape as e
from pathlib import Path

import yaml

d = yaml.safe_load(Path("data.yaml").read_text())


person = json.dumps(
    {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": d["name"],
        "jobTitle": d["role"].split(" · ")[0],
        "affiliation": {"@type": "CollegeOrUniversity", "name": "Universitat Jaume I", "url": "https://www.uji.es"},
        "url": d["site"] + "/",
        "image": d["site"] + "/profile.jpg",
        "description": d["description"],
        "sameAs": [l["url"] for l in d["links"] if not l["url"].startswith("mailto:")] + [d["papers_all"]["url"]],
    },
    ensure_ascii=False,
    indent=2,
)


def link(text, url):
    return f'<a href="{e(url)}">{e(text)}</a>' if url else e(text)


def section(title, items):
    lis = "\n".join(f"      <li>{i}</li>" for i in items)
    return f"\n    <h2>{title}</h2>\n    <ul>\n{lis}\n    </ul>\n"


links = "\n      ".join(link(l["label"], l["url"]) for l in d["links"])
software = [
    f'{link(s["name"], s["url"])} ({e(s["when"])}) — {e(s["role"])}. {e(s["text"])}'
    for s in d["software"]
]
papers = [
    f'{link(p["title"], p.get("url"))}. '
    + (f'With {e(p["with"])}. ' if "with" in p else "")
    + f'<em>{e(p["venue"])}</em>, {p["year"]}.'
    for p in d["papers"]
]
papers.append(link(d["papers_all"]["label"] + " →", d["papers_all"]["url"]))
background = [e(t["text"]) for t in d["background"]]
collab = [
    e(t["text"]) + (f' Paper: {link(t["paper"]["label"], t["paper"]["url"])}.' if "paper" in t else "")
    for t in d["collaborations"]
]

page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(d["title"])}</title>
  <meta name="description" content="{e(d["description"])}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{e(d["title"])}">
  <meta property="og:description" content="{e(d["description"])}">
  <meta property="og:url" content="{e(d["site"])}/">
  <meta property="og:image" content="{e(d["site"])}/profile.jpg">
  <meta name="twitter:card" content="summary">
  <link rel="canonical" href="{e(d["site"])}/">
  <script type="application/ld+json">
{person}
  </script>
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main>
    <header>
      <img src="profile.jpg" alt="{e(d["name"])}" width="96" height="96">
      <div>
        <h1>{e(d["name"])}</h1>
        <p>{e(d["role"])}</p>
      </div>
      <svg class="simplex" viewBox="0 0 120 110" aria-hidden="true">
        <path class="hull" d="M60 8 L8 100 L112 100 Z"/>
        <path class="mix" d="M60 62 L60 8 M60 62 L8 100 M60 62 L112 100"/>
        <circle class="p" cx="60" cy="62" r="3.5"/>
        <circle class="p" cx="42" cy="80" r="2.5"/>
        <circle class="p" cx="82" cy="82" r="2.5"/>
        <circle class="p" cx="60" cy="36" r="2.5"/>
        <circle class="p" cx="38" cy="92" r="2.5"/>
        <circle class="p" cx="90" cy="92" r="2.5"/>
        <circle class="v" cx="60" cy="8" r="5"/>
        <circle class="v" cx="8" cy="100" r="5"/>
        <circle class="v" cx="112" cy="100" r="5"/>
      </svg>
    </header>

    <p>{e(d["bio"])}</p>

    <p class="links">
      {links}
    </p>
{section("Selected papers", papers)}{section("Collaborations", collab)}{section("Software", software)}{section("Background", background)}  </main>
  <script src="simplex.js" defer></script>
</body>
</html>
"""

Path("index.html").write_text(page)
