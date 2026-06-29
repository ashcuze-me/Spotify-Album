"""
pixel.py — Downloads album artwork and converts it to authentic 8-bit pixel art.

Pipeline
--------
1. Fetch the artwork image over HTTP.
2. Resize down to PIXEL_CANVAS_SIZE × PIXEL_CANVAS_SIZE using NEAREST resampling
   (hard pixel edges, no blurring).
3. Quantise the palette to PIXEL_PALETTE_COLORS colours via Pillow's adaptive
   quantisation (median-cut algorithm).
4. Upscale the result to PIXEL_DISPLAY_SIZE × PIXEL_DISPLAY_SIZE using NEAREST
   resampling so every logical pixel becomes a crisp block.
5. Save as PNG to OUTPUT_FILENAME.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import requests
from PIL import Image

import config

log = logging.getLogger(__name__)


# ── Image download ────────────────────────────────────────────────────────────

def download_image(url: str, timeout: int = 10) -> Image.Image:
    """
    Fetch an image from *url* and return it as a Pillow Image.

    Args:
        url:     HTTP/HTTPS URL of the image.
        timeout: Request timeout in seconds.

    Returns:
        An RGB PIL Image.

    Raises:
        requests.HTTPError: on a non-2xx HTTP response.
        requests.RequestException: on connection / timeout errors.
        OSError: if Pillow cannot decode the downloaded bytes as an image.
    """
    log.debug("Downloading artwork from: %s", url)

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()  # Raise on 4xx / 5xx

    image = Image.open(io.BytesIO(response.content))

    # Normalise to RGB — artwork could be CMYK, RGBA, P, etc.
    image = image.convert("RGB")

    log.debug("Downloaded image size: %s", image.size)
    return image


# ── Pixel-art conversion ──────────────────────────────────────────────────────

def to_pixel_art(
    image: Image.Image,
    canvas_size: int = config.PIXEL_CANVAS_SIZE,
    display_size: int = config.PIXEL_DISPLAY_SIZE,
    palette_colors: int = config.PIXEL_PALETTE_COLORS,
) -> Image.Image:
    """
    Convert a full-resolution RGB image to a lo-fi 8-bit pixel-art style.

    Steps
    -----
    1. Downscale to *canvas_size* × *canvas_size* with NEAREST-neighbour so we
       get hard pixel boundaries right from the start.
    2. Quantise to *palette_colors* colours using Pillow's adaptive quantiser.
       Valid values for Pillow's ``quantize`` method are 2–256.
    3. Convert back to RGB (quantised images are palette-mode 'P').
    4. Upscale to *display_size* × *display_size* with NEAREST-neighbour so
       each lo-res pixel becomes a perfect square block.

    Args:
        image:         Source image (any size, RGB).
        canvas_size:   Target width/height for the pixelated intermediate.
        display_size:  Final output width/height (should be a multiple of canvas_size).
        palette_colors: Number of colours in the reduced palette (16, 32, or 64).

    Returns:
        An RGB PIL Image ready to be saved.
    """
    # ── Step 1: Downscale (pixelate) ──────────────────────────────────────────
    # Image.NEAREST = no interpolation, preserves hard edges
    small: Image.Image = image.resize(
        (canvas_size, canvas_size),
        resample=Image.Resampling.NEAREST,
    )
    log.debug("Downscaled to %s×%s", canvas_size, canvas_size)

    # ── Step 2: Palette quantisation (colour reduction) ───────────────────────
    # Pillow's adaptive quantiser uses median-cut internally.
    # We request palette_colors colours and then convert back to full RGB so
    # subsequent operations stay in a familiar colour mode.
    palette_colors = max(2, min(256, palette_colors))  # clamp to valid Pillow range
    quantised: Image.Image = small.quantize(colors=palette_colors, method=Image.Quantize.MEDIANCUT)
    log.debug("Quantised palette to %d colours", palette_colors)

    # ── Step 3: Back to RGB ───────────────────────────────────────────────────
    rgb: Image.Image = quantised.convert("RGB")

    # ── Step 4: Upscale (make pixels visible as blocks) ──────────────────────
    large: Image.Image = rgb.resize(
        (display_size, display_size),
        resample=Image.Resampling.NEAREST,
    )
    log.debug("Upscaled to %s×%s", display_size, display_size)

    return large


# ── Convenience one-shot function ────────────────────────────────────────────

def process_artwork(artwork_url: str, output_path: str = config.OUTPUT_FILENAME) -> Path:
    """
    Download the artwork at *artwork_url*, convert it to pixel art, and save
    the result to *output_path*.

    Args:
        artwork_url: URL of the album artwork (from Spotify API).
        output_path: Destination filename for the output PNG.

    Returns:
        Path object pointing to the saved file.

    Raises:
        Any exception from download_image() or Pillow save operations.
    """
    # 1. Download
    original = download_image(artwork_url)

    # 2. Convert
    pixel = to_pixel_art(original)

    # 3. Save
    dest = Path(output_path)
    pixel.save(dest, format="PNG")
    log.info("Pixel art saved → %s", dest.resolve())

    return dest
