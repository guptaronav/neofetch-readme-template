"""Convert portrait images to ASCII art automatically.

Supports portrait.png and portrait.jpg in the repo root. Falls back to
ascii-art.txt if no portrait is found. Uses Pillow for image processing
and custom grayscale + character mapping for ASCII conversion.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PIL import Image


ROOT = Path(__file__).parent
DEFAULT_WIDTH = 50
DEFAULT_CHARSET = " .:-=+*#%@"


def detect_portrait() -> Optional[Path]:
    """Look for portrait.png or portrait.jpg in the repo root.

    Returns the first match found, or None if neither exists.
    """
    for name in ["portrait.png", "portrait.jpg"]:
        path = ROOT / name
        if path.exists():
            return path
    return None


def convert_portrait(path: Path, width: int = DEFAULT_WIDTH,
                     charset: str = DEFAULT_CHARSET) -> list[str]:
    """Convert an image to ASCII art lines.

    Args:
        path: Path to the image file (PNG, JPG, etc.)
        width: Output width in characters (default: 50)
        charset: Characters to use from light to dark (default: 10-char set)

    Returns:
        List of ASCII art lines (strings)

    Raises:
        FileNotFoundError: If the image file doesn't exist
        IOError: If the image cannot be opened or processed
    """
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    try:
        img = Image.open(path)
    except IOError as e:
        raise IOError(f"Cannot open image {path}: {e}") from e

    # Resize to target width, maintaining aspect ratio
    height = max(1, width // 2)  # Aspect ratio for character cells
    img.thumbnail((width, height), Image.Resampling.LANCZOS)

    # Convert to grayscale
    img = img.convert("L")

    # Convert to ASCII
    result = []
    for y in range(img.height):
        line = ""
        for x in range(img.width):
            pixel = img.getpixel((x, y))
            # Map pixel brightness (0-255) to charset index
            idx = min(int((pixel / 255) * (len(charset) - 1)), len(charset) - 1)
            line += charset[idx]
        result.append(line)

    return result


def convert_with_fallback(portrait_path: Optional[Path],
                          fallback_ascii_path: Path) -> list[str]:
    """Convert portrait if present, otherwise fall back to ascii-art.txt.

    Args:
        portrait_path: Path to portrait image, or None if not found
        fallback_ascii_path: Path to ascii-art.txt or similar

    Returns:
        List of ASCII art lines from either source
    """
    # Try portrait first
    if portrait_path:
        try:
            lines = convert_portrait(portrait_path)
            return lines
        except (FileNotFoundError, IOError) as e:
            print(f"Warning: Could not convert portrait: {e}", file=sys.stderr)
            # Fall through to fallback

    # Fall back to ascii-art.txt
    if fallback_ascii_path.exists():
        text = fallback_ascii_path.read_text().rstrip("\n")
        if text:
            return text.split("\n")

    # Last resort: placeholder
    return ["(no portrait or ascii-art.txt found)"]
