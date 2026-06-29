"""
spotify.py — Handles Spotify OAuth authentication and currently-playing lookups.

Uses the spotipy library (https://spotipy.readthedocs.io/) which wraps the
Spotify Web API and manages the OAuth 2.0 PKCE / Authorization-Code flows.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import config

log = logging.getLogger(__name__)


# ── Public data class ─────────────────────────────────────────────────────────

@dataclass
class TrackInfo:
    """Lightweight snapshot of the currently playing track."""
    track_id:    str   # Unique Spotify track ID
    track_name:  str
    artist_name: str
    album_name:  str
    artwork_url: str   # Direct URL of the largest available album-art image


# ── Spotify client factory ────────────────────────────────────────────────────

def create_spotify_client() -> spotipy.Spotify:
    """
    Build an authenticated spotipy.Spotify client using the Authorization-Code
    flow.  On the first run the user is sent to a Spotify login page; the token
    is then cached at SPOTIFY_CACHE_PATH for subsequent runs.

    Raises:
        EnvironmentError: if SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET are missing.
    """
    if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
        raise EnvironmentError(
            "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set as "
            "environment variables before running this application."
        )

    auth_manager = SpotifyOAuth(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI,
        scope=config.SPOTIFY_SCOPES,
        cache_path=config.SPOTIFY_CACHE_PATH,
        open_browser=True,   # Auto-open the auth page in the default browser
    )

    client = spotipy.Spotify(auth_manager=auth_manager)
    log.info("Spotify client created successfully.")
    return client


# ── Currently-playing helper ──────────────────────────────────────────────────

def get_currently_playing(client: spotipy.Spotify) -> Optional[TrackInfo]:
    """
    Query the Spotify 'currently playing' endpoint.

    Returns:
        A TrackInfo instance if a track is actively playing, otherwise None
        (the user may be paused, have no active device, or the API may return
        an empty response).

    The function swallows non-critical API errors and logs them so that a
    transient network hiccup does not crash the polling loop.
    """
    try:
        result = client.current_playback()
    except spotipy.SpotifyException as exc:
        log.warning("Spotify API error while fetching playback: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001  (broad — network errors etc.)
        log.warning("Unexpected error fetching playback: %s", exc)
        return None

    # Validate the response structure before accessing nested keys
    if not result:
        log.debug("No active playback session returned by Spotify.")
        return None

    if not result.get("is_playing"):
        log.debug("Spotify reports playback is paused or stopped.")
        return None

    item = result.get("item")
    if not item or item.get("type") != "track":
        # Could be a podcast episode or similar — we only handle tracks
        log.debug("Currently playing item is not a music track: %s", item)
        return None

    # Extract the highest-resolution artwork image (images are sorted by size,
    # largest first, by the Spotify API).
    images: list[dict] = item.get("album", {}).get("images", [])
    if not images:
        log.warning("Album has no artwork images — skipping.")
        return None

    artwork_url: str = images[0]["url"]

    artists: list[dict] = item.get("artists", [{}])
    artist_name: str = ", ".join(a.get("name", "Unknown") for a in artists)

    return TrackInfo(
        track_id=item["id"],
        track_name=item.get("name", "Unknown Track"),
        artist_name=artist_name,
        album_name=item.get("album", {}).get("name", "Unknown Album"),
        artwork_url=artwork_url,
    )
