"""Tests for build.py and image_to_ascii.py."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import build
import image_to_ascii


# ─── load_config ─────────────────────────────────────────────────────────────

def test_load_config_applies_defaults(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yml"
    cfg_file.write_text("user: alice\n")

    cfg = build.load_config(cfg_file)

    assert cfg["user"] == "alice"
    assert cfg["host"] == "host"  # default
    assert cfg["birthday"] is None
    assert cfg["sections"] == []


def test_load_config_missing_file_exits_with_message(tmp_path: Path,
                                                     capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit) as exc:
        build.load_config(tmp_path / "nonexistent.yml")
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "config file not found" in err.lower()


def test_load_config_malformed_yaml_exits(tmp_path: Path,
                                          capsys: pytest.CaptureFixture) -> None:
    bad = tmp_path / "config.yml"
    bad.write_text("user: alice\n  bad: indent\n: missing key\n")
    with pytest.raises(SystemExit) as exc:
        build.load_config(bad)
    assert exc.value.code == 1
    assert "error parsing" in capsys.readouterr().err.lower()


# ─── plural + daily_readme ───────────────────────────────────────────────────

def test_plural() -> None:
    assert build.plural(0) == "s"
    assert build.plural(1) == ""
    assert build.plural(2) == "s"


def test_daily_readme_formats_age() -> None:
    age = build.daily_readme("2000-01-01")
    assert age is not None
    # Days are always omitted — birthday comes from a secret
    assert re.match(r"^\d+ years?, \d+ months?$", age)
    assert "day" not in age


def test_daily_readme_none_returns_none() -> None:
    assert build.daily_readme(None) is None
    assert build.daily_readme("") is None


# ─── resolve_birthday ────────────────────────────────────────────────────────

def test_resolve_birthday_reads_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIRTHDAY", "1995-03-20")
    assert build.resolve_birthday() == "1995-03-20"


def test_resolve_birthday_returns_none_when_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BIRTHDAY", raising=False)
    assert build.resolve_birthday() is None


def test_resolve_birthday_ignores_config_file_value(monkeypatch: pytest.MonkeyPatch) -> None:
    # Even if someone puts a date in config.yml, only the secret is used.
    monkeypatch.delenv("BIRTHDAY", raising=False)
    # resolve_birthday() takes no args — config is not consulted
    assert build.resolve_birthday() is None


# ─── render_svg uptime ───────────────────────────────────────────────────────

def test_render_svg_uptime_never_shows_days() -> None:
    svg = build.render_svg(_make_cfg(birthday="2000-01-01"), ["x"], build.LIGHT_THEME)
    assert "Uptime" in svg
    assert "day" not in svg  # days always omitted for privacy


def test_render_svg_uptime_absent_when_no_birthday() -> None:
    svg = build.render_svg(_make_cfg(birthday=None), ["x"], build.LIGHT_THEME)
    assert "Uptime" not in svg


# ─── parse_item + dot padding ────────────────────────────────────────────────

def test_parse_item_splits_on_first_colon() -> None:
    assert build.parse_item("OS: macOS") == ("OS", "macOS")
    assert build.parse_item("Website: https://example.com") == (
        "Website", "https://example.com")


def test_parse_item_without_colon() -> None:
    assert build.parse_item("just text") == ("just text", "")


def test_dots_pads_to_target_width() -> None:
    # short value → more dots
    short = build._dots(target_width=30, used=10)
    long = build._dots(target_width=30, used=20)
    assert len(short) > len(long)
    # both wrapped in single spaces, dots between
    assert short.startswith(" ") and short.endswith(" ")


# ─── render_item_tspan ───────────────────────────────────────────────────────

def test_render_item_tspan_contains_key_and_value() -> None:
    out = build.render_item_tspan(390, 50, "OS", "macOS")
    assert ">OS<" in out
    assert ">macOS<" in out
    assert 'class="key"' in out
    assert 'class="value"' in out


def test_render_item_tspan_handles_compound_key() -> None:
    out = build.render_item_tspan(390, 50, "Languages.Programming", "Python")
    assert "Languages" in out
    assert "Programming" in out
    assert out.count('class="key"') == 2  # both halves styled


def test_render_item_tspan_escapes_html() -> None:
    out = build.render_item_tspan(390, 50, "Stack", "<script>alert(1)</script>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


# ─── render_svg end-to-end ───────────────────────────────────────────────────

def _make_cfg(**overrides: object) -> dict:
    base = {
        "user": "alice",
        "host": "host",
        "birthday": None,
        "sections": [
            {"title": "", "items": ["OS: macOS"]},
        ],
    }
    base.update(overrides)
    return base


def test_render_svg_is_valid_xml() -> None:
    svg = build.render_svg(_make_cfg(), ["x"], build.LIGHT_THEME)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")


def test_render_svg_includes_uptime_when_birthday_set() -> None:
    svg = build.render_svg(_make_cfg(birthday="2000-01-01"), ["x"], build.LIGHT_THEME)
    assert "Uptime" in svg


def test_render_svg_includes_section_titles() -> None:
    cfg = _make_cfg(sections=[
        {"title": "Contact", "items": ["Email: a@b.com"]},
    ])
    svg = build.render_svg(cfg, ["x"], build.LIGHT_THEME)
    assert "- Contact" in svg


def test_render_svg_themes_differ() -> None:
    cfg = _make_cfg()
    light = build.render_svg(cfg, ["x"], build.LIGHT_THEME)
    dark = build.render_svg(cfg, ["x"], build.DARK_THEME)
    assert build.LIGHT_THEME["bg"] in light
    assert build.DARK_THEME["bg"] in dark
    assert light != dark


# ─── main() end-to-end ───────────────────────────────────────────────────────

def test_main_writes_both_svgs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = tmp_path / "config.yml"
    cfg.write_text("user: alice\nhost: host\nsections:\n"
                   "  - title: ''\n    items:\n      - 'OS: macOS'\n")
    ascii_f = tmp_path / "ascii-art.txt"
    ascii_f.write_text("xxx\n")
    light = tmp_path / "light_mode.svg"
    dark = tmp_path / "dark_mode.svg"

    monkeypatch.setattr(build, "CONFIG_PATH", cfg)
    monkeypatch.setattr(build, "ASCII_PATH", ascii_f)
    monkeypatch.setattr(build, "OUT_LIGHT", light)
    monkeypatch.setattr(build, "OUT_DARK", dark)

    build.main()

    assert light.exists() and dark.exists()
    # Both must parse as valid XML
    ET.parse(light)
    ET.parse(dark)


# ─── image_to_ascii: portrait detection ──────────────────────────────────────

def test_detect_portrait_finds_png(tmp_path: Path,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
    # Create a test portrait.png
    portrait = tmp_path / "portrait.png"
    portrait.write_bytes(b"fake png data")

    monkeypatch.setattr(image_to_ascii, "ROOT", tmp_path)

    result = image_to_ascii.detect_portrait()

    assert result == portrait


def test_detect_portrait_finds_jpg(tmp_path: Path,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
    # Create a test portrait.jpg
    portrait = tmp_path / "portrait.jpg"
    portrait.write_bytes(b"fake jpg data")

    monkeypatch.setattr(image_to_ascii, "ROOT", tmp_path)

    result = image_to_ascii.detect_portrait()

    assert result == portrait


def test_detect_portrait_missing_returns_none(tmp_path: Path,
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    # Empty directory, no portrait files

    monkeypatch.setattr(image_to_ascii, "ROOT", tmp_path)

    result = image_to_ascii.detect_portrait()

    assert result is None


# ─── image_to_ascii: conversion ──────────────────────────────────────────────

def test_convert_portrait_returns_list_of_strings(tmp_path: Path) -> None:
    # Create a minimal valid PNG image using Pillow
    from PIL import Image
    img = Image.new('RGB', (10, 5), color='white')
    portrait = tmp_path / "test.png"
    img.save(portrait)

    result = image_to_ascii.convert_portrait(portrait, width=10)

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(line, str) for line in result)


def test_convert_portrait_file_missing_raises(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.png"

    with pytest.raises(FileNotFoundError):
        image_to_ascii.convert_portrait(missing)


# ─── image_to_ascii: fallback logic ──────────────────────────────────────────

def test_convert_with_fallback_uses_portrait_if_present(tmp_path: Path) -> None:
    # Create a test portrait
    from PIL import Image
    img = Image.new('RGB', (10, 5), color='black')
    portrait = tmp_path / "portrait.png"
    img.save(portrait)

    # Create a fallback file that should NOT be used
    fallback = tmp_path / "ascii-art.txt"
    fallback.write_text("FALLBACK\nFALLBACK\n")

    result = image_to_ascii.convert_with_fallback(portrait, fallback)

    # Result should come from portrait, not fallback
    assert "FALLBACK" not in '\n'.join(result)
    assert len(result) > 0  # Portrait conversion succeeded


def test_convert_with_fallback_uses_fallback_if_no_portrait(tmp_path: Path) -> None:
    # No portrait file
    fallback = tmp_path / "ascii-art.txt"
    fallback.write_text("FALLBACK LINE 1\nFALLBACK LINE 2\n")

    result = image_to_ascii.convert_with_fallback(None, fallback)

    assert result == ["FALLBACK LINE 1", "FALLBACK LINE 2"]
