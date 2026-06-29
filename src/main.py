"""
main.py — Entry point for the Spotify Pixel Art application.

Run with:
    python main.py

The script:
  • Authenticates with Spotify via OAuth (browser pop-up on first run).
  • Polls the currently-playing endpoint every POLL_INTERVAL_SECONDS seconds.
  • When the track changes (or on first detection), downloads the album artwork,
    converts it to pixel art, and saves it as OUTPUT_FILENAME.
  • Runs indefinitely until interrupted with Ctrl-C.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Optional

from . import config
from . import spotify
from . import pixel
from pixel import process_artwork
from spotify import TrackInfo, create_spotify_client, get_currently_playing

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


# ── Helpers ───────────────────────────────────────────────────────────────────

def validate_config() -> None:
    """
    Abort early with a helpful message if required credentials are missing,
    rather than letting the error surface deep inside spotipy.
    """
    missing: list[str] = []
    if not config.SPOTIFY_CLIENT_ID:
        missing.append("SPOTIFY_CLIENT_ID")
    if not config.SPOTIFY_CLIENT_SECRET:
        missing.append("SPOTIFY_CLIENT_SECRET")

    if missing:
        log.error(
            "Missing required environment variable(s): %s\n"
            "  Create a Spotify app at https://developer.spotify.com/dashboard\n"
            "  then export the credentials before running:\n"
            "    export SPOTIFY_CLIENT_ID='<your-client-id>'\n"
            "    export SPOTIFY_CLIENT_SECRET='<your-client-secret>'",
            ", ".join(missing),
        )
        sys.exit(1)

    valid_palette_sizes = {16, 32, 64}
    if config.PIXEL_PALETTE_COLORS not in valid_palette_sizes:
        log.warning(
            "PIXEL_PALETTE_COLORS=%d is not one of %s — will still work but "
            "may not give authentic 8-bit aesthetics.",
            config.PIXEL_PALETTE_COLORS,
            valid_palette_sizes,
        )


def handle_track_change(track: TrackInfo) -> None:
    """
    Called whenever a new track is detected.  Downloads artwork, converts to
    pixel art, and prints a status line.
    """
    print()
    log.info("♪  Now playing: %s — %s  [%s]", track.artist_name, track.track_name, track.album_name)
    log.info("   Generating pixel art …")

    try:
        dest = process_artwork(track.artwork_url, config.OUTPUT_FILENAME)
        log.info("✓  Pixel art saved to: %s", dest)
    except Exception as exc:  # noqa: BLE001
        log.error("Failed to generate pixel art: %s", exc)


# ── Main polling loop ─────────────────────────────────────────────────────────

def run() -> None:
    """
    Main loop: authenticate → poll Spotify → react to song changes.
    """
    validate_config()

    log.info("Initialising Spotify client …")
    client = create_spotify_client()
    log.info("Connected to Spotify  ✓")

    log.info(
        "Polling every %ds for currently-playing track.  Press Ctrl-C to stop.",
        config.POLL_INTERVAL_SECONDS,
    )

    last_track_id: Optional[str] = None

    while True:
        track: Optional[TrackInfo] = get_currently_playing(client)

        if track is None:
            # Nothing playing or playback paused — wait quietly
            log.debug("No track currently playing.")
        elif track.track_id != last_track_id:
            # New song detected — generate pixel art
            last_track_id = track.track_id
            handle_track_change(track)
        else:
            # Same track as before — nothing to do
            log.debug("Same track still playing: %s", track.track_name)

        try:
            time.sleep(config.POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            break

    log.info("Stopped by user.")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        log.info("Goodbye!")
