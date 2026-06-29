"""
config.py — Central configuration for the Spotify Pixel Art app.
All credentials are read from environment variables; no secrets are hardcoded.
"""
import os
# ── Spotify OAuth credentials ─────────────────────────────────────────────────
# Register an app at https://developer.spotify.com/dashboard to obtain these.
SPOTIFY_CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI  = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
# OAuth scopes required by this application
SPOTIFY_SCOPES = "user-read-currently-playing user-read-playback-state"
# Path where spotipy stores the cached OAuth token between runs
SPOTIFY_CACHE_PATH = ".spotify_token_cache"
# ── Pixel-art settings ────────────────────────────────────────────────────────
# Intermediate canvas size (gives authentic lo-fi pixel appearance)
PIXEL_CANVAS_SIZE: int = 64          # width × height of the pixelated intermediate

# Final display size (integer-upscaled; no smoothing applied)
PIXEL_DISPLAY_SIZE: int = 512        # width × height of the saved PNG

# Number of colours in the quantised palette — choose 16, 32, or 64
PIXEL_PALETTE_COLORS: int = 32

# ── Polling ───────────────────────────────────────────────────────────────────
# How often (seconds) to ask Spotify what is currently playing
POLL_INTERVAL_SECONDS: int = 5

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_FILENAME: str = "pixel_album.png"
