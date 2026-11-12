#!/usr/bin/env python3
"""Regenerate the profile README's SVGs and data sections.

Standard library only. Reads scripts/profile.json, pulls public repo data,
language byte counts and recent public events from the GitHub API, then:
  * writes assets/header-{light,dark}.svg      (animated header + illustration)
  * writes assets/status-<status>-{theme}.svg  (small status pills)
  * writes assets/panel-<name>-{theme}.svg     (stack, learning, language mix)
  * rewrites README.md between <!-- NAME:START --> / <!-- NAME:END --> markers
    for PROJECTS, MORE and ACTIVITY.

Icons in assets/icons/ are from Simple Icons (CC0) and are inlined as paths.

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
from datetime import datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICONS = ASSETS / "icons"
README = ROOT / "README.md"
CONFIG = json.loads((ROOT / "scripts" / "profile.json").read_text())
USER = CONFIG["username"]
API = "https://api.github.com"

# --------------------------------------------------------------------------
# Palette: warm paper + ink, with a wide set of accents. Light-theme accents
# are dark enough for text on paper; dark-theme accents are bright on ink.
# --------------------------------------------------------------------------
THEMES = {
    "light": {"bg": "#FFFAF2", "border": "#EADFCC", "ink": "#2A2433",
              "muted": "#6B6274", "chip": "#F6EEDF",
              "wood": "#C08A4E", "device": "#3A3346", "screen": "#211D2B"},
    "dark":  {"bg": "#17151F", "border": "#2F2A3D", "ink": "#F4EEE4",
              "muted": "#A9A1B5", "chip": "#221F2D",
              "wood": "#A87443", "device": "#4A445A", "screen": "#0F0D16"},
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
REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


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


def language_mix(repos: dict[str, dict]) -> list[tuple[str, float]]:
    skip = set(CONFIG.get("language_exclude", []))
    totals: dict[str, int] = {}
    for r in repos.values():
        if r.get("fork") or r["name"] == USER:
            continue
        for lang, n in gh(f"/repos/{USER}/{r['name']}/languages").items():
            if lang not in skip:
                totals[lang] = totals.get(lang, 0) + n
    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    top = [(k, v / total * 100) for k, v in ranked[:5]]
    rest = sum(v for _, v in ranked[5:]) / total * 100
    if rest >= 0.05:
        top.append(("Other", rest))
    return top


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


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text() if path.exists() else None
    if old != content:
        path.write_text(content)
        print(f"  wrote {path.relative_to(ROOT)}")


def icon_path(name: str | None) -> str | None:
    if not name:
        return None
    f = ICONS / f"{name}.svg"
    if not f.exists():
        return None
    m = re.search(r'<path d="([^"]+)"', f.read_text())
    return m.group(1) if m else None


def svg_open(W: int, H: int, title: str, desc: str, style: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-labelledby="t d">\n<title id="t">{x(title)}</title>\n<desc id="d">{x(desc)}</desc>\n'
            f'<style>{style}{REDUCED_MOTION}</style>\n')


# --------------------------------------------------------------------------
# Header: editorial left column + original desk illustration on the right
# --------------------------------------------------------------------------
def illustration(theme: str) -> str:
    t = THEMES[theme]
    A = lambda n: accent(n, theme)  # noqa: E731
    # laptop screen: blocky low-res half on the left, sharp half on the right
    blocks, colors = [], [A("teal"), A("sky"), A("sage"), A("teal")]
    for i in range(2):
        for j in range(3):
            blocks.append(f'<rect x="{84 + j*12}" y="{100 + i*20}" width="12" height="20" fill="{colors[(i+j) % 4]}" opacity="{0.55 + 0.15*((i+j) % 3)}"/>')
    for i in range(8):
        for j in range(6):
            blocks.append(f'<rect x="{120 + j*6}" y="{100 + i*5}" width="6" height="5" fill="{colors[(i//2 + j//2) % 4]}" opacity="{0.6 + 0.08*((i+j) % 4)}"/>')
    stars = "".join(
        f'<circle class="tw" style="animation-delay:{d}s" cx="{cx}" cy="{cy}" r="{r}" fill="{A(c)}"/>'
        for cx, cy, r, c, d in [(30, 30, 3, "mustard", 0), (250, 20, 2.5, "rose", 0.8),
                                (200, 50, 2, "sky", 1.6), (60, 70, 2, "plum", 1.1)])
    orbit = "M 20 78 Q 140 -10 262 70"
    return f'''<g transform="translate(500,14)">
  {stars}
  <path d="{orbit}" fill="none" stroke="{t["border"]}" stroke-width="1.5" stroke-dasharray="3 5"/>
  <g>
    <animateMotion path="{orbit}" dur="14s" repeatCount="indefinite" rotate="auto"/>
    <rect x="-5" y="-4" width="10" height="8" rx="2" fill="{t["device"]}"/>
    <rect x="-17" y="-3" width="10" height="6" fill="{A("sky")}"/>
    <rect x="7" y="-3" width="10" height="6" fill="{A("sky")}"/>
    <circle cx="0" cy="-7" r="2" fill="{A("rose")}"/>
  </g>
  <circle class="glow" cx="204" cy="126" r="24" fill="{A("mustard")}" opacity="0.16"/>
  <!-- lamp -->
  <rect x="206" y="166" width="22" height="5" rx="2" fill="{t["device"]}"/>
  <path d="M217 166 L 226 128 L 204 104" fill="none" stroke="{t["device"]}" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M190 116 L 204 96 L 214 110 Z" fill="{A("terracotta")}"/>
  <!-- books -->
  <rect x="34" y="152" width="40" height="9" rx="2" fill="{A("sky")}"/>
  <rect x="38" y="143" width="34" height="9" rx="2" fill="{A("rose")}"/>
  <rect x="36" y="134" width="30" height="9" rx="2" fill="{A("mustard")}"/>
  <!-- laptop -->
  <rect x="78" y="94" width="90" height="62" rx="5" fill="{t["device"]}"/>
  <rect x="84" y="100" width="78" height="40" fill="{t["screen"]}"/>
  {"".join(blocks)}
  <rect class="scan" x="84" y="100" width="2" height="40" fill="{t["ink"]}" opacity="0.7"/>
  <path d="M70 156 H 176 L 170 162 H 76 Z" fill="{t["device"]}"/>
  <!-- mug + steam -->
  <rect x="182" y="146" width="16" height="16" rx="3" fill="{A("plum")}"/>
  <path d="M198 150 q 6 0 6 5 t -6 5" fill="none" stroke="{A("plum")}" stroke-width="2.5"/>
  <path class="steam" d="M187 140 q -4 -6 0 -12 t 0 -12" fill="none" stroke="{t["muted"]}" stroke-width="2" stroke-linecap="round"/>
  <path class="steam" style="animation-delay:1.2s" d="M194 140 q -4 -6 0 -12 t 0 -12" fill="none" stroke="{t["muted"]}" stroke-width="2" stroke-linecap="round"/>
  <!-- plant -->
  <g class="sway">
    <ellipse cx="246" cy="128" rx="7" ry="16" fill="{A("sage")}" transform="rotate(-28 246 140)"/>
    <ellipse cx="256" cy="124" rx="7" ry="18" fill="{A("sage")}" transform="rotate(8 256 140)"/>
    <ellipse cx="264" cy="132" rx="6" ry="14" fill="{A("teal")}" transform="rotate(38 264 144)"/>
  </g>
  <path d="M240 142 H 270 L 266 162 H 244 Z" fill="{A("terracotta")}"/>
  <!-- desk -->
  <rect x="24" y="162" width="256" height="9" rx="3" fill="{t["wood"]}"/>
  <rect x="40" y="171" width="7" height="58" fill="{t["wood"]}"/>
  <rect x="256" y="171" width="7" height="58" fill="{t["wood"]}"/>
  <rect x="47" y="196" width="209" height="4" fill="{t["wood"]}" opacity="0.6"/>
</g>'''


def header_svg(theme: str) -> str:
    t = THEMES[theme]
    W, H = 800, 262
    x0 = 58
    name, size, name_y = CONFIG["name"], 66, 150

    steps = [0.0] + [0.85 * text_width(name[: i + 1], size, bold=True) for i in range(len(name))]
    clip_vals = ";".join(f"{s:.1f}" for s in steps[:-1]) + f";{steps[-1] + 60:.1f}"
    cursor_vals = ";".join(f"{x0 + s + 6:.1f}" for s in steps)
    type_dur = 0.11 * len(name)

    role_colors = ["terracotta", "teal", "plum", "sky"]
    roles = []
    for i, r in enumerate(CONFIG["roles"]):
        if i:
            roles.append(f'<tspan fill="{t["muted"]}"> / </tspan>')
        roles.append(f'<tspan fill="{accent(role_colors[i % 4], theme)}">{x(r)}</tspan>')

    meta = []
    for i, m in enumerate(CONFIG["meta"]):
        fill = t["ink"] if i == 0 else t["muted"]
        dx = ' dx="26"' if i else ""
        meta.append(f'<tspan{dx} fill="{fill}">{x(m)}</tspan>')

    style = (
        ".fade{animation:fade .8s ease-out both}"
        "@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
        ".blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        ".grow{transform-box:fill-box;transform-origin:left;animation:grow 1s ease-out both}"
        "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
        ".tw{animation:tw 3s ease-in-out infinite}@keyframes tw{50%{opacity:.2}}"
        ".glow{animation:glow 4s ease-in-out infinite}@keyframes glow{50%{opacity:.07}}"
        ".scan{animation:scan 3.5s ease-in-out infinite}@keyframes scan{0%,100%{transform:translateX(0)}50%{transform:translateX(76px)}}"
        ".steam{animation:steam 2.4s ease-out infinite}@keyframes steam{0%{opacity:0;transform:translateY(4px)}40%{opacity:.8}100%{opacity:0;transform:translateY(-6px)}}"
        ".sway{transform-box:fill-box;transform-origin:bottom center;animation:sway 5s ease-in-out infinite}"
        "@keyframes sway{0%,100%{transform:rotate(-3deg)}50%{transform:rotate(3deg)}}"
    )
    desc = f'{" / ".join(CONFIG["roles"])}. {", ".join(CONFIG["meta"])}. Illustration of a desk with a laptop sharpening a pixelated image, a lamp, books, a mug and a plant, with a satellite orbiting above.'
    return svg_open(W, H, name, desc, style) + f'''<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.5"/>
<rect x="30" y="30" width="5" height="{H-60}" rx="2.5" fill="{accent("terracotta", theme)}"/>
<g font-family="{MONO}">
  <text class="fade" x="{x0}" y="58" font-size="15" fill="{t["muted"]}">{x(CONFIG["handle"])}</text>
  <line class="fade" x1="{x0}" x2="470" y1="74" y2="74" stroke="{t["border"]}" stroke-width="1.5"/>
</g>
<clipPath id="type"><rect x="{x0}" y="{name_y-62}" width="{steps[-1] + 60:.1f}" height="80">
  <animate attributeName="width" values="{clip_vals}" calcMode="discrete" dur="{type_dur:.2f}s" begin="0s" fill="freeze"/>
</rect></clipPath>
<text x="{x0}" y="{name_y}" clip-path="url(#type)" font-family="{SANS}" font-size="{size}" font-weight="800" fill="{t["ink"]}" letter-spacing="-1">{x(name)}</text>
<rect class="blink" x="{x0 + steps[-1] + 6:.1f}" y="{name_y-50}" width="5" height="56" rx="2" fill="{accent("teal", theme)}">
  <animate attributeName="x" values="{cursor_vals}" calcMode="discrete" dur="{type_dur:.2f}s" begin="0s" fill="freeze"/>
</rect>
<text class="fade" style="animation-delay:{type_dur:.2f}s" x="{x0}" y="188" font-family="{MONO}" font-size="17" font-weight="600">{"".join(roles)}</text>
<rect class="grow" style="animation-delay:{type_dur + 0.3:.2f}s" x="{x0}" y="204" width="120" height="4" rx="2" fill="{accent("terracotta", theme)}"/>
<text class="fade" style="animation-delay:{type_dur + 0.5:.2f}s" x="{x0}" y="236" font-family="{MONO}" font-size="13" font-weight="600">{"".join(meta)}</text>
{illustration(theme)}
</svg>
'''


# --------------------------------------------------------------------------
# Project cards: accent stripe, breathing colour blob, pulsing status dot
# --------------------------------------------------------------------------
STATUS_DOT_PULSE = {"live", "in progress"}


def card_svg(p: dict, theme: str) -> str:
    t = THEMES[theme]
    a = accent(p["accent"], theme)
    W, H, pad = 400, 230, 24
    inner = W - 2 * pad

    status = p["status"]
    st_w = text_width(status, 12, bold=True) + 30
    corner = p.get("updated", "")
    if p.get("built_with"):
        corner = "with " + ", ".join(f"@{h}" for h in p["built_with"])

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
    upd = (f'<text x="{W-pad}" y="40" text-anchor="end" font-size="11.5" fill="{t["muted"]}">{x(corner)}</text>'
           if corner else "")

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
# Panels (two per row in the README, one per row on phones)
# --------------------------------------------------------------------------
PANEL_W, PANEL_H, PAD = 400, 182, 24


def panel_frame(theme: str, title: str, color: str, body: str, desc: str, style: str = "") -> str:
    t = THEMES[theme]
    a = accent(color, theme)
    return svg_open(PANEL_W, PANEL_H, title, desc, style) + f'''<rect x="1" y="1" width="{PANEL_W-2}" height="{PANEL_H-2}" rx="16" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.5"/>
<rect x="{PAD}" y="26" width="18" height="4" rx="2" fill="{a}"/>
<text x="{PAD}" y="52" font-family="{SANS}" font-size="16" font-weight="800" fill="{t["ink"]}">{x(title)}</text>
<g font-family="{SANS}">{body}</g>
</svg>
'''


def icon_tiles(items: list, color: str, theme: str, dashed: bool = False) -> str:
    t = THEMES[theme]
    a = accent(color, theme)
    out, cx, y = [], PAD, 66
    for label, icon, *tile_text in items:
        stroke = f'stroke="{a}" stroke-dasharray="4 3"' if dashed else f'stroke="{t["border"]}"'
        out.append(f'<rect x="{cx}" y="{y}" width="42" height="42" rx="11" fill="{t["chip"]}" {stroke} stroke-width="1.3"/>')
        path = icon_path(icon)
        if path:
            out.append(f'<path transform="translate({cx+10},{y+10}) scale({22/24:.4f})" d="{path}" fill="{a}"/>')
        else:
            first = re.findall(r"[A-Za-z]+", label)[0]
            initials = tile_text[0] if tile_text else (first if first.isupper() else first[:2])[:3]
            out.append(f'<text x="{cx+21}" y="{y+26}" text-anchor="middle" font-size="12" font-weight="800" fill="{a}">{x(initials)}</text>')
        cx += 50
    return "".join(out)


def label_lines(labels: list[str], theme: str, y: float = 132) -> str:
    t = THEMES[theme]
    lines = wrap(" · ".join(labels), 13, PANEL_W - 2 * PAD, 2)
    return "".join(f'<text x="{PAD}" y="{y + i*19}" font-size="13" fill="{t["muted"]}">{x(l)}</text>'
                   for i, l in enumerate(lines))


def stack_panel(group: dict, theme: str) -> str:
    labels = [item[0] for item in group["items"]]
    body = icon_tiles(group["items"], group["accent"], theme) + label_lines(labels, theme)
    return panel_frame(theme, group["label"], group["accent"], body, f'{group["label"]}: {", ".join(labels)}.')


def learning_panel(theme: str) -> str:
    items = CONFIG["learning"]
    a = accent("rose", theme)
    labels = [item[0] for item in items]
    body = (icon_tiles(items, "rose", theme, dashed=True) + label_lines(labels, theme) +
            f'<circle class="pulse" cx="{PANEL_W-PAD-74}" cy="46" r="4" fill="{a}"/>'
            f'<text x="{PANEL_W-PAD}" y="50.5" text-anchor="end" font-size="12" font-weight="700" fill="{a}">in progress</text>')
    style = ".pulse{animation:pulse 1.8s ease-in-out infinite}@keyframes pulse{50%{opacity:.25}}"
    return panel_frame(theme, "Learning right now", "rose", body,
                       f'Currently learning: {", ".join(labels)}.', style)


def language_panel(mix: list[tuple[str, float]], theme: str) -> str:
    t = THEMES[theme]
    colors = ["terracotta", "teal", "mustard", "plum", "sky", "sage"]
    bar_w, bx, by = PANEL_W - 2 * PAD, PAD, 76
    segs, legend, cx = [], [], bx
    for i, (lang, pct) in enumerate(mix):
        w = bar_w * pct / 100
        col = accent(colors[i % len(colors)], theme) if lang != "Other" else t["muted"]
        segs.append(f'<rect class="grow" style="animation-delay:{i*0.12:.2f}s" x="{cx:.2f}" y="{by}" width="{max(w, 0.5):.2f}" height="12" fill="{col}"/>')
        cx += w
        col_x = PAD + (i % 3) * 120
        row_y = 116 + (i // 3) * 36
        legend.append(f'<circle cx="{col_x+5}" cy="{row_y-4}" r="4.5" fill="{col}"/>'
                      f'<text x="{col_x+15}" y="{row_y}" font-size="12.5" fill="{t["ink"]}">{x(lang)}</text>'
                      f'<text x="{col_x+15}" y="{row_y+16}" font-size="12" font-weight="700" fill="{t["muted"]}">{pct:.1f}%</text>')
    body = (f'<text x="{PANEL_W-PAD}" y="50.5" text-anchor="end" font-size="11.5" fill="{t["muted"]}">public repos · notebooks excluded</text>'
            f'<clipPath id="bar"><rect x="{bx}" y="{by}" width="{bar_w}" height="12" rx="6"/></clipPath>'
            f'<g clip-path="url(#bar)">{"".join(segs)}</g>{"".join(legend)}')
    style = (".grow{transform-box:fill-box;transform-origin:left;animation:grow .9s ease-out both}"
             "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}")
    desc = "Language mix by bytes of code in public repos: " + ", ".join(f"{l} {p:.1f}%" for l, p in mix) + "."
    return panel_frame(theme, "Language mix", "mustard", body, desc, style)


# --------------------------------------------------------------------------
# README sections
# --------------------------------------------------------------------------
def picture(name: str, alt: str, extra: str = "") -> str:
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
            f'<img src="assets/{name}-light.svg" alt="{x(alt)}"{extra}></picture>')


def month(iso: str) -> str:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %Y")


def projects_section(featured: list[dict]) -> str:
    cards, links = [], []
    for p in featured:
        alt = f'{p["title"]} ({p["status"]}): {p["pitch"]} Stack: {", ".join(p["stack"])}.'
        img = picture(f'card-{slug(p["title"])}', alt)
        cards.append(f'<a href="{p["url"]}">{img}</a>' if p.get("url") else img)
        bits = []
        if p.get("repo_url"):
            bits.append(f'<a href="{p["repo_url"]}">code</a>')
        if p.get("homepage"):
            bits.append(f'<a href="{p["homepage"]}">live demo</a>')
        if p.get("built_with"):
            bits.append("built with " + ", ".join(
                f'<a href="https://github.com/{h}">@{h}</a>' for h in p["built_with"]))
        if bits:
            links.append(f'<b>{x(p["title"])}</b> {" · ".join(bits)}')
    rows = []
    for i in range(0, len(cards), 2):
        rows.append('<p align="center">\n  ' + "\n  ".join(cards[i:i + 2]) + "\n</p>")
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
    print("Fetching repos, languages and events…")
    repos = fetch_repos()
    events = gh(f"/users/{USER}/events/public?per_page=50")
    mix = language_mix(repos)

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
        for p in featured:
            write(ASSETS / f"card-{slug(p['title'])}-{theme}.svg", card_svg(p, theme))
        for group in CONFIG["stack"]:
            write(ASSETS / f"panel-{slug(group['label'])}-{theme}.svg", stack_panel(group, theme))
        write(ASSETS / f"panel-learning-{theme}.svg", learning_panel(theme))
        write(ASSETS / f"panel-languages-{theme}.svg", language_panel(mix, theme))

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
