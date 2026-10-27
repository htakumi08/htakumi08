"""Build self-hosted profile SVGs from public repositories and GitHub activity.

Requires Python 3.11+ and the GitHub CLI. No third-party Python packages.
"""

import html
import json
import math
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

USER = "htakumi08"
ROOT = Path(__file__).resolve().parents[1]
BG, PANEL, CYAN, BLUE, WHITE, MUTED = (
    "#07111f", "#0c1c30", "#42e8e0", "#438bff", "#edf7ff", "#8fa8c4"
)


def gh_json(*args: str) -> dict | list:
    result = subprocess.run(
        ["gh", "api", *args], check=True, capture_output=True, text=True, timeout=90
    )
    return json.loads(result.stdout)


def summarize(repos: list[dict]) -> dict:
    projects = [r for r in repos if not r["fork"] and not r["private"] and r["name"] != USER]
    return {
        "projects": len(projects),
        "stars": sum(r["stargazers_count"] for r in projects),
        "languages": dict(Counter(r["language"] for r in projects if r["language"])),
    }


def fetch_data() -> dict:
    pages = gh_json(f"users/{USER}/repos?type=owner&per_page=100", "--paginate", "--slurp")
    repos = [repo for page in pages for repo in page]
    query = """query($login:String!) {
      user(login:$login) { contributionsCollection {
        contributionCalendar { weeks { contributionDays { date weekday contributionCount } } }
      } }
    }"""
    response = gh_json("graphql", "-f", f"query={query}", "-f", f"login={USER}")
    if response.get("errors") or not response.get("data", {}).get("user"):
        raise RuntimeError("GitHub did not return a contribution calendar")
    weeks = response["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    today = datetime.now(timezone.utc).date().isoformat()
    days = [
        {"date": day["date"], "weekday": day["weekday"], "count": day["contributionCount"], "week": week}
        for week, value in enumerate(weeks)
        for day in value["contributionDays"] if day["date"] <= today
    ]
    if not days:
        raise RuntimeError("Empty contribution calendar; retaining the previous images")
    return {"summary": summarize(repos), "days": days}


def text(x: float, y: float, value: object, size: int = 16, color: str = WHITE, extra: str = "") -> str:
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{html.escape(str(value))}</text>'


def frame(width: int, height: int, title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title, quote=True)}">
<title>{html.escape(title)}</title>
<defs><linearGradient id="accent"><stop stop-color="{CYAN}"/><stop offset="1" stop-color="{BLUE}"/></linearGradient></defs>
<style>text{{font-family:Inter,Segoe UI,Arial,sans-serif}}.mono{{font-family:SFMono-Regular,Consolas,monospace}}@media(prefers-reduced-motion:reduce){{.motion{{display:none}}}}</style>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="20" fill="{BG}" stroke="#1d3550"/>
{body}</svg>'''


def render_stats(summary: dict, days: list[dict]) -> str:
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    body = text(34, 40, "ACTIVITY / AT A GLANCE", 14, CYAN, 'class="mono" letter-spacing="2"')
    for i, (value, label) in enumerate([
        (summary["projects"], "PUBLIC PROJECTS"), (total, "CONTRIBUTIONS"),
        (active, "ACTIVE DAYS"), (summary["stars"], "PROJECT STARS"),
    ]):
        x = 34 + i * 225
        body += f'<rect x="{x}" y="66" width="208" height="118" rx="12" fill="{PANEL}"/>'
        body += text(x + 20, 120, value, 38, WHITE, 'font-weight="700"')
        body += text(x + 20, 153, label, 11, MUTED, 'class="mono" letter-spacing="1"')
    language_text = "  /  ".join(sorted(summary["languages"])) or "New projects ahead"
    body += text(34, 218, "Primary repository languages: " + language_text, 14, MUTED)
    period = f'{days[0]["date"]} — {days[-1]["date"]}' if days else "No activity yet"
    body += text(34, 249, period + "  ·  Original public projects only; forks excluded", 11, MUTED, 'class="mono"')
    return frame(960, 274, "GitHub activity summary", body)


def render_city(days: list[dict]) -> str:
    body = text(34, 42, "CONTRIBUTION CITY", 18, WHITE, 'font-weight="700" letter-spacing="2"')
    body += text(34, 68, "Small commits. A growing skyline.", 14, MUTED)
    # Each real date becomes one building, with height proportional to log(count + 1).
    count_weeks = max((d["week"] for d in days), default=52) + 1
    dx = min(14, 742 / max(1, count_weeks))
    for day in sorted(days, key=lambda d: (d["week"] + d["weekday"], d["week"])):
        x = 125 + day["week"] * dx - day["weekday"] * 12
        y = 128 + day["week"] * 2.5 + day["weekday"] * 12
        h = 2 if day["count"] == 0 else 9 + math.log2(day["count"] + 1) * 12
        front, side, top = ("#0e273e", "#0a1e31", "#19384e") if not day["count"] else ("#147b9c", "#2251a1", CYAN)
        points = [(x, y-h), (x+dx-2, y+2.5-h), (x+dx-14, y+12-h), (x-12, y+9.5-h)]
        p = " ".join(f"{a:.1f},{b:.1f}" for a, b in points)
        label = html.escape(f'{day["date"]}: {day["count"]} contributions')
        body += f'<g class="building"><title>{label}</title>'
        body += f'<path d="M{x-12},{y+9.5-h} L{x+dx-14},{y+12-h} V{y+12} L{x-12},{y+9.5}Z" fill="{front}"/>'
        body += f'<path d="M{x+dx-14},{y+12-h} L{x+dx-2},{y+2.5-h} V{y+2.5} L{x+dx-14},{y+12}Z" fill="{side}"/>'
        body += f'<polygon points="{p}" fill="{top}" stroke="{BG}" stroke-width="0.6"/></g>'
    body += '<path d="M60 362H900" stroke="#1d3550"/>'
    body += text(34, 397, f'{sum(d["count"] for d in days)} contributions · past year', 14, CYAN, 'class="mono"')
    body += text(650, 397, "ONE BLOCK = ONE DAY", 12, MUTED, 'class="mono" letter-spacing="1"')
    return frame(960, 428, "3D contribution skyline based on real GitHub activity", body)


def render_grid(days: list[dict]) -> str:
    body = text(34, 40, "COMMIT SIGNAL", 14, CYAN, 'class="mono" letter-spacing="2"')
    colors = ["#11283d", "#13566c", "#197d97", "#29aebb", CYAN]
    for day in days:
        level = min(4, math.ceil(math.log2(day["count"] + 1)))
        x, y = 36 + day["week"] * 16.6, 65 + day["weekday"] * 17
        body += f'<rect x="{x:.1f}" y="{y}" width="12.5" height="12.5" rx="3" fill="{colors[level]}"><title>{day["date"]}: {day["count"]} contributions</title></rect>'
    body += '<g class="motion"><rect x="36" y="62" width="2" height="120" fill="#75fff4" opacity="0.7"><animate attributeName="x" values="36;918;36" dur="14s" repeatCount="indefinite"/></rect></g>'
    body += text(34, 218, "PUBLIC SIGNALS / CONTINUOUS EXPLORATION", 11, MUTED, 'class="mono" letter-spacing="1"')
    return frame(960, 242, "Contribution heatmap with an animated scan line", body)


def render_assets(data: dict) -> dict[str, str]:
    return {
        "stats.svg": render_stats(data["summary"], data["days"]),
        "city.svg": render_city(data["days"]),
        "activity.svg": render_grid(data["days"]),
    }


def update(output: Path) -> None:
    data = fetch_data()
    assets = render_assets(data)
    for svg in assets.values():
        ET.fromstring(svg)
    output.mkdir(parents=True, exist_ok=True)
    for name, svg in assets.items():
        temporary = output / f".{name}.tmp"
        temporary.write_text(svg, encoding="utf-8")
        temporary.replace(output / name)
    print(f'Updated {len(assets)} assets using {len(data["days"])} real calendar days.')


if __name__ == "__main__":
    update(ROOT / "assets")
