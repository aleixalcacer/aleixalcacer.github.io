#!/usr/bin/env python3
"""Pre-render script to generate include files from unified cv.yml"""
import yaml
from datetime import datetime
from pathlib import Path


def format_date(date_str: str) -> str:
    """Convert date string to readable format (e.g., '2023-08-06' -> 'August 6, 2023')."""
    if not date_str:
        return ""
    try:
        # Handle both YYYY-MM-DD and YYYY/MM/DD formats
        date_str = date_str.replace("/", "-")
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%B %d, %Y").replace(" 0", " ")  # Remove leading zero from day
    except (ValueError, AttributeError):
        return str(date_str)


def format_doi(doi: str) -> str:
    """Format DOI as a clean hyperlink."""
    return f'<a href="https://doi.org/{doi}">{doi}</a>'


def render_labels(item: dict) -> str:
    """Generate HTML for code/pdf/labels links."""
    labels = []
    if item.get("code"):
        labels.append(f'<span class="quarto-label"><a href="{item["code"]}">CODE</a></span>')
    if item.get("pdf"):
        labels.append(f'<span class="quarto-label"><a href="{item["pdf"]}">PDF</a></span>')
    for label in item.get("labels", []):
        if label.get("url"):
            labels.append(f'<span class="quarto-label"><a href="{label["url"]}">{label["name"].upper()}</a></span>')
    if labels:
        return f'<div class="quarto-labels">{" ".join(labels)}</div>'
    return ""


def render_journal_articles(articles: list) -> str:
    """Generate HTML for journal articles (APA-like format).

    Format: Author (Year). Title. *Journal, Volume*(Issue). DOI
    """
    lines = ['```{=html}', '<ul id="quarto-journal">']
    for item in articles:
        lines.append('    <li class="quarto-publication">')

        # Author (Year). Title.
        citation = f'{item["author"]} ({item["year"]}). {item["title"]}. '

        # *Journal, Volume*(Issue).
        citation += f'<i>{item["journal"]}'
        if item.get("volume"):
            citation += f', {item["volume"]}'
        citation += '</i>'
        if item.get("number"):
            citation += f'({item["number"]})'
        citation += '. '

        # DOI
        citation += format_doi(item["doi"])

        lines.append(f'        {citation}')

        # JIF info
        if item.get("jif"):
            lines.append(f'        <br><small class="text-muted">{item["jif_year"]} JIF: {item["jif"]} ({item["jif_quartile"]} in {item["jif_category"]})</small>')

        # Labels
        labels = render_labels(item)
        if labels:
            lines.append(f'        {labels}')

        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_book_chapters(chapters: list) -> str:
    """Generate HTML for book chapters (APA-like format).

    Format: Author (Year). Chapter title. In *Book title* (Series). Publisher. DOI
    """
    lines = ['```{=html}', '<ul id="quarto-book-chapter">']
    for item in chapters:
        lines.append('    <li class="quarto-publication">')

        # Author (Year). Chapter title. In *Book title*
        citation = f'{item["author"]} ({item["year"]}). {item["title"]}. '
        citation += f'In <i>{item["booktitle"]}</i>'

        # (Series)
        if item.get("series"):
            citation += f' ({item["series"]})'

        # Publisher. DOI
        citation += f'. {item["publisher"]}. '
        citation += format_doi(item["doi"])

        lines.append(f'        {citation}')

        # Labels
        labels = render_labels(item)
        if labels:
            lines.append(f'        {labels}')

        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_conference_proceedings(proceedings: list) -> str:
    """Generate HTML for conference proceedings (APA-like format).

    Format: Author (Year). Paper title. In *Proceedings* (Series). Publisher. DOI
    """
    lines = ['```{=html}', '<ul id="quarto-proceeding">']
    for item in proceedings:
        lines.append('    <li class="quarto-publication">')

        # Author (Year). Paper title. In *Proceedings*
        citation = f'{item["author"]} ({item["year"]}). {item["title"]}. '
        citation += f'In <i>{item["booktitle"]}</i>'

        # (Series)
        if item.get("series"):
            citation += f' ({item["series"]})'

        # Publisher. DOI
        citation += f'. {item["publisher"]}. '
        citation += format_doi(item["doi"])

        lines.append(f'        {citation}')

        # Labels
        labels = render_labels(item)
        if labels:
            lines.append(f'        {labels}')

        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_conference_presentations(presentations: list) -> str:
    """Generate HTML for conference presentations (APA-like format).

    Format: Author (Date). *Title* [Conference presentation]. Conference, Location.
    """
    lines = ['```{=html}', '<ul id="quarto-conference">']
    for item in presentations:
        lines.append('    <li class="quarto-publication">')

        # Author (Date).
        date_formatted = format_date(item.get("date"))
        citation = f'{item["author"]} ({date_formatted}). '

        # *Title* [Conference presentation].
        citation += f'<i>{item["title"]}</i> [Conference presentation]. '

        # Conference, Location.
        citation += f'{item["conference"]}, {item["location"]}.'

        lines.append(f'        {citation}')

        # Note
        if item.get("note"):
            lines.append(f'        <br><small class="text-muted"><i>{item["note"]}</i></small>')

        # Labels
        labels = render_labels(item)
        if labels:
            lines.append(f'        {labels}')

        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_research_stays(stays: list) -> str:
    """Generate HTML for research stays."""
    lines = ['```{=html}', '<ul id="quarto-stays">']
    for item in stays:
        lines.append('    <li class="quarto-publication">')
        lines.append(f'        <strong>{item["institution"]}</strong>, {item["location"]} ({item["dates"]})')
        lines.append(f'        <br>Host: {item["host"]}')
        lines.append(f'        <br><i>{item["description"]}</i>')
        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_teaching_experience(experience: list) -> str:
    """Generate HTML for teaching experience table."""
    lines = ['```{=html}', '<div class="table-responsive">']
    lines.append('    <table class="table table-hover">')
    lines.append('        <thead style="white-space: nowrap">')
    lines.append('        <tr>')
    lines.append('            <th scope="col">Course</th>')
    lines.append('            <th scope="col">Degree</th>')
    lines.append('            <th scope="col">Entity</th>')
    lines.append('            <th scope="col">ECTS</th>')
    lines.append('            <th scope="col">Year</th>')
    lines.append('        </tr>')
    lines.append('        </thead>')
    lines.append('        <tbody>')
    for item in experience:
        lines.append('            <tr>')
        lines.append(f'                <td>{item["course"]}</td>')
        lines.append(f'                <td>{item["degree"]}</td>')
        lines.append(f'                <td>{item["entity"]}</td>')
        lines.append(f'                <td>{item["credits"]}</td>')
        lines.append(f'                <td>{item["year"] - 1}/{item["year"]}</td>')
        lines.append('            </tr>')
    lines.append('        </tbody>')
    lines.append('    </table>')
    lines.append('</div>')
    lines.append('```')
    return '\n'.join(lines)


