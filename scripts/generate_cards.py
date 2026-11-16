#!/usr/bin/env python3
"""Generate custom GitHub profile cards (SVG) straight from the GitHub API.

No third-party image servers are used, so the cards can't go down or get
rate-limited. Run it locally or let the GitHub Action do it on a schedule.

    python scripts/generate_cards.py

Optional: set GITHUB_TOKEN to raise the API rate limit (the Action does this).
"""
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

# ----------------------------------------------------------------- settings
USERNAME = "SamiKhan43"
DISPLAY_NAME = "Samiullah"
FEATURED_REPOS = [
    "roadmap-hub",
    "URL-Shortening-Service",
    "Image-Processing-Application-",
    "Saved-Reels-Visualizer",
]
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"

# ------------------------------------------------------------------- theme
BG = "#0f172a"
BORDER = "#26304a"
TITLE = "#9be9ff"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#6c63ff"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "C++": "#f34b7d", "C": "#8a8a8a", "HTML": "#e34c26", "CSS": "#9b59d0",
    "Java": "#b07219", "Go": "#00ADD8", "Rust": "#dea584", "Shell": "#89e051",
    "Jupyter Notebook": "#DA5B0B", "Dockerfile": "#384d54", "PLpgSQL": "#336790",
    "SQL": "#e38c00", "Jinja": "#a52a22", "Mako": "#7e858d",
}
FALLBACK_COLORS = ["#6c63ff", "#9be9ff", "#f59e0b", "#10b981", "#ef4444", "#ec4899"]

STAR_PATH = ("M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 "
             "1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 "
             "1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28"
             "l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z")
FORK_PATH = ("M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 "
             "2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 "
             "0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 "
             "1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 "
             "1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z")
REPO_PATH = ("M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75"
             ".75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072"
             " 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 "
             "0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a"
             ".25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4"
             "-.2Z")


