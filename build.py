"""Generate neofetch-style profile README SVGs from config.yml.

Run `python build.py` from the repo root. Reads `config.yml` and `ascii-art.txt`,
writes `light_mode.svg` and `dark_mode.svg`. That's it.

Automatically converts portrait.png/jpg to ASCII if present in repo root.
Falls back to ascii-art.txt if no portrait found.
"""
from __future__ import annotations

import datetime
import html
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from dateutil import relativedelta

import image_to_ascii

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yml"
ASCII_PATH = ROOT / "ascii-art.txt"
OUT_LIGHT = ROOT / "light_mode.svg"
OUT_DARK = ROOT / "dark_mode.svg"

# GitHub-native color palettes (light + dark mode of the README viewer).
LIGHT_THEME = {
    "bg": "#f6f8fa",
    "fg": "#24292f",
    "key": "#953800",
    "value": "#0a3069",
    "cc": "#c2cfde",
    "add": "#1a7f37",
    "delete": "#cf222e",
}

DARK_THEME = {
    "bg": "#161b22",
    "fg": "#c9d1d9",
    "key": "#ffa657",
    "value": "#a5d6ff",
    "cc": "#616e7f",
    "add": "#3fb950",
    "delete": "#f85149",
}

# Layout constants — match the upstream guptaronav SVG geometry.
INFO_X = 390
INFO_Y0 = 30
LINE_HEIGHT = 20
ASCII_X = 15
TARGET_WIDTH = 58  # default visible-char width per line for dot alignment

DEFAULT_CONFIG: dict = {
    "user": "user",
    "host": "host",
    "birthday": None,
    "sections": [],
    "target_width": TARGET_WIDTH,
}


# ─── Config + helpers ─────────────────────────────────────────────────────────