def render_teaching_conferences(conferences: list) -> str:
    """Generate HTML for teaching conferences (APA-like format).

    Format: Author (Date). *Title* [Conference paper]. Conference, Location. DOI
    """
    lines = ['```{=html}', '<ul id="quarto-conference">']
    for item in conferences:
        lines.append('    <li class="quarto-publication">')

        # Author (Date).
        date_formatted = format_date(item.get("date"))
        citation = f'{item["author"]} ({date_formatted}). '

        # *Title* [Conference paper].
        citation += f'<i>{item["title"]}</i> [Conference paper]. '

        # Conference, Location.
        citation += f'{item["conference"]}, {item["location"]}.'

        # DOI
        if item.get("doi"):
            citation += f' {format_doi(item["doi"])}'

        lines.append(f'        {citation}')

        # Labels
        labels = render_labels(item)
        if labels:
            lines.append(f'        {labels}')

        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_projects(projects: list) -> str:
    """Generate HTML for open source projects."""
    lines = ['```{=html}']
    for category in projects:
        lines.append(f'<div class="projects-section">')
        lines.append(f'<h2>{category["category"]}</h2>')
        lines.append('<div class="projects-grid">')
        for tile in category["items"]:
            lines.append('  <div class="card project-card">')
            lines.append('    <div class="card-header">')
            lines.append(f'      <a href="{tile["href"]}" class="listing-title">{tile["title"]}</a>')
            if tile.get("code"):
                lines.append(f'      <a href="{tile["code"]}" title="View source code">')
                lines.append('        <i class="bi-github"></i>')
                lines.append('      </a>')
            lines.append('    </div>')
            lines.append('    <div class="card-body">')
            lines.append(f'      <span class="card-text">{tile["description"]}</span>')
            lines.append('    </div>')
            lines.append('    <div class="card-footer">')
            lines.append(f'      <span class="role-text">{tile["role"]}</span>')
            lines.append(f'      <span class="date-text">{tile["date"]}</span>')
            lines.append('    </div>')
            lines.append('  </div>')
        lines.append('</div>')
        lines.append('</div>')
    lines.append('```')
    return '\n'.join(lines)


