# Plan: Neofetch Profile README Template — Core Renderer

**Source PRD**: `.claude/prds/neofetch-readme-template.prd.md`
**Selected Milestone**: 1 — Core renderer (config.yml + local script → working light/dark SVGs)
**Complexity**: Medium

## Summary
Build the local-only foundation of the template repo: a single `build.py` script that reads `config.yml` (all neofetch fields), reads `ascii-art.txt` (placeholder for now — image conversion arrives in Milestone 2), and emits valid `light_mode.svg` + `dark_mode.svg`. No GitHub Action yet, no secrets yet, no image-to-ASCII yet. Goal: a stranger who clones the repo can `pip install -r requirements.txt`, edit `config.yml`, run `python build.py`, and see two working SVGs.

## Patterns to Mirror
| Category | Source | Pattern |
|---|---|---|
| Renderer shape | `/Users/ronav/Desktop/guptaronav/today.py:48-58` | Single `svg_overwrite` flow: parse → mutate → write |
| Birthday → age string | `/Users/ronav/Desktop/guptaronav/today.py:10-20` | `relativedelta` + plural helper; returns `"X years, Y months, Z days"` |
| Dot-padding alignment | `/Users/ronav/Desktop/guptaronav/today.py:35-46` | `justify_format(root, id, text, length)` calculates dots to right-justify value at a target column |
| SVG colors | `/Users/ronav/Desktop/guptaronav/light_mode.svg:11-15` and `dark_mode.svg:11-15` | Light: `#953800/#0a3069/#c2cfde` on `#f6f8fa`. Dark: `#ffa657/#a5d6ff/#616e7f` on `#161b22` |
| Status output | `/Users/ronav/Desktop/guptaronav/today.py:52` | Single `print(f"Updated X to: {value}")` line at exit |
| Naming | `today.py`, `light_mode.svg`, `dark_mode.svg` | snake_case files at repo root; no `src/` directory |

No existing project skeleton at `/Users/ronav/Desktop/neofetch-readme-template/`. All files in this plan are CREATE.

## Files to Change
| File | Action | Why |
|---|---|---|
| `build.py` | CREATE | Main renderer: read config, read ASCII, write both SVGs |
| `config.yml` | CREATE | Single source of truth for all neofetch fields — the only file most users edit |
| `ascii-art.txt` | CREATE | Placeholder ASCII art shipped with the repo (replaced in M2 by image-converter output) |
| `requirements.txt` | CREATE | `pyyaml`, `python-dateutil` (no `lxml` needed since we render SVG as strings, not parse them) |
| `README.md` | CREATE | Bare-minimum setup steps (gets a polish pass in M4) |
| `.gitignore` | CREATE | Standard Python ignores (`__pycache__`, `.venv`, `.env`, `.DS_Store`) |
| `test_build.py` | CREATE | pytest smoke tests: build runs on default config, produces valid SVGs, age math is correct |

## Config Schema (the design decision that drives everything else)

```yaml
# Header line at top of the neofetch box: "user@host"
user: yourusername
host: yourhost

# Optional. Format: YYYY-MM-DD. If null/missing, the Uptime line is omitted.
# In Milestone 3 this gets overridden by a BIRTHDAY repo secret.
birthday: null

# Sections render top-to-bottom in the order listed.
# A section with empty `title` renders its items inline (no "- Title -" header).
# A section with a non-empty `title` renders a divider header above its items.
# Items render as ". Key: ............... Value"
sections:
  - title: ""
    items:
      - { key: "OS",     value: "macOS" }
      - { key: "Host",   value: "Your Org" }
      - { key: "Kernel", value: "Engineer" }
      - { key: "IDE",    value: "VS Code" }
      - { key: "Shell",  value: "zsh" }

  - title: ""
    items:
      - { key: "Languages.Programming", value: "Python, TypeScript" }
      - { key: "Languages.Computer",    value: "HTML, CSS, JSON, YAML" }
      - { key: "Languages.Real",        value: "English" }

  - title: "Contact"
    items:
      - { key: "Email",   value: "you@example.com" }
      - { key: "Discord", value: "username" }
      - { key: "Website", value: "example.com" }
```

