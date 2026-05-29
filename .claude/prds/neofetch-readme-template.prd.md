# Neofetch Profile README Template

## Problem
Building a dynamic neofetch-style GitHub profile README is currently a steep climb. Andrew6rant's reference implementation bundles ~350 lines of Python, GraphQL queries, custom SVG dot-padding math, and hand-crafted ASCII art that most people can't reproduce. Existing profile-README generators (gh-profile-readme-generator, profileme.dev, readme.so) don't produce the neofetch aesthetic at all. The cost of leaving this unsolved: a distinctive look that's effectively locked to one user's repo, and anyone wanting the same style has to wade through Andrew6rant's GraphQL plumbing.

## Evidence
- Assumption — needs validation via real-world fork count and friend feedback after release.
- Personal experience: porting Andrew6rant's setup into `guptaronav/guptaronav` took multiple iterations of font-sizing, SVG dot-counting alignment, and ASCII art generation. Setup was non-trivial even with Claude assisting.

## Users
- **Primary**: Both developers wanting a fast profile README without forking 350 lines of someone else's GraphQL plumbing, *and* casual GitHub users (students, designers) who like the look but find secrets/Python/SVG intimidating.
- **Not for**: Users who want hand-tuned custom ASCII portraits, or users who need their README to display live GitHub commit/star/LoC stats.

## Hypothesis
We believe **a fork-and-customize template repo with a single YAML config, automatic image-to-ASCII conversion, and an optional birthday secret** will **give users a working neofetch-style profile README in under 10 minutes** for **both developers and casual GitHub users**.
We'll know we're right when **first-time setup completes without needing to open any source file beyond `config.yml` and the setup README** (qualitative signal: friends-asking-how-you-made-yours messages stop arriving).

## Success Metrics
| Metric | Target | How measured |
|---|---|---|
| Time to first successful render (fork → push → live README) | < 10 min | Self-test on a fresh GitHub account |
| Files a new user must edit | ≤ 2 (config.yml + portrait image) | Manual count |
| Source files a new user must read to set up | 0 | All customization through config + image drop + README |
| Organic forks within 3 months (signal, not gate) | ≥ 10 | GitHub fork count |

## Scope
**MVP**
- "Use this template" GitHub button enabled on the repo
- `config.yml` exposing every neofetch field: header (`user@host`), OS, Host, Kernel, IDE, Shell, Languages.Programming, Languages.Computer, Languages.Real, Hobbies.Software, Hobbies.Hardware, Email (personal + work), Discord, Website, plus a flexible "additional sections" list
- Image → ASCII pipeline: user commits `portrait.png` or `portrait.jpg`, GitHub Action converts it on push and embeds it in both light/dark SVGs
- Birthday: **optional**. If `BIRTHDAY` repo secret is present (format `YYYY-MM-DD`), Uptime line is rendered and refreshed daily. If absent, Uptime line is omitted entirely.
- Setup README with: "Use this template" link, ≤ 5 step instructions, screenshots of expected result
- Light + dark mode SVGs auto-generated from config

**Out of scope** (for v1)
- Web UI or installer — adds maintenance burden; fork+edit covers the use case
- Theme/color customization beyond the two GitHub-native themes
- Live GitHub stats (commits, stars, LoC) — explicitly removed in upstream guptaronav; complexity isn't worth it
- Multiple ASCII art styles / picker — one converter, take it or leave it
- README i18n
- Automatic config validation UI

## Delivery Milestones
<!-- Business outcomes, not engineering tasks. /plan turns each into a plan. -->
<!-- Status: pending | in-progress | complete -->

| # | Milestone | Outcome | Status | Plan |
|---|---|---|---|---|
| 1 | Core renderer | A user can edit config.yml, run a single local script, and produce working light/dark SVGs (no Action yet) | complete | `.claude/plans/neofetch-readme-template.plan.md` |
| 2 | Image → ASCII pipeline | User drops `portrait.png`, gets ASCII embedded in SVGs automatically | complete | `.claude/plans/neofetch-readme-template.plan.md` |
| 3 | GitHub Action + optional secrets | Push to main triggers full regen; daily cron refreshes Uptime when BIRTHDAY secret is set | in-progress | `.claude/plans/neofetch-readme-template.plan.md` |
| 4 | Template-repo polish | "Use this template" works end-to-end; README guides a stranger from zero to live profile in <10 min with screenshots | pending | — |

## Open Questions
- [ ] Which ASCII conversion library produces the best portrait output? (`ascii-magic`, `image-to-ascii`, `Pillow` + custom) — needs a small spike comparing outputs on real photos
- [ ] How is the "additional sections" list represented in `config.yml`? Flat list of `{header, items}` vs. nested schema
- [ ] Should the Action commit generated SVGs back to the repo (current guptaronav behavior) or render on the fly via a CDN proxy?
- [ ] Final repo name — `neofetch-readme-template`? `profile-neofetch`? `readme-neofetch`?

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Auto ASCII converter produces ugly output for arbitrary user photos | High | Setup feels "broken" on first try | Document image requirements (high contrast, simple subject, square crop); ship a known-good test image to confirm pipeline works |
| Config schema becomes inflexible as users want unsupported sections | Medium | Forks diverge from template | Support "extra sections" list in config from v1 |
| GitHub Actions permissions / secrets confuse non-dev users | Medium | Abandonment at setup step | Walk through with screenshots; default no-secret path means setup works without touching Settings → Secrets |
| Andrew6rant updates upstream with similar features | Low | Project becomes redundant | Acceptable — this is "I built it, why not share it," not a competitive product |

---
*Status: DRAFT — requirements only. Implementation planning pending via /plan.*