def render_awards(awards: list) -> str:
    """Generate HTML for awards and honors."""
    lines = ['```{=html}', '<ul id="quarto-awards">']
    for item in awards:
        lines.append('    <li class="quarto-publication">')
        lines.append(f'        <strong>{item["title"]}</strong> ({item["year"]})')
        lines.append(f'        <br>{item["institution"]}')
        if item.get("description"):
            lines.append(f'        <br><i>{item["description"]}</i>')
        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_grants(grants: list) -> str:
    """Generate HTML for grants and fellowships."""
    lines = ['```{=html}', '<ul id="quarto-grants">']
    for item in grants:
        lines.append('    <li class="quarto-publication">')
        lines.append(f'        <strong>{item["name"]}</strong>')
        lines.append(f'        <br>{item["entity"]}')
        if item.get("type"):
            lines.append(f'        <br><i>{item["type"]}</i>')
        date_str = format_date(item.get("date"))
        if date_str:
            duration = f' ({item["duration"]})' if item.get("duration") else ''
            lines.append(f'        <br><small class="text-muted">{date_str}{duration}</small>')
        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_languages(languages: list) -> str:
    """Generate HTML for languages."""
    lines = ['```{=html}', '<ul id="quarto-languages">']
    for item in languages:
        lines.append('    <li>')
        lines.append(f'        <strong>{item["language"]}</strong>: {item["level"]}')
        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_service(service: list) -> str:
    """Generate HTML for professional service."""
    lines = ['```{=html}', '<ul id="quarto-service">']
    for item in service:
        lines.append('    <li>')
        lines.append(f'        {item["description"]}')
        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_research_projects(projects: list) -> str:
    """Generate HTML for research projects."""
    lines = ['```{=html}', '<ul id="quarto-research-projects">']
    for item in projects:
        lines.append('    <li class="quarto-publication">')
        lines.append(f'        <strong>{item["title"]}</strong>')
        if item.get("code"):
            lines.append(f'        <br>Code: {item["code"]}')
        if item.get("program"):
            lines.append(f'        <br>Program: {item["program"]}')
        lines.append(f'        <br>Funder: {item["funder"]}')
        lines.append(f'        <br>PI: {item["pi"]}')
        lines.append(f'        <br>Period: {item["dates"]}')
        if item.get("amount"):
            lines.append(f'        <br>Funding: {item["amount"]}')
        if item.get("role"):
            lines.append(f'        <br><small class="text-muted">Role: {item["role"]}</small>')
        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def render_teaching_projects(projects: list) -> str:
    """Generate HTML for teaching innovation projects."""
    lines = ['```{=html}', '<ul id="quarto-teaching-projects">']
    for item in projects:
        lines.append('    <li class="quarto-publication">')
        lines.append(f'        <strong>{item["title"]}</strong>')
        if item.get("code"):
            lines.append(f'        <br>Code: {item["code"]}')
        lines.append(f'        <br>Funder: {item["funder"]}')
        lines.append(f'        <br>Role: {item["role"]}')
        lines.append(f'        <br>Period: {item["dates"]}')
        if item.get("description"):
            lines.append(f'        <br><i>{item["description"]}</i>')
        lines.append('    </li>')
    lines.append('</ul>')
    lines.append('```')
    return '\n'.join(lines)


def format_work_date(date_str: str) -> str:
    """Convert date string to Month Year format (e.g., '2024-09-28' -> 'Sep 2024')."""
    if not date_str:
        return "present"
    try:
        date_str = date_str.replace("/", "-")
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%b %Y")
    except (ValueError, AttributeError):
        return str(date_str)


def generate_work_experience_qmd(work_data: list) -> str:
    """Generate Quarto markdown for work experience section."""
    lines = []
    for item in work_data:
        start = format_work_date(item.get("start_date"))
        end = format_work_date(item.get("end_date"))

        # Position and dates
        lines.append(f"- **{item['position']}** | {start} - {end}  ")

        # Institution and location
        inst_line = f"  {item['institution']}"
        if item.get("department"):
            inst_line += f", {item['department']}"
        inst_line += f", {item['location']}"
        lines.append(inst_line)

        # Description
        if item.get("description"):
            lines.append(f"  *{item['description']}*")

        lines.append("")

    return "\n".join(lines)