# ---------------------------------------------------------------- GitHub API
def api(path, params=None):
    url = "https://api.github.com" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-cards"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def optional(fn, default=None):
    """Run fn(); on any failure print a warning and return default."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        print(f"  warning: {exc}", file=sys.stderr)
        return default


# --------------------------------------------------------------- SVG helpers
def svg_open(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img">\n'
            f'<rect x="0.5" y="0.5" rx="10" width="{w - 1}" height="{h - 1}" '
            f'fill="{BG}" stroke="{BORDER}"/>\n'
            f'<rect x="0" y="0" width="4" height="{h}" rx="2" fill="{ACCENT}"/>\n')


def text(x, y, s, size=14, fill=TEXT, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(str(s))}</text>\n')


def fmt(n):
    if n is None:
        return "-"
    return f"{n/1000:.1f}k" if n >= 10000 else f"{n:,}"


# --------------------------------------------------------------- stats card
def build_stats_card(stats):
    w, h = 495, 230
    svg = svg_open(w, h)
    svg += f'<title>{escape(DISPLAY_NAME)} GitHub stats</title>\n'
    svg += text(28, 38, f"{DISPLAY_NAME}'s GitHub Stats", 19, TITLE, 700)
    rows = [
        ("Public repositories", stats["repos"]),
        ("Total stars earned", stats["stars"]),
        ("Total commits", stats["commits"]),
        ("Pull requests", stats["prs"]),
        ("Issues opened", stats["issues"]),
        ("Followers", stats["followers"]),
    ]
    for i, (label, value) in enumerate(rows):
        col, row = divmod(i, 3)
        x = 28 + col * 232
        y = 80 + row * 40
        svg += f'<circle cx="{x + 4}" cy="{y - 5}" r="4" fill="{ACCENT}"/>\n'
        svg += text(x + 18, y, label, 13, MUTED)
        svg += text(x + 18, y + 20, fmt(value), 17, TEXT, 700)
    svg += text(28, h - 18, f"github.com/{USERNAME}", 11, MUTED)
    return svg + "</svg>\n"


# ----------------------------------------------------------- languages card
def build_languages_card(langs):
    w, h = 495, 230
    svg = svg_open(w, h)
    svg += f'<title>Most used languages</title>\n'
    svg += text(28, 38, "Most Used Languages", 19, TITLE, 700)

    total = sum(langs.values())
    if not total:
        svg += text(28, 100, "No language data yet.", 14, MUTED)
        return svg + "</svg>\n"

    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:6]
    shown_total = sum(v for _, v in top)
    bar_x, bar_w, bar_y = 28, 440, 56
    svg += (f'<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" '
            f'height="10" rx="5"/></clipPath>\n<g clip-path="url(#bar)">\n')
    x = float(bar_x)
    for i, (name, value) in enumerate(top):
        seg = bar_w * value / shown_total
        color = LANG_COLORS.get(name, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        svg += f'<rect x="{x:.2f}" y="{bar_y}" width="{seg:.2f}" height="10" fill="{color}"/>\n'
        x += seg
    svg += "</g>\n"

    for i, (name, value) in enumerate(top):
        col, row = divmod(i, 3)
        lx = 28 + col * 232
        ly = 105 + row * 32
        color = LANG_COLORS.get(name, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        svg += f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>\n'
        svg += text(lx + 18, ly, name, 14, TEXT, 600)
        svg += text(lx + 205, ly, f"{value / total * 100:.1f}%", 13, MUTED, 400, "end")
    svg += text(28, h - 18, "Based on public, non-fork repositories", 11, MUTED)
    return svg + "</svg>\n"


# ------------------------------------------------------------- project card
def build_project_card(repo):
    w, h = 400, 150
    svg = svg_open(w, h)
    svg += f'<title>{escape(repo["name"])}</title>\n'
    svg += (f'<svg x="26" y="22" width="18" height="18" viewBox="0 0 16 16">'
            f'<path fill="{ACCENT}" d="{REPO_PATH}"/></svg>\n')
    name = repo["name"].rstrip("-")
    svg += text(52, 36, name, 17, TITLE, 700)

    desc = (repo.get("description") or "No description yet.").strip()
    wrapped = textwrap.wrap(desc, width=50)
    lines = wrapped[:2]
    if len(wrapped) > 2:
        lines[1] = lines[1][:47].rstrip() + "..."
    for i, line in enumerate(lines):
        svg += text(28, 68 + i * 20, line, 13, TEXT)

    y = h - 24
    x = 28
    lang = repo.get("language")
    if lang:
        color = LANG_COLORS.get(lang, ACCENT)
        svg += f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{color}"/>\n'
        svg += text(x + 16, y, lang, 12, MUTED)
        x += 16 + 8 * len(lang) + 14
    svg += (f'<svg x="{x}" y="{y - 12}" width="14" height="14" viewBox="0 0 16 16">'
            f'<path fill="{MUTED}" d="{STAR_PATH}"/></svg>\n')
    svg += text(x + 19, y, repo["stargazers_count"], 12, MUTED)
    x += 19 + 10 * len(str(repo["stargazers_count"])) + 16
    svg += (f'<svg x="{x}" y="{y - 12}" width="14" height="14" viewBox="0 0 16 16">'
            f'<path fill="{MUTED}" d="{FORK_PATH}"/></svg>\n')
    svg += text(x + 19, y, repo["forks_count"], 12, MUTED)
    return svg + "</svg>\n"


# --------------------------------------------------------------------- main
def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Fetching data for {USERNAME} ...")
    user = api(f"/users/{USERNAME}")
    repos = api(f"/users/{USERNAME}/repos", {"per_page": 100, "type": "owner"})
    own = [r for r in repos if not r["fork"]]

    stats = {
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(r["stargazers_count"] for r in own),
        "commits": optional(lambda: api("/search/commits", {
            "q": f"author:{USERNAME}", "per_page": 1})["total_count"]),
        "prs": optional(lambda: api("/search/issues", {
            "q": f"author:{USERNAME} type:pr", "per_page": 1})["total_count"]),
        "issues": optional(lambda: api("/search/issues", {
            "q": f"author:{USERNAME} type:issue", "per_page": 1})["total_count"]),
    }

    langs = {}
    for r in own:
        data = optional(lambda r=r: api(f"/repos/{USERNAME}/{r['name']}/languages"), {})
        for lang, size in data.items():
            langs[lang] = langs.get(lang, 0) + size

    (OUT_DIR / "stats.svg").write_text(build_stats_card(stats), encoding="utf-8")
    (OUT_DIR / "languages.svg").write_text(build_languages_card(langs), encoding="utf-8")
    print("  wrote stats.svg, languages.svg")

    by_name = {r["name"].lower(): r for r in repos}
    for name in FEATURED_REPOS:
        repo = by_name.get(name.lower()) or optional(
            lambda n=name: api(f"/repos/{USERNAME}/{n}"))
        if not repo:
            print(f"  skipped {name} (not found)", file=sys.stderr)
            continue
        out = OUT_DIR / f"project-{slug(name)}.svg"
        out.write_text(build_project_card(repo), encoding="utf-8")
        print(f"  wrote {out.name}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as err:
        sys.exit(f"GitHub API error {err.code}: {err.reason} "
                 f"(rate limit? set GITHUB_TOKEN and retry)")
