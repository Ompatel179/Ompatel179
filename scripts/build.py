#!/usr/bin/env python3
"""Regenerate the profile README's SVGs and data sections.

Standard library only. Reads scripts/profile.json, pulls public repo data and
recent public events from the GitHub API, then:
  * writes assets/header-{light,dark}.svg
  * writes assets/card-<slug>-{light,dark}.svg for each featured project
  * writes assets/stack-{light,dark}.svg
  * rewrites README.md between <!-- NAME:START --> / <!-- NAME:END --> markers
    for PROJECTS, MORE and ACTIVITY.

Usage:  GITHUB_TOKEN=... python3 scripts/build.py
The token is optional (unauthenticated calls work, with a lower rate limit).
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
CONFIG = json.loads((ROOT / "scripts" / "profile.json").read_text())
USER = CONFIG["username"]
API = "https://api.github.com"

# --------------------------------------------------------------------------
# Palette: warm paper + ink, with a wide set of accents. Each accent has a
# light-theme value (dark enough for text on paper, >= 4.5:1) and a
# dark-theme value (bright enough on ink).
# --------------------------------------------------------------------------
THEMES = {
    "light": {"bg": "#FFFAF2", "border": "#EADFCC", "ink": "#2A2433",
              "muted": "#6B6274", "chip": "#F6EEDF"},
    "dark":  {"bg": "#17151F", "border": "#2F2A3D", "ink": "#F4EEE4",
              "muted": "#A9A1B5", "chip": "#221F2D"},
}
ACCENTS = {
    "terracotta": {"light": "#B9481F", "dark": "#FF8A65"},
    "teal":       {"light": "#1C746C", "dark": "#4FD1C5"},
    "plum":       {"light": "#7B3F8C", "dark": "#D29BF0"},
    "mustard":    {"light": "#8F5E0E", "dark": "#F6C453"},
    "sky":        {"light": "#2563A8", "dark": "#7CB8FF"},
    "rose":       {"light": "#B3325A", "dark": "#FF7AA2"},
    "sage":       {"light": "#3F6F2C", "dark": "#9ED07F"},
}
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def accent(name: str, theme: str) -> str:
    return ACCENTS[name][theme]


# --------------------------------------------------------------------------
# GitHub API
# --------------------------------------------------------------------------
def gh(path: str):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-builder",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_repos() -> dict[str, dict]:
    repos = gh(f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed")
    return {r["name"]: r for r in repos if not r.get("private")}


def find_repo(repos: dict[str, dict], name: str) -> dict | None:
    """Look a configured repo up by name, following GitHub's redirect if it was renamed."""
    if not name:
        return None
    if name in repos:
        return repos[name]
    try:
        r = gh(f"/repos/{USER}/{name}")  # 301 for renamed repos; urllib follows it
    except urllib.error.HTTPError:
        print(f"  warning: repo '{name}' not found; update scripts/profile.json")
        return None
    if r.get("private"):
        return None
    print(f"  note: '{name}' is now '{r['name']}'; update scripts/profile.json")
    return r


# --------------------------------------------------------------------------
# Text measurement: rough per-glyph widths (in em) for a Helvetica-like sans.
# Deliberately a little generous so text never clips.
# --------------------------------------------------------------------------
_NARROW = set("iljIl.,:;'|!`()[]{} ")
_SEMI = set("frt-/\"*")
_WIDE = set("mwMW@%")


def text_width(text: str, size: float, bold: bool = False, mono: bool = False) -> float:
    if mono:
        return len(text) * 0.61 * size
    w = 0.0
    for ch in text:
        if ch in _NARROW:
            w += 0.29
        elif ch in _SEMI:
            w += 0.37
        elif ch in _WIDE:
            w += 0.86
        elif ch == "·":
            w += 0.3
        elif ch == "→":
            w += 1.0
        elif ch.isupper() or not ch.isascii():
            w += 0.69
        elif ch.isdigit():
            w += 0.57
        else:
            w += 0.55
    return w * size * (1.07 if bold else 1.0) * 1.04