def generate_education_qmd(education_data: list) -> str:
    """Generate Quarto markdown for education section."""
    lines = []
    for item in education_data:
        end_year = item.get("end_year") or "present"
        lines.append(f"- **{item['degree']}** | {item['start_year']} - {end_year}  ")
        lines.append(f"  {item['institution']}, {item['location']}")
        lines.append("")
    return "\n".join(lines)


def generate_interests_qmd(interests_data: list) -> str:
    """Generate Quarto markdown for interests section with tag/chip style."""
    # Map interests to icons
    icon_map = {
        "Archetypal Analysis": "bi-graph-up",
        "Machine Learning": "bi-robot",
        "Data Visualisation": "bi-bar-chart",
        "Reinforcement Learning": "bi-cpu",
        "HPC and Software Optimization": "bi-speedometer2",
        "Knowledge Sharing": "bi-share",
    }
    lines = ['```{=html}', '<div class="interests-container">']
    for interest in interests_data:
        icon = icon_map.get(interest, "bi-star")
        lines.append(f'  <span class="interest-tag"><i class="bi {icon}"></i>{interest}</span>')
    lines.append('</div>')
    lines.append('```')
    return "\n".join(lines)


def generate_about_qmd(personal: dict, cv_url: str) -> str:
    """Generate Quarto markdown for about/bio section."""
    lines = []
    # Add bio paragraphs
    bio = personal.get("bio", "").strip()
    for paragraph in bio.split("\n\n"):
        lines.append(paragraph.strip())
        lines.append("")
    # Add CV link
    lines.append(f"[View my complete CV]({cv_url}).")
    return "\n".join(lines)


def generate_social_links_qmd(social: list) -> str:
    """Generate Quarto markdown for social links (used in YAML frontmatter)."""
    lines = []
    for item in social:
        icon = item["icon"].replace("fa ", "fa-").replace(" ", " fa-")
        lines.append(f'    - text: "{{{{< {icon} >}}}} {item["label"]}"')
        lines.append(f'      href: "{item["url"]}"')
    return "\n".join(lines)


def main():
    # Read the unified CV data
    cv_path = Path(__file__).parent.parent / "_data" / "cv.yml"
    with open(cv_path, encoding="utf-8") as f:
        cv = yaml.safe_load(f)

    root = Path(__file__).parent.parent
    includes_dir = root / "_includes"
    includes_dir.mkdir(exist_ok=True)

    # Define include file mappings
    include_mappings = {
        "journal-publications.qmd": render_journal_articles(cv["publications"]["articles"]),
        "book-chapters.qmd": render_book_chapters(cv["publications"]["incollection"]),
        "conference-proceedings.qmd": render_conference_proceedings(cv["publications"]["inproceedings"]),
        "conference-contributions.qmd": render_conference_presentations(cv["publications"]["presentations"]),
        "other-contributions.qmd": render_conference_presentations(cv["publications"]["other"]),
        "research-stays.qmd": render_research_stays(cv["research_stays"]),
        "teaching-experience.qmd": render_teaching_experience(cv["teaching"]["experience"]),
        "teaching-publications.qmd": render_journal_articles(cv["teaching"]["publications"]),
        "teaching-conferences.qmd": render_teaching_conferences(cv["teaching"]["conferences"]),
        "projects.qmd": render_projects(cv["projects"]),
        "work-experience.qmd": generate_work_experience_qmd(cv["work_experience"]),
        "education.qmd": generate_education_qmd(cv["education"]),
        "interests.qmd": generate_interests_qmd(cv["interests"]),
        "about.qmd": generate_about_qmd(cv["personal"], cv["personal"]["cv_url"]),
        "awards.qmd": render_awards(cv["awards"]),
        "grants.qmd": render_grants(cv["grants"]),
        "languages.qmd": render_languages(cv["languages"]),
        "research-service.qmd": render_service(cv["research_service"]),
        "teaching-service.qmd": render_service(cv["teaching_service"]),
        "research-projects.qmd": render_research_projects(cv["research_projects"]),
        "teaching-projects.qmd": render_teaching_projects(cv["teaching_projects"]),
    }

    # Generate each include file
    for filename, content in include_mappings.items():
        output_path = includes_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("<!-- AUTO-GENERATED from _data/cv.yml - DO NOT EDIT -->\n")
            f.write(content)
        print(f"Generated: _includes/{filename}")


if __name__ == "__main__":
    main()
