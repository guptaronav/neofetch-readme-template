"""Tests for build.py."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import build


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
    assert re.match(r"^\d+ years?, \d+ months?, \d+ days?$", age)


def test_daily_readme_none_returns_none() -> None:
    assert build.daily_readme(None) is None
    assert build.daily_readme("") is None


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


def test_render_svg_omits_uptime_when_no_birthday() -> None:
    svg = build.render_svg(_make_cfg(birthday=None), ["x"], build.LIGHT_THEME)
    assert "Uptime" not in svg


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