def wrap(text: str, size: float, max_w: float, max_lines: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if text_width(trial, size) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while text_width(last + "…", size) > max_w and " " in last:
            last = last.rsplit(" ", 1)[0]
        lines[-1] = last + "…"
    return lines


def x(text: str) -> str:
    return escape(text, quote=True)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text() if path.exists() else None
    if old != content:
        path.write_text(content)
        print(f"  wrote {path.relative_to(ROOT)}")


REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
def header_svg(theme: str) -> str:
    t = THEMES[theme]
    W, H = 800, 210
    greet = "Hi, I'm "
    name = CONFIG["name"]
    line = greet + name
    size = 50
    x0, y0 = 40, 122

    # discrete typing steps: clip width after each character
    # the generic estimator runs ~15% wide for this heavy display weight; scale it
    # for the cursor, and let the final clip value overshoot so nothing is cut off
    steps = [0.0] + [0.85 * text_width(line[: i + 1], size, bold=True) for i in range(len(line))]
    clip_vals = ";".join(f"{s:.1f}" for s in steps[:-1]) + f";{steps[-1] + 60:.1f}"
    cursor_vals = ";".join(f"{x0 + s + 6:.1f}" for s in steps)
    type_dur = 0.09 * len(line)

    # role line: each segment gets its own accent
    parts = [p.strip() for p in CONFIG["role"].split("·")]
    colors = ["terracotta", "teal", "plum", "sky", "sage"]
    role_size = 23
    spans = []
    for i, part in enumerate(parts):
        if i:
            spans.append(f'<tspan dx="12" fill="{t["muted"]}">·</tspan>')
        dx = ' dx="12"' if i else ""
        spans.append(f'<tspan{dx} fill="{accent(colors[i % len(colors)], theme)}">{x(part)}</tspan>')

    note = CONFIG["header_note"]
    note_w = text_width(note, 13, bold=True) + 26

    # playful dot constellation on the right
    dots = [
        (640, 64, 15, "terracotta", 0.0), (700, 46, 9, "mustard", 0.6),
        (742, 92, 20, "teal", 1.2), (676, 118, 11, "plum", 0.3),
        (724, 158, 13, "rose", 0.9), (650, 170, 7, "sky", 1.5),
        (764, 140, 6, "sage", 0.45),
    ]
    dot_svg = "\n".join(
        f'<circle class="bob" style="animation-delay:{d}s" cx="{cx_}" cy="{cy}" r="{r}" fill="{accent(c, theme)}"/>'
        for cx_, cy, r, c, d in dots
    )
    squiggle = accent("mustard", theme)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">{x(line)}</title>
<desc id="d">{x(CONFIG["role"])}. {x(note)}.</desc>
<style>
.bob{{animation:bob 5s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-6px)}}}}
.fade{{animation:fade .8s ease-out both}}
@keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.blink{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.draw{{stroke-dasharray:240;animation:draw 1.6s ease-out 1.4s both}}
@keyframes draw{{from{{stroke-dashoffset:240}}to{{stroke-dashoffset:0}}}}
{REDUCED_MOTION}
</style>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.5"/>
<g class="fade">
  <rect x="{x0}" y="34" width="{note_w:.1f}" height="26" rx="13" fill="{t["chip"]}" stroke="{t["border"]}"/>
  <circle cx="{x0+14}" cy="47" r="4" fill="{accent("sage", theme)}"/>
  <text x="{x0+24}" y="51.5" font-family="{SANS}" font-size="13" font-weight="600" fill="{t["muted"]}">{x(note)}</text>
</g>
<clipPath id="type"><rect x="{x0}" y="{y0-50}" width="{steps[-1] + 20:.1f}" height="66">
  <animate attributeName="width" values="{clip_vals}" calcMode="discrete" dur="{type_dur:.2f}s" begin="0s" fill="freeze"/>
</rect></clipPath>
<text x="{x0}" y="{y0}" clip-path="url(#type)" font-family="{SANS}" font-size="{size}" font-weight="800" fill="{t["ink"]}" letter-spacing="-0.5">{x(greet)}<tspan fill="{accent("terracotta", theme)}">{x(name)}</tspan></text>
<rect class="blink" x="{x0 + steps[-1] + 6:.1f}" y="{y0-40}" width="4" height="46" rx="2" fill="{accent("teal", theme)}">
  <animate attributeName="x" values="{cursor_vals}" calcMode="discrete" dur="{type_dur:.2f}s" begin="0s" fill="freeze"/>
</rect>
<text class="fade" style="animation-delay:{type_dur+0.4:.2f}s" x="{x0}" y="{y0+46}" font-family="{SANS}" font-size="{role_size}" font-weight="700">{"".join(spans)}</text>
<path class="draw" d="M {x0} {y0+64} q 20 -10 40 0 t 40 0 t 40 0 t 40 0" fill="none" stroke="{squiggle}" stroke-width="3" stroke-linecap="round"/>
{dot_svg}
</svg>
'''


# --------------------------------------------------------------------------
# Project cards
# --------------------------------------------------------------------------
STATUS_DOT_PULSE = {"live", "in progress"}


def card_svg(p: dict, theme: str) -> str:
    t = THEMES[theme]
    a = accent(p["accent"], theme)
    W, H, pad = 400, 230, 24
    inner = W - 2 * pad

    status = p["status"]
    st_w = text_width(status, 12, bold=True) + 30
    updated = p.get("updated", "")

    title_y = 76
    lines = wrap(p["pitch"], 13.5, inner, 3)
    pitch = "".join(
        f'<tspan x="{pad}" dy="{0 if i == 0 else 19.5}">{x(l)}</tspan>' for i, l in enumerate(lines)
    )
    pitch_y = 102
    stats_y = pitch_y + 19.5 * (len(lines) - 1) + 25
    stats = p["stats"]
    while text_width(stats, 12, mono=True) > inner and " · " in stats:
        stats = stats.rsplit(" · ", 1)[0]

    chips, cx, chip_y = [], pad, H - 48
    for item in p["stack"]:
        w = text_width(item, 12) + 18
        if cx + w > W - pad:
            break
        chips.append(
            f'<rect x="{cx:.1f}" y="{chip_y}" width="{w:.1f}" height="24" rx="12" fill="{t["chip"]}" stroke="{t["border"]}"/>'
            f'<text x="{cx + w/2:.1f}" y="{chip_y+16}" text-anchor="middle" font-size="12" fill="{t["ink"]}">{x(item)}</text>'
        )
        cx += w + 6

    pulse = ' class="pulse"' if status in STATUS_DOT_PULSE else ""
    upd = (f'<text x="{W-pad}" y="40" text-anchor="end" font-size="11.5" fill="{t["muted"]}">{x(updated)}</text>'
           if updated else "")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">{x(p["title"])} ({x(status)})</title>
<desc id="d">{x(p["pitch"])} {x(p["stats"])}. Built with {x(", ".join(p["stack"]))}.</desc>
<style>
.blob{{animation:breathe 7s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
@keyframes breathe{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.12)}}}}
.pulse{{animation:pulse 1.8s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
{REDUCED_MOTION}
</style>
<clipPath id="c"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16"/></clipPath>
<g clip-path="url(#c)">
  <rect x="1" y="1" width="{W-2}" height="{H-2}" fill="{t["bg"]}"/>
  <circle class="blob" cx="{W-18}" cy="{H-6}" r="62" fill="{a}" opacity="0.13"/>
  <rect x="1" y="1" width="6" height="{H-2}" fill="{a}"/>
</g>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="none" stroke="{t["border"]}" stroke-width="1.5"/>
<g font-family="{SANS}">
  <rect x="{pad}" y="24" width="{st_w:.1f}" height="22" rx="11" fill="{a}" fill-opacity="0.14"/>
  <circle{pulse} cx="{pad+12}" cy="35" r="4" fill="{a}"/>
  <text x="{pad+21}" y="39.5" font-size="12" font-weight="700" fill="{a}">{x(status)}</text>
  {upd}
  <text x="{pad}" y="{title_y}" font-size="22" font-weight="800" fill="{t["ink"]}" letter-spacing="-0.3">{x(p["title"])}</text>
  <text x="{pad}" y="{pitch_y}" font-size="13.5" fill="{t["muted"]}">{pitch}</text>
  <text x="{pad}" y="{stats_y:.1f}" font-family="{MONO}" font-size="12" font-weight="700" fill="{a}">{x(stats)}</text>
  {"".join(chips)}
</g>
</svg>
'''


# --------------------------------------------------------------------------
# Tech stack
# --------------------------------------------------------------------------
def stack_svg(theme: str) -> str:
    t = THEMES[theme]
    W, pad, label_w = 520, 22, 104
    chip_h, gap, row_gap = 26, 7, 10
    max_x = W - pad
    rows_svg, y = [], 30

    def chip_row(label, color, items, dashed=False):
        nonlocal y
        a = accent(color, theme)
        out = [f'<text x="{pad}" y="{y+17}" font-size="12.5" font-weight="700" fill="{a}">{x(label)}</text>']
        cx = pad + label_w
        for item in items:
            w = text_width(item, 13) + 22 + (12 if dashed else 0)
            if cx + w > max_x:
                cx = pad + label_w
                y += chip_h + gap
            dash = ' stroke-dasharray="4 3"' if dashed else ""
            fill = "none" if dashed else t["chip"]
            stroke = a if dashed else t["border"]
            out.append(f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="{chip_h}" rx="13" fill="{fill}" stroke="{stroke}" stroke-width="1.3"{dash}/>')
            tx = cx + 11
            if dashed:
                out.append(f'<circle class="pulse" cx="{cx+12:.1f}" cy="{y+13}" r="3.5" fill="{a}"/>')
                tx += 11
            out.append(f'<text x="{tx:.1f}" y="{y+17.5}" font-size="13" fill="{t["ink"]}">{x(item)}</text>')
            cx += w + gap
        y += chip_h + row_gap
        return "".join(out)

    rows_svg.append(f'<text x="{pad}" y="{y}" font-size="15" font-weight="800" fill="{t["ink"]}">Built with</text>')
    y += 14
    for group in CONFIG["stack"]:
        rows_svg.append(chip_row(group["label"], group["accent"], group["items"]))

    y += 12
    rows_svg.append(f'<line x1="{pad}" x2="{W-pad}" y1="{y}" y2="{y}" stroke="{t["border"]}" stroke-dasharray="2 4"/>')
    y += 30
    rows_svg.append(f'<text x="{pad}" y="{y}" font-size="15" font-weight="800" fill="{t["ink"]}">Learning right now</text>')
    y += 14
    rows_svg.append(chip_row("in progress", "rose", CONFIG["learning"], dashed=True))
    H = int(y + 12)

    built = "; ".join(f'{g["label"]}: {", ".join(g["items"])}' for g in CONFIG["stack"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">Tech stack</title>
<desc id="d">Built with: {x(built)}. Currently learning: {x(", ".join(CONFIG["learning"]))}.</desc>
<style>.pulse{{animation:pulse 1.8s ease-in-out infinite}}@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}{REDUCED_MOTION}</style>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.5"/>
<g font-family="{SANS}">{"".join(rows_svg)}</g>
</svg>
'''


# --------------------------------------------------------------------------
# README sections
# --------------------------------------------------------------------------
def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def picture(name: str, alt: str, width: int | None = None) -> str:
    w = f' width="{width}"' if width else ""
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
            f'<img src="assets/{name}-light.svg" alt="{x(alt)}"{w}></picture>')


def month(iso: str) -> str:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %Y")


def projects_section(featured: list[dict]) -> str:
    cards, links = [], []
    for p in featured:
        alt = f'{p["title"]} ({p["status"]}): {p["pitch"]} Stack: {", ".join(p["stack"])}.'
        img = picture(f'card-{slug(p["title"])}', alt)
        if p.get("url"):
            cards.append(f'<a href="{p["url"]}">{img}</a>')
        else:
            cards.append(img)
        bits = []
        if p.get("repo_url"):
            bits.append(f'<a href="{p["repo_url"]}">code</a>')
        if p.get("homepage"):
            bits.append(f'<a href="{p["homepage"]}">live demo</a>')
        if bits:
            links.append(f'<b>{x(p["title"])}</b> {" · ".join(bits)}')
    rows = []
    for i in range(0, len(cards), 2):
        rows.append(f'<p align="center">\n  {cards[i]}\n  ' + ("\n  ".join(cards[i + 1:i + 2])) + "\n</p>")
    return "\n".join(rows) + f'\n<p align="center"><sub>{" &nbsp;|&nbsp; ".join(links)}</sub></p>'


def more_section(more: list[dict], repos: dict) -> str:
    out = []
    for m in more:
        r = find_repo(repos, m["repo"]) or {}
        url = r.get("html_url", f"https://github.com/{USER}/{m['repo']}")
        pitch = r.get("description") or m["pitch"]
        line = f'- **[{m["title"]}]({url})**: {pitch}  \n  <sub>{m["stack"]}'
        if r.get("homepage"):
            line += f' · [live demo]({r["homepage"]})'
        out.append(line + "</sub>")
    return "\n".join(out)


def pr_title(repo: str, number: int) -> str | None:
    try:
        return gh(f"/repos/{repo}/pulls/{number}").get("title")
    except urllib.error.HTTPError:
        return None


def activity_section(events: list[dict]) -> str:
    skip = set(CONFIG.get("exclude_from_activity", []))
    events = [e for e in events if e["repo"]["name"] not in skip]
    merges = {(e["repo"]["name"], e["created_at"][:15]) for e in events
              if e["type"] == "PullRequestEvent" and e["payload"].get("action") in ("merged", "closed")}
    seen_prs, items = set(), []
    for e in events:
        repo = e["repo"]["name"]
        short = repo.split("/", 1)[1]
        repo_link = f"[{short}](https://github.com/{repo})"
        when = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")).strftime("%b&nbsp;%d")
        p, kind = e["payload"], e["type"]
        text = None
        if kind == "PullRequestEvent":
            num = p.get("number") or p.get("pull_request", {}).get("number")
            action = p.get("action")
            if action == "closed" and p.get("pull_request", {}).get("merged"):
                action = "merged"
            if action not in ("opened", "merged") or (repo, num) in seen_prs:
                continue
            seen_prs.add((repo, num))
            title = p.get("pull_request", {}).get("title") or pr_title(repo, num)
            verb = "Merged" if action == "merged" else "Opened"
            t = f" *{escape(title, quote=False)}*" if title else ""
            text = f"{verb} PR [#{num}](https://github.com/{repo}/pull/{num}){t} in {repo_link}"
        elif kind == "ReleaseEvent":
            rel = p.get("release", {})
            text = f"Released [{rel.get('tag_name', 'a new version')}]({rel.get('html_url', '')}) of {repo_link}"
        elif kind == "CreateEvent" and p.get("ref_type") == "repository":
            text = f"Created {repo_link}"
        elif kind == "PushEvent":
            if (repo, e["created_at"][:15]) in merges:
                continue  # push that came from merging a PR
            branch = (p.get("ref") or "").replace("refs/heads/", "")
            text = f"Pushed to `{branch}` in {repo_link}" if branch else f"Pushed to {repo_link}"
        if text:
            items.append(f"- {text} <sub>·&nbsp;{when}</sub>")
        if len(items) == 5:
            break
    return "\n".join(items) if items else "- Quiet week. Probably reading papers."


def replace_section(readme: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:START -->)(.*?)(<!-- {name}:END -->)", re.S)
    if not pattern.search(readme):
        sys.exit(f"README is missing the {name} markers")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", readme)


# --------------------------------------------------------------------------
def main() -> None:
    print("Fetching repos and events…")
    repos = fetch_repos()
    events = gh(f"/users/{USER}/events/public?per_page=50")

    featured = []
    for p in CONFIG["featured"]:
        p = dict(p)
        r = find_repo(repos, p.get("repo", ""))
        if r:
            p["repo_url"] = r["html_url"]
            p.setdefault("url", r["html_url"])
            if r.get("homepage"):
                p["homepage"] = r["homepage"]
            p["updated"] = "updated " + month(r["pushed_at"])
        featured.append(p)

    print("Rendering SVGs…")
    for theme in THEMES:
        write(ASSETS / f"header-{theme}.svg", header_svg(theme))
        write(ASSETS / f"stack-{theme}.svg", stack_svg(theme))
        for p in featured:
            write(ASSETS / f"card-{slug(p['title'])}-{theme}.svg", card_svg(p, theme))

    print("Updating README…")
    readme = README.read_text()
    new = replace_section(readme, "PROJECTS", projects_section(featured))
    new = replace_section(new, "MORE", more_section(CONFIG["more"], repos))
    new = replace_section(new, "ACTIVITY", activity_section(events))
    if new != readme:
        README.write_text(new)
        print("  wrote README.md")
    print("Done.")


if __name__ == "__main__":
    main()
