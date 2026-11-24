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
BG = "#17142d"
PANEL = "#28233d"
LAVENDER = "#c9bdff"
VIOLET = "#8f7bd1"
WHITE = "#fbf8ff"
MUTED = "#c1b9dc"
GOLD = "#e8cf77"
BORDER = "#554a78"


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
<style>text{{font-family:Inter,Segoe UI,Arial,"Hiragino Sans","Yu Gothic",Meiryo,"Noto Sans CJK JP",sans-serif}}.mono{{font-family:SFMono-Regular,Consolas,"Hiragino Sans","Yu Gothic",Meiryo,"Noto Sans CJK JP",monospace}}@media(prefers-reduced-motion:reduce){{.motion{{display:none}}}}</style>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="8" fill="{BG}" stroke="{BORDER}"/>
{body}</svg>'''


def render_stats(summary: dict, days: list[dict]) -> str:
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    body = text(34, 40, "活動の概要", 14, LAVENDER, 'class="mono" letter-spacing="2"')
    for i, (value, label) in enumerate([
        (summary["projects"], "公開プロジェクト"), (total, "コントリビューション数"),
        (active, "活動日数"), (summary["stars"], "プロジェクトのスター数"),
    ]):
        x = 34 + i * 225
        body += f'<rect x="{x}" y="66" width="208" height="118" rx="4" fill="{PANEL}" stroke="{BORDER}"/>'
        body += f'<rect x="{x+20}" y="81" width="7" height="7" fill="{LAVENDER}"/>'
        body += text(x + 20, 120, value, 38, WHITE, 'font-weight="700"')
        body += text(x + 20, 153, label, 11, MUTED, 'class="mono" letter-spacing="1"')
    language_text = "  /  ".join(sorted(summary["languages"])) or "集計対象の言語なし"
    body += text(34, 218, "リポジトリの主要言語　" + language_text, 14, MUTED)
    period = f'{days[0]["date"]} — {days[-1]["date"]}' if days else "活動データなし"
    body += text(34, 249, period + "  ·  フォークを除く公開プロジェクトを集計", 11, MUTED, 'class="mono"')
    return frame(960, 274, "GitHubの活動の概要", body)


def render_city(days: list[dict]) -> str:
    body = text(34, 42, "コントリビューションの街", 18, WHITE, 'font-weight="700" letter-spacing="2"')
    body += text(34, 68, "日々の活動が、街を育てる。", 14, MUTED)
    # Each real date becomes one building, with height proportional to log(count + 1).
    count_weeks = max((d["week"] for d in days), default=52) + 1
    dx = min(14, 742 / max(1, count_weeks))
    for day in sorted(days, key=lambda d: (d["week"] + d["weekday"], d["week"])):
        x = 125 + day["week"] * dx - day["weekday"] * 12
        y = 128 + day["week"] * 2.5 + day["weekday"] * 12
        h = 2 if day["count"] == 0 else 9 + math.log2(day["count"] + 1) * 12
        if day["count"] >= 8:
            front, side, top = "#b39a6c", "#796583", GOLD
        elif day["count"]:
            front, side, top = "#7665a8", "#524478", LAVENDER
        else:
            front, side, top = "#302b47", "#242039", "#40365e"
        points = [(x, y-h), (x+dx-2, y+2.5-h), (x+dx-14, y+12-h), (x-12, y+9.5-h)]
        p = " ".join(f"{a:.1f},{b:.1f}" for a, b in points)
        label = html.escape(f'{day["date"]}　{day["count"]}件')
        body += f'<g class="building"><title>{label}</title>'
        body += f'<path d="M{x-12},{y+9.5-h} L{x+dx-14},{y+12-h} V{y+12} L{x-12},{y+9.5}Z" fill="{front}"/>'
        body += f'<path d="M{x+dx-14},{y+12-h} L{x+dx-2},{y+2.5-h} V{y+2.5} L{x+dx-14},{y+12}Z" fill="{side}"/>'
        body += f'<polygon points="{p}" fill="{top}" stroke="{BG}" stroke-width="0.6"/></g>'
    body += f'<path d="M34 362H926" stroke="{BORDER}"/>'
    body += text(34, 397, f'{sum(d["count"] for d in days)}件（過去1年間）', 14, LAVENDER, 'class="mono"')
    body += text(650, 397, "建物1棟が1日分", 12, MUTED, 'class="mono" letter-spacing="1"')
    return frame(960, 428, "GitHubの活動を建物の高さで表した街", body)


def render_grid(days: list[dict]) -> str:
    body = text(34, 40, "活動ヒートマップ", 14, LAVENDER, 'class="mono" letter-spacing="2"')
    colors = ["#302b47", "#5c4d83", VIOLET, LAVENDER, GOLD]
    for day in days:
        level = min(4, math.ceil(math.log2(day["count"] + 1)))
        x, y = 36 + day["week"] * 16.6, 65 + day["weekday"] * 17
        body += f'<rect x="{x:.1f}" y="{y}" width="12.5" height="12.5" rx="1" fill="{colors[level]}"><title>{day["date"]}　{day["count"]}件</title></rect>'
    body += '<g class="motion"><rect x="36" y="62" width="2" height="120" fill="#e2cfff" opacity="0.7"><animate attributeName="x" values="36;918;36" dur="14s" repeatCount="indefinite"/></rect></g>'
    body += text(34, 218, "色が明るいほど、その日のコントリビューション数が多くなります。", 11, MUTED, 'class="mono" letter-spacing="1"')
    return frame(960, 242, "走査線が動くGitHubの活動ヒートマップ", body)


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
    update(ROOT / "assets" / "purple")