**Why this shape:**
- Flat list of sections solves the "additional sections" open question from the PRD without inventing a custom mini-language.
- Each item is `{key, value}` only — no per-item color/width overrides in v1 (YAGNI).
- `title: ""` lets users group items without a visible header, matching how guptaronav's top block has OS/Host/Kernel/IDE/Shell with no header.
- Dot-notation keys (`Languages.Programming`) are rendered with the dot styled as the divider, matching upstream.

## Tasks

### Task 1: Project skeleton
- **Action**: Create `requirements.txt` (`pyyaml`, `python-dateutil`), `.gitignore` (Python defaults), bare `README.md` with "edit config.yml, run python build.py" instructions, and an empty `config.yml` and `ascii-art.txt` so the repo is git-init-ready.
- **Mirror**: `guptaronav/.gitignore` and `guptaronav/cache/requirements.txt`
- **Validate**: `ls` shows all 6 files; `git init && git add . && git status` shows clean state.

### Task 2: Config loader with defaults
- **Action**: In `build.py`, add `load_config()` that reads `config.yml`, applies sensible defaults for missing keys (`user="user"`, `host="host"`, `birthday=None`, `sections=[]`), and exits with a clear error if YAML is malformed.
- **Mirror**: `today.py`'s simple imperative style — no classes, no Click, no argparse for now.
- **Validate**: `python -c "from build import load_config; print(load_config())"` returns a dict; missing-file case exits cleanly with non-zero status and a readable message.

### Task 3: Birthday → Uptime helper
- **Action**: Port `daily_readme()` and `plural()` verbatim from `guptaronav/today.py:10-20`, changing only the input from `datetime.datetime` object to a YYYY-MM-DD string. Return `None` if input is `None` (no Uptime line should render).
- **Mirror**: `guptaronav/today.py:10-24`
- **Validate**: Add unit test `test_uptime_format`: `daily_readme("2011-08-26")` returns a string matching `r"\d+ years?, \d+ months?, \d+ days?"`; `daily_readme(None)` returns `None`.

### Task 4: Dot-padding line builder
- **Action**: Write `format_line(key, value, target_width=58)`: returns the rendered string `". {key}: ........... {value}"` with dot count chosen so that the line is roughly `target_width` characters wide. Handle `key` containing dots (e.g., `Languages.Programming`) by rendering the dot literally; the SVG `<tspan>` styling treats both halves as `.key` class.
- **Mirror**: `guptaronav/today.py:35-46` `justify_format` logic, but simplified — we're building text strings, not mutating an existing SVG element.
- **Validate**: Unit test `test_format_line_alignment`: outputs for `("OS", "macOS")` and `("OS", "macOS, iOS, Windows 11")` should both render to lines of the same `target_width`.

