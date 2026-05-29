# Neofetch Profile README Template

A fork-and-customize template for a dynamic neofetch-style GitHub profile README.

> **Status**: Milestone 1 of 4 — local renderer works. Image→ASCII conversion (M2), GitHub Action + secrets (M3), and "Use this template" polish (M4) are coming.

## Quick start (local)

```bash
git clone https://github.com/YOUR_USERNAME/neofetch-readme-template
cd neofetch-readme-template
python3 -m pip install -r requirements.txt
# edit config.yml with your info, optionally replace ascii-art.txt
python3 build.py
```

You'll get two files: `light_mode.svg` and `dark_mode.svg`. Open them to preview.

## What you edit

Only two files. Everything else is generated.

| File | What it controls |
|---|---|
| `config.yml` | Every neofetch field — user, host, OS, languages, hobbies, contact, etc. |
| `ascii-art.txt` | The ASCII art on the left side. Drop in any monospace ASCII (~40×20 chars fits best). |

## Birthday → Uptime counter

The `birthday` field in `config.yml` powers the "Uptime" line that shows your age in years/months/days. Leave it as `null` to hide that line entirely. Coming in Milestone 3: store the birthday as a repo secret instead of in the file.

## Tests

```bash
python3 -m pip install pytest
pytest test_build.py -v
```

## Roadmap

- [x] **M1** — Core renderer: `config.yml` → SVGs via `python build.py`
- [ ] **M2** — Drop a `portrait.png` in the repo, get ASCII automatically
- [ ] **M3** — GitHub Action: daily refresh + optional `BIRTHDAY` repo secret
- [ ] **M4** — One-click "Use this template" with screenshots and walkthrough

---

Inspired by [Andrew6rant/Andrew6rant](https://github.com/Andrew6rant/Andrew6rant).
