# Profile maintenance

## Design

Midnight purple `#100a1d`, electric violet `#9b6dff`, soft lavender `#c4a2ff`.
The header, footer, project cards, city, statistics and heatmap are original SVG artwork.
The section structure was inspired by [uzuchan](https://github.com/uzuchan).
Technology icons are served by [Skill Icons](https://github.com/tandpfun/skill-icons).

## Editing

- Bio and project descriptions: `README.md`
- Banner: `assets/header.svg`
- Project cards: `assets/project-*.svg`
- Stats, city and heatmap: `scripts/update_profile.py`

The biography and stack were based on the public READMEs of Re-Decide,
devlab-board and mcp-pr-review. They describe areas being used/explored,
not proficiency levels or employment history.

## Updates

GitHub Actions runs daily at 06:23 JST (scheduling can be delayed by GitHub).
To update immediately, open Actions → Refresh profile visuals → Run workflow.
The workflow uses the repository's temporary `GITHUB_TOKEN`; no personal token is needed.

The generator reads public owned repositories using the REST API, and the
last year's aggregate contribution calendar using GraphQL. No private repository
names, descriptions, issues or source code are requested or published.
GitHub's own contribution counting rules apply; these are not raw commit counts.

Repository metrics exclude forks and this profile repository. "Primary repository
languages" means GitHub's primary language per public project, not language
proficiency or percentage of code. The Blade classification of the review project
comes from its Laravel sample application.

City heights use `9 + 12 * log2(contributions + 1)` for active days; empty days are
low tiles. The scan line in the heatmap is decorative and does not alter counts.

If API access fails, generation stops before replacing the existing assets.
No external stats-card service is needed. Animated decoration is hidden when
the image renderer respects `prefers-reduced-motion`.

## Local validation

Requires Python 3.11+ and an authenticated GitHub CLI (`gh`).

```sh
python3 -m unittest discover -s tests -v
python3 scripts/update_profile.py
```
