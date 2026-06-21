"""
Integration test: -auto-orient bakes EXIF rotation into pixel data.

Fixture: 200x100 JPEG with EXIF Orientation=6 (90° CW).
Expected proxy: portrait dimensions (height > width), Orientation tag 1 or absent.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from PIL import Image

from rapidcull.adapters.imagemagick import ImageMagickAdapter


def _make_rotated_jpeg(path: Path) -> None:
    """Write a 200x100 landscape JPEG tagged as Orientation=6 (90° CW)."""
    img = Image.new("RGB", (200, 100), color=(128, 64, 32))
    # Build minimal EXIF blob with Orientation=6
    exif = img.getexif()
    exif[274] = 6  # 274 == Orientation tag
    img.save(path, format="JPEG", exif=exif.tobytes())


def _read_orientation_exiftool(path: Path) -> int | None:
    """Return EXIF Orientation value via exiftool, or None if tag absent."""
    try:
        result = subprocess.run(
            ["exiftool", "-Orientation#", "-s3", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
        val = result.stdout.strip()
        return int(val) if val else None
    except (OSError, ValueError):
        return None


def _read_dimensions_pil(path: Path) -> tuple[int, int]:
    """Return (width, height) of image without applying EXIF orientation."""
    with Image.open(path) as im:
        return im.size  # (width, height), raw pixel dims


@pytest.mark.integration
def test_auto_orient_bakes_rotation_into_proxy(tmp_path: Path) -> None:
    """Display proxy of a 90°-tagged landscape JPEG must be portrait in pixels."""
    src = tmp_path / "rotated.jpg"
    _make_rotated_jpeg(src)

    # Sanity: source file is landscape pixels (200x100) with Orientation=6
    src_w, src_h = _read_dimensions_pil(src)
    assert src_w == 200 and src_h == 100, f"fixture dims wrong: {src_w}x{src_h}"

    display_out = tmp_path / "display.webp"
    adapter = ImageMagickAdapter()
    outcome = adapter.generate_still_thumbnail(
        path=src,
        display_path=display_out,
    )

    assert outcome.ok, f"adapter failed: {outcome.reason}"
    assert display_out.exists(), "display proxy not written"

    # Pixel dimensions must be portrait after -auto-orient bakes the rotation
    out_w, out_h = _read_dimensions_pil(display_out)
    assert out_h > out_w, (
        f"expected portrait proxy (h>w) but got {out_w}x{out_h} — "
        "-auto-orient may not be applied"
    )

    # EXIF Orientation must be 1 or absent in the output
    orientation = _read_orientation_exiftool(display_out)
    assert orientation in (None, 1), (
        f"expected Orientation=1 or absent but got {orientation} — "
        "rotation tag was not reset"
    )
