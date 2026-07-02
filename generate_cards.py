#!/usr/bin/env python3
"""
generate_cards.py

Generates self-hosted, static SVG "repo pin" cards (same look as
github-readme-stats' /api/pin endpoint, github_dark_dimmed theme)
so your profile README never depends on an external service again.

Usage:
    python3 generate_cards.py USERNAME repo1 repo2 repo3 ...

    # with a token to avoid the 60 req/hr anonymous rate limit
    GITHUB_TOKEN=ghp_xxx python3 generate_cards.py USERNAME repo1 repo2 ...

Output:
    ./cards/<repo>.svg   one file per repo

Then embed in your README with a plain markdown image + link, no query
params, no external host:

    [![ElkDB](./cards/ElkDB.svg)](https://github.com/USERNAME/ElkDB)
"""
import html
import json
import os
import sys
import textwrap
import urllib.request

OUT_DIR = "cards"

# github_dark_dimmed palette (same family GitHub uses for its own dark
# dimmed theme)
BG_COLOR = "#22272e"
BORDER_COLOR = "#444c56"
TITLE_COLOR = "#adbac7"
TEXT_COLOR = "#768390"
ICON_COLOR = "#768390"
STAR_COLOR = "#e3b341"

# Linguist-ish colors for common languages, extend as needed
LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572A5",
    "Go": "#00ADD8", "Rust": "#dea584", "C++": "#f34b7d", "C": "#555555",
    "C#": "#178600", "Java": "#b07219", "Ruby": "#701516", "PHP": "#4F5D95",
    "Shell": "#89e051", "HTML": "#e34c26", "CSS": "#563d7c", "Scala": "#c22d40",
    "Kotlin": "#A97BFF", "Swift": "#F05138", "Dart": "#00B4AB",
    "Elixir": "#6e4a7e", "Haskell": "#5e5086", "OCaml": "#ef7a08",
    "Erlang": "#B83998", "Lua": "#000080", "Vue": "#41b883",
}

CARD_W = 400
CARD_H = 120


def fetch_repo(user, repo, token=None):
    url = f"https://api.github.com/repos/{user}/{repo}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except Exception as e:
        print(f"  ! could not fetch {repo}: {e}", file=sys.stderr)
        return None


def wrap_desc(desc, width=58, max_lines=2):
    if not desc:
        return ["No description provided."]
    lines = textwrap.wrap(desc, width=width)[:max_lines]
    if len(lines) == max_lines and len(textwrap.wrap(desc, width=width)) > max_lines:
        lines[-1] = lines[-1].rstrip() + "…"
    return lines


def svg_for(repo_data, user, repo, show_owner=True):
    name = repo_data.get("name", repo) if repo_data else repo
    desc = repo_data.get("description") if repo_data else None
    lang = repo_data.get("language") if repo_data else None
    stars = repo_data.get("stargazers_count", 0) if repo_data else 0
    forks = repo_data.get("forks_count", 0) if repo_data else 0
    lang_color = LANG_COLORS.get(lang, "#8b949e")

    title = f"{user}/{name}" if show_owner else name
    title = html.escape(title)
    desc_lines = [html.escape(l) for l in wrap_desc(desc)]

    desc_svg = "\n".join(
        f'<text x="25" y="{55 + i * 20}" class="desc">{line}</text>'
        for i, line in enumerate(desc_lines)
    )

    lang_block = ""
    if lang:
        lang_block = f'''
    <circle cx="30" cy="{CARD_H - 20}" r="6" fill="{lang_color}"/>
    <text x="42" y="{CARD_H - 15}" class="meta">{html.escape(lang)}</text>'''

    return f'''<svg width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .card {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Ubuntu, Helvetica, Arial, sans-serif; }}
    .title {{ fill: {TITLE_COLOR}; font-size: 16px; font-weight: 600; }}
    .desc  {{ fill: {TEXT_COLOR};  font-size: 12px; }}
    .meta  {{ fill: {TEXT_COLOR};  font-size: 12px; }}
    .bg    {{ fill: {BG_COLOR}; stroke: {BORDER_COLOR}; stroke-width: 1; }}
    a text {{ text-decoration: none; }}
  </style>
  <g class="card">
    <rect class="bg" x="0.5" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="6"/>
    <!-- repo icon -->
    <path fill="{ICON_COLOR}" transform="translate(25, 22)" d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 1 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.994 1.117.75.75 0 1 1-1.492.166A2.5 2.5 0 0 1 2 11.5Zm10.5-1H4.5a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8Z" transform-origin="0 0" />
    <text x="46" y="35" class="title">{title}</text>
    {desc_svg}
    {lang_block}
    <!-- star icon -->
    <path fill="{STAR_COLOR}" transform="translate({CARD_W - 150}, {CARD_H - 26})" d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/>
    <text x="{CARD_W - 130}" y="{CARD_H - 15}" class="meta">{stars}</text>
    <!-- fork icon -->
    <path fill="{ICON_COLOR}" transform="translate({CARD_W - 90}, {CARD_H - 26})" d="M5 3.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm0 2.122a2.25 2.25 0 1 0-1.5 0v.878A2.25 2.25 0 0 0 5.75 8.5h1.5v2.128a2.251 2.251 0 1 0 1.5 0V8.5h1.5a2.25 2.25 0 0 0 2.25-2.25v-.878a2.25 2.25 0 1 0-1.5 0v.878a.75.75 0 0 1-.75.75h-4.5a.75.75 0 0 1-.75-.75Zm6.75-.878a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5ZM8.75 12.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z"/>
    <text x="{CARD_W - 70}" y="{CARD_H - 15}" class="meta">{forks}</text>
  </g>
</svg>'''


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_cards.py USERNAME repo1 repo2 ...")
        sys.exit(1)

    user = sys.argv[1]
    repos = sys.argv[2:]
    token = os.environ.get("GITHUB_TOKEN")

    os.makedirs(OUT_DIR, exist_ok=True)
    for repo in repos:
        print(f"fetching {user}/{repo} ...")
        data = fetch_repo(user, repo, token)
        svg = svg_for(data, user, repo)
        path = os.path.join(OUT_DIR, f"{repo}.svg")
        with open(path, "w") as f:
            f.write(svg)
        print(f"  -> {path}")

    print("\nDone. Embed with, e.g.:")
    for repo in repos:
        print(f'[![{repo}](./{OUT_DIR}/{repo}.svg)](https://github.com/{user}/{repo})')


if __name__ == "__main__":
    main()