def load_config(path: Path = CONFIG_PATH) -> dict:
    """Parse config.yml. Apply defaults for missing keys. Exit on error."""
    if not path.exists():
        print(f"Error: config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        print(f"Error parsing {path}: {e}", file=sys.stderr)
        sys.exit(1)
    return {**DEFAULT_CONFIG, **data}


def load_ascii(path: Path = ASCII_PATH) -> list[str]:
    """Load ASCII art lines. Single-line placeholder if file missing or empty."""
    if not path.exists():
        return ["(drop ascii-art.txt in the repo root)"]
    text = path.read_text().rstrip("\n")
    if not text:
        return ["(ascii-art.txt is empty)"]
    return text.split("\n")


def plural(n: int) -> str:
    """Return 's' unless n is exactly 1."""
    return "s" if n != 1 else ""


def resolve_birthday(config: dict) -> tuple[Optional[str], bool]:
    """Resolve birthday and whether to show the day component.

    Returns (birthday_str, show_days).

    Priority: config.birthday → BIRTHDAY env var → None.
    - Config path  → show_days=True  (full "X years, Y months, Z days")
    - Env-var path → show_days=False (only "X years, Y months"; days omitted
                     because env var is typically a repo secret and days can
                     narrow down a birth date too precisely)
    """
    config_bday = config.get("birthday") or None
    if config_bday:
        return config_bday, True
    env_bday = os.environ.get("BIRTHDAY") or None
    if env_bday:
        return env_bday, False
    return None, True


def daily_readme(birthday: Optional[str], show_days: bool = True) -> Optional[str]:
    """Format birthday (YYYY-MM-DD) into an age string.

    Returns 'X years, Y months, Z days' when show_days is True, or
    'X years, Y months' when show_days is False (secret / privacy path).
    Returns None if `birthday` is falsy so the Uptime line is omitted.
    """
    if not birthday:
        return None
    bd = datetime.datetime.strptime(birthday, "%Y-%m-%d")
    diff = relativedelta.relativedelta(datetime.datetime.today(), bd)
    age = (
        f"{diff.years} year{plural(diff.years)}, "
        f"{diff.months} month{plural(diff.months)}"
    )
    if show_days:
        age += f", {diff.days} day{plural(diff.days)}"
    return age


def parse_item(item_str: str) -> tuple[str, str]:
    """Split a 'Key: Value' config string into (key, value). Splits on first ':'.

    Lets values contain colons (e.g., URLs, times).
    """
    if ":" not in item_str:
        return item_str.strip(), ""
    key, _, value = item_str.partition(":")
    return key.strip(), value.strip()


# ─── Rendering ────────────────────────────────────────────────────────────────

def _dots(target_width: int, used: int) -> str:
    """Return ' .....' padding sized to reach `target_width` visible chars."""
    just_len = max(2, target_width - used)
    return " " + ("." * (just_len - 2)) + " "


def render_item_tspan(x: int, y: int, key: str, value: str,
                      target_width: int = TARGET_WIDTH) -> str:
    """Render '. Key: ........... Value' as SVG <tspan> markup.

    A dotted compound key like 'Languages.Programming' gets both halves styled
    as `.key` with a literal '.' divider, matching the upstream look.
    """
    value_esc = html.escape(value)

    if "." in key:
        head, tail = key.split(".", 1)
        key_markup = (
            f'<tspan class="key">{html.escape(head)}</tspan>'
            f'.<tspan class="key">{html.escape(tail)}</tspan>'
        )
        key_visible = f"{head}.{tail}"
    else:
        key_markup = f'<tspan class="key">{html.escape(key)}</tspan>'
        key_visible = key

    # Visible chars: ". " (2) + key + ": " (2) + dots + value
    used = 2 + len(key_visible) + 2 + len(value)
    dots = _dots(target_width, used)

    return (
        f'<tspan x="{x}" y="{y}" class="cc">. </tspan>'
        f'{key_markup}:'
        f'<tspan class="cc">{dots}</tspan>'
        f'<tspan class="value">{value_esc}</tspan>'
    )


def render_section_header(x: int, y: int, title: str) -> str:
    """Render a '- Title -——————————————' divider line."""
    return (
        f'<tspan x="{x}" y="{y}">- {html.escape(title)}</tspan>'
        ' -——————————————————————————————————————————————-—-'
    )


def _pick_ascii_metrics(ascii_count: int, info_rows: int) -> tuple[int, int]:
    """Choose ASCII font-size + line-height so it fits the same vertical span as info.

    Default to the upstream 16px/20px for short ASCII. For taller art, shrink
    so the last ASCII line lands near the last info line.
    """
    available = max(info_rows, 1) * LINE_HEIGHT  # pixels of vertical space info uses
    if ascii_count <= info_rows:
        return 16, LINE_HEIGHT  # plenty of room, native size
    lh = max(8, available // ascii_count)
    font = max(7, lh - 1)
    return font, lh


def render_svg(config: dict, ascii_lines: list[str], theme: dict,
               show_days: bool = True) -> str:
    """Render the full SVG XML string from config + ASCII + theme.

    show_days controls whether the Uptime line includes the day component.
    Pass False when birthday came from a repo secret (privacy path).
    """
    tw = int(config.get("target_width", TARGET_WIDTH))
    info_tspans: list[str] = []
    y = INFO_Y0

    # Header line: "user@host -—————"
    user = html.escape(str(config.get("user", "user")))
    host = html.escape(str(config.get("host", "host")))
    info_tspans.append(
        f'<tspan x="{INFO_X}" y="{y}">{user}@{host}</tspan>'
        ' -———————————————————————————————————————————-—-'
    )
    y += LINE_HEIGHT

    # Optional Uptime line (only if birthday set)
    age = daily_readme(config.get("birthday"), show_days=show_days)
    if age:
        info_tspans.append(render_item_tspan(INFO_X, y, "Uptime", age, target_width=tw))
        y += LINE_HEIGHT

    # Sections
    sections = config.get("sections") or []
    for i, section in enumerate(sections):
        title = (section.get("title") or "").strip()
        items = section.get("items") or []

        if title:
            # blank line before titled section (unless first content after header)
            if i > 0 or age:
                y += LINE_HEIGHT
            info_tspans.append(render_section_header(INFO_X, y, title))
            y += LINE_HEIGHT
        elif i > 0:
            # Untitled section after another → just a blank gap
            y += LINE_HEIGHT

        for item_str in items:
            key, value = parse_item(str(item_str))
            info_tspans.append(render_item_tspan(INFO_X, y, key, value, target_width=tw))
            y += LINE_HEIGHT

    info_last_y = y - LINE_HEIGHT
    info_rows = (info_last_y - INFO_Y0) // LINE_HEIGHT + 1
    svg_height = max(440, info_last_y + 30)

    # ASCII: scale to fit the same vertical span as info
    ascii_font, ascii_lh = _pick_ascii_metrics(len(ascii_lines), info_rows)
    ascii_tspans = [
        f'<tspan x="{ASCII_X}" y="{INFO_Y0 + i * ascii_lh}">{html.escape(line)}</tspan>'
        for i, line in enumerate(ascii_lines)
    ]

    info_block = "\n".join(info_tspans)
    ascii_block = "\n".join(ascii_tspans)

    return (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ConsolasFallback,Consolas,monospace" '
        f'width="985px" height="{svg_height}px" font-size="16px">\n'
        "<style>\n"
        "@font-face {\n"
        "src: local('Consolas'), local('Consolas Bold');\n"
        "font-family: 'ConsolasFallback';\n"
        "font-display: swap;\n"
        "-webkit-size-adjust: 109%;\n"
        "size-adjust: 109%;\n"
        "}\n"
        f'.key {{fill: {theme["key"]};}}\n'
        f'.value {{fill: {theme["value"]};}}\n'
        f'.addColor {{fill: {theme["add"]};}}\n'
        f'.delColor {{fill: {theme["delete"]};}}\n'
        f'.cc {{fill: {theme["cc"]};}}\n'
        "text, tspan {white-space: pre;}\n"
        "</style>\n"
        f'<rect width="985px" height="{svg_height}px" fill="{theme["bg"]}" rx="15"/>\n'
        f'<text x="{ASCII_X}" y="{INFO_Y0}" fill="{theme["fg"]}" '
        f'font-size="{ascii_font}px" class="ascii">\n'
        f"{ascii_block}\n"
        "</text>\n"
        f'<text x="{INFO_X}" y="{INFO_Y0}" fill="{theme["fg"]}">\n'
        f"{info_block}\n"
        "</text>\n"
        "</svg>\n"
    )


# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    config = load_config()

    # Birthday: config.yml wins; env var (repo secret) is the fallback.
    # show_days=False when using the secret path — days omitted for privacy.
    birthday, show_days = resolve_birthday(config)
    config = {**config, "birthday": birthday}

    # Try portrait first, fall back to ascii-art.txt
    portrait_path = image_to_ascii.detect_portrait()
    ascii_lines = image_to_ascii.convert_with_fallback(portrait_path, ASCII_PATH)

    light = render_svg(config, ascii_lines, LIGHT_THEME, show_days=show_days)
    dark = render_svg(config, ascii_lines, DARK_THEME, show_days=show_days)

    OUT_LIGHT.write_text(light)
    OUT_DARK.write_text(dark)
    print(f"Wrote {OUT_LIGHT.name} and {OUT_DARK.name}")


if __name__ == "__main__":
    main()
