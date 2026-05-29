# Neofetch Profile README Template

A fork-and-customize template for a dynamic neofetch-style GitHub profile README.

> **Status**: Milestone 2 of 4 — local renderer + automatic portrait→ASCII conversion work. GitHub Action + secrets (M3) and "Use this template" polish (M4) are coming.

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

Only three items. Everything else is generated.

| Item | What it controls |
|---|---|
| `config.yml` | Every neofetch field — user, host, OS, languages, hobbies, contact, etc. |
| `portrait.png` or `portrait.jpg` | **Optional**: Drop your portrait here. Automatically converts to ASCII art (replaces `ascii-art.txt`). |
| `ascii-art.txt` | **Fallback**: The ASCII art on the left side. Used only if no portrait image is present. |

## Auto ASCII portrait

Drop a portrait image in the repo root and the build system converts it to ASCII automatically:

1. **Save your portrait** as `portrait.png` or `portrait.jpg` in the repo root
2. **Run the build**: `python build.py`
3. **Done**: ASCII version embeds in both light/dark SVGs

**Image tips**:
- High contrast works best (bright face, dark background or vice versa)
- Square crop is ideal (tool resizes to 50×25 characters)
- Monospace displays ~50 chars wide

If no portrait is found, the build falls back to `ascii-art.txt` so you always have output.

## Birthday → Uptime counter

The `birthday` field in `config.yml` powers the "Uptime" line that shows your age in years/months/days. Leave it as `null` to hide that line entirely. Coming in Milestone 3: store the birthday as a repo secret instead of in the file.

## Tests

```bash
python3 -m pip install pytest
pytest test_build.py -v
```

## Roadmap

- [x] **M1** — Core renderer: `config.yml` → SVGs via `python build.py`
- [x] **M2** — Drop a `portrait.png` in the repo, get ASCII automatically
- [ ] **M3** — GitHub Action: daily refresh + optional `BIRTHDAY` repo secret
- [ ] **M4** — One-click "Use this template" with screenshots and walkthrough

---

Inspired by [Andrew6rant/Andrew6rant](https://github.com/Andrew6rant/Andrew6rant).