### Task 5: SVG renderer
- **Action**: Write `render_svg(config, ascii_lines, theme: dict)` returning an SVG XML string. Responsibilities:
  - Compute info section y-positions: start at y=30, +20 per item, +20 for blank separator between unrelated sections, +20 before each non-empty title.
  - Compute ASCII font size: if the ASCII art has more lines than the info section has y-rows, scale ASCII line-height down to fit (mirror what we did manually for guptaronav's 28-line portrait at 14px line-height).
  - Generate `<tspan>` for each ASCII line and each info line, HTML-escaping `<`, `>`, `&`.
  - Wrap in the SVG header (font-family, style block, background rect) using the supplied `theme` dict for colors.
- **Mirror**: The structure of `guptaronav/light_mode.svg` lines 1-18 (header + style + rect) and 19-45 (ASCII text element) and 46+ (info text element).
- **Validate**: Smoke test `test_render_produces_valid_xml`: parses the output with `xml.etree.ElementTree` and asserts root tag is `{http://www.w3.org/2000/svg}svg`.

### Task 6: Theme definitions
- **Action**: Define two constants `LIGHT_THEME` and `DARK_THEME` at the top of `build.py` as dicts with keys: `bg`, `fg`, `key`, `value`, `cc`, `add`, `delete`. Values taken directly from `guptaronav/light_mode.svg:11-18` and `dark_mode.svg:11-18`.
- **Mirror**: Existing color scheme.
- **Validate**: Visual diff — running `python build.py` with a config equivalent to guptaronav's should produce SVGs visually identical to the current ones.

### Task 7: `main()` and CLI
- **Action**: Add `main()` that runs `load_config()`, reads `ascii-art.txt` (if present; else use a single-line placeholder), calls `render_svg` twice (light + dark), writes outputs, prints `Wrote light_mode.svg and dark_mode.svg`. Wire `if __name__ == "__main__": main()`.
- **Mirror**: `guptaronav/today.py:54-58`
- **Validate**: `python build.py` from a clean clone exits 0 and creates two SVG files.

### Task 8: Default config + placeholder ASCII
- **Action**: Pre-fill `config.yml` with a complete working example (similar fields to guptaronav but with placeholder values like `yourname@yourhost`, `Your Org`, `you@example.com`). Pre-fill `ascii-art.txt` with the simple flame design we used early in guptaronav (so the template works out of the box before the user does anything).
- **Mirror**: Field shapes from `guptaronav/light_mode.svg:46-65`
- **Validate**: `git clone` → `pip install -r requirements.txt` → `python build.py` produces valid SVGs without any editing.

### Task 9: Smoke + unit tests
- **Action**: `test_build.py` with pytest covering: (1) `load_config()` defaults, (2) `daily_readme()` formatting and `None` handling, (3) `format_line()` width consistency, (4) `render_svg()` produces parseable XML, (5) end-to-end: `main()` writes both output files.
- **Mirror**: No existing test patterns in guptaronav; using pytest conventions from `~/.claude/rules/ecc/python/testing.md`.
- **Validate**: `pytest test_build.py -v` → 5+ tests, all pass.

## Validation
```bash
cd /Users/ronav/Desktop/neofetch-readme-template

# Install
python3 -m pip install -r requirements.txt

# Default run produces working output
python3 build.py
# Expected: "Wrote light_mode.svg and dark_mode.svg"

# Verify SVGs are valid XML
python3 -c "import xml.etree.ElementTree as ET; ET.parse('light_mode.svg'); ET.parse('dark_mode.svg'); print('OK')"

# Tests pass
pytest test_build.py -v

# Visual sanity: open SVGs in Preview/browser
open light_mode.svg dark_mode.svg
```

## Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
| Dot-padding alignment looks ragged across varying value lengths | Medium | Use a fixed `target_width` (58 chars worked for guptaronav); unit-test that all rendered lines hit the same width |
| ASCII art wider than the configured x-offset overlaps info text | Medium | Compute info `x` dynamically as `max(ascii_width_px) + 20`, falling back to 390 if no ASCII present |
| YAML parsing surprises (missing keys, weird types) crash with a stack trace, not a readable error | Medium | Wrap `yaml.safe_load` in try/except; on `YAMLError` print `Error in config.yml at line N: ...` and exit 1 |
| Generated SVG renders fine in browser preview but wrong on GitHub | Low | Mirror upstream exactly — same `<style>` block, same `font-family`, same attribute order |
| Tests assume system fonts that aren't on CI | Low | Tests check XML structure only, not rendered geometry |

## Acceptance
- [ ] All 9 tasks complete
- [ ] `python build.py` on a fresh clone produces two valid SVGs without any editing
- [ ] `pytest test_build.py -v` passes 5+ tests
- [ ] Edited `config.yml` (change `user`, add a section, change a value) regenerates SVGs visibly reflecting the change
- [ ] No file outside `config.yml` and `ascii-art.txt` requires editing for v1 customization
- [ ] Patterns mirrored from `guptaronav/today.py` — no novel renderer architecture invented
