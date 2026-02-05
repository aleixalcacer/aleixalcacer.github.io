#!/usr/bin/env python3
"""Pre-render script to generate listing YAML files from unified cv.yml"""
import yaml
from pathlib import Path


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
    """Generate Quarto markdown for interests section."""
    lines = []
    for interest in interests_data:
        lines.append(f"- {interest}")
    return "\n".join(lines)


def main():
    # Read the unified CV data
    cv_path = Path(__file__).parent.parent / "_data" / "cv.yml"
    with open(cv_path, encoding="utf-8") as f:
        cv = yaml.safe_load(f)

    # Define mappings from cv.yml sections to output files
    mappings = {
        "research/journal-publications.yml": cv["publications"]["articles"],
        "research/book-chapters.yml": cv["publications"]["incollection"],
        "research/conference-proceedings.yml": cv["publications"]["inproceedings"],
        "research/conference-contributions.yml": cv["publications"]["presentations"],
        "research/other-contributions.yml": cv["publications"]["other"],
        "research/research-stays.yml": cv["research_stays"],
        "teaching/experience.yml": cv["teaching"]["experience"],
        "teaching/journal-publications.yml": cv["teaching"]["publications"],
        "teaching/conference-contributions.yml": cv["teaching"]["conferences"],
        "os-projects/projects.yml": cv["projects"],
    }

    # Generate each output file
    root = Path(__file__).parent.parent
    for path, data in mappings.items():
        output_path = root / path
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# AUTO-GENERATED from _data/cv.yml - DO NOT EDIT\n")
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"Generated: {path}")

    # Generate Quarto include files for education and interests
    includes_dir = root / "_includes"
    includes_dir.mkdir(exist_ok=True)

    education_qmd = includes_dir / "education.qmd"
    with open(education_qmd, "w", encoding="utf-8") as f:
        f.write("<!-- AUTO-GENERATED from _data/cv.yml - DO NOT EDIT -->\n")
        f.write(generate_education_qmd(cv["education"]))
    print(f"Generated: _includes/education.qmd")

    interests_qmd = includes_dir / "interests.qmd"
    with open(interests_qmd, "w", encoding="utf-8") as f:
        f.write("<!-- AUTO-GENERATED from _data/cv.yml - DO NOT EDIT -->\n")
        f.write(generate_interests_qmd(cv["interests"]))
    print(f"Generated: _includes/interests.qmd")


if __name__ == "__main__":
    main()
