#!/usr/bin/env python3

"""
Merge projects.json (user-curated) with live GitHub data.

User controls:
    name, repo, logo, description, tags, order

Auto-fetched:
    stars, languages, pushed_at

Jupyter Notebook is excluded from the language donut because
it represents notebook file size rather than the programming
languages you want highlighted on the profile.
"""

import json
import os
import sys
import urllib.request


TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Languages that should not appear in the project language donut.
HIDDEN_LANGUAGES = {
    "Jupyter Notebook",
}


def gh(url):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}" if TOKEN else "",
            "User-Agent": "projects-panel",
        },
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def filter_languages(languages):
    """
    Remove unwanted languages such as Jupyter Notebook.
    """
    return {
        language: bytes_count
        for language, bytes_count in languages.items()
        if language not in HIDDEN_LANGUAGES
    }


def main():

    with open("projects.json", encoding="utf-8") as file:
        projects = json.load(file)

    for project in projects:

        repo = project.get("repo", "").strip()

        repo = (
            repo
            .replace("https://github.com/", "")
            .replace("http://github.com/", "")
            .rstrip("/")
        )

        project["repo"] = repo

        try:

            # Fetch repository information
            info = gh(
                f"https://api.github.com/repos/{repo}"
            )

            project["stars"] = info.get(
                "stargazers_count",
                0,
            )

            project["pushed_at"] = info.get(
                "pushed_at"
            )

            # Use GitHub description only if projects.json
            # does not already contain one.
            if not project.get("description"):
                project["description"] = (
                    info.get("description") or ""
                )

            # Fetch repository language statistics
            languages = gh(
                f"https://api.github.com/repos/{repo}/languages"
            )

            # Remove Jupyter Notebook
            project["languages"] = filter_languages(
                languages
            )

        except Exception as error:

            print(
                f"warn: could not fetch {repo}: {error}",
                file=sys.stderr,
            )

            project.setdefault(
                "stars",
                0,
            )

            project.setdefault(
                "languages",
                {},
            )

            project.setdefault(
                "pushed_at",
                None,
            )

    # Generate merged.json
    with open(
        "merged.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            projects,
            file,
            indent=2,
        )

    print(
        f"merged {len(projects)} projects"
    )


if __name__ == "__main__":
    main()