# Spotify Pixel Art :)

Turns your currently playing Spotify track's album artwork into **authentic 8-bit pixel art** automatically, every time the song changes.

```
Full-res artwork  →  64×64 pixelated  →  colour-reduced  →  512×512 pixel art PNG
```

---

## Project structure

```
spotify_pixel/
├── config.py        # All settings & environment-variable bindings
├── spotify.py       # OAuth client + currently-playing lookup
├── pixel.py         # Image download & pixel-art conversion pipeline
├── main.py          # Polling loop & entry point
└── requirements.txt
```

---

## Quick start

### 1 — Create a Spotify app

1. Go to <https://developer.spotify.com/dashboard> and log in.
2. Click **Create app**.
3. Set the **Redirect URI** to `http://localhost:8888/callback`.
4. Copy your **Client ID** and **Client Secret**.

### 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### 3 — Export credentials

**macOS / Linux**
```bash
export SPOTIFY_CLIENT_ID="your-client-id-here"
export SPOTIFY_CLIENT_SECRET="your-client-secret-here"
# Optional — only needed if you changed the redirect URI in the Spotify dashboard
# export SPOTIFY_REDIRECT_URI="http://localhost:8888/callback"
```

**Windows (PowerShell)**
```powershell
$env:SPOTIFY_CLIENT_ID    = "your-client-id-here"
$env:SPOTIFY_CLIENT_SECRET = "your-client-secret-here"
```

### 4 — Run

```bash
python main.py
```

On the **first run** a browser tab opens asking you to log in and authorise the app.  
After that, the token is cached in `.spotify_token_cache` and no browser is needed.

---

## Output

Every time the track changes, `pixel_album.png` is overwritten with a fresh  
512 × 512 pixel-art version of the album cover.

Open the file in any image viewer; many viewers (macOS Preview, Windows Photos)  
auto-refresh when the file changes on disk.

---

## Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `PIXEL_CANVAS_SIZE` | `64` | Intermediate pixel canvas (px) |
| `PIXEL_DISPLAY_SIZE` | `512` | Final output resolution (px) |
| `PIXEL_PALETTE_COLORS` | `32` | Palette size — `16`, `32`, or `64` |
| `POLL_INTERVAL_SECONDS` | `5` | How often to check Spotify (seconds) |
| `OUTPUT_FILENAME` | `pixel_album.png` | Output file path |

Edit `config.py` directly or override by setting the corresponding environment variable.

---

## How the pixel-art pipeline works

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Download   artwork URL → Pillow Image (RGB)                 │
│  2. Downscale  any size → 64×64  (NEAREST resampling)          │
│  3. Quantise   64×64 RGB → 64×64 palette (32 colours, median-cut)│
│  4. Upscale    64×64 → 512×512  (NEAREST resampling → blocks)  │
│  5. Save       → pixel_album.png (PNG, lossless)               │
└─────────────────────────────────────────────────────────────────┘
```

Step 2 uses **nearest-neighbour** scaling (no blurring) to preserve hard edges.  
Step 4 uses the same filter so each logical pixel becomes a crisp 8×8 block.  
The palette reduction in step 3 gives the characteristic "limited colour" look of  
old game consoles and home computers.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `EnvironmentError: SPOTIFY_CLIENT_ID … must be set` | Export the env vars (step 3 above) |
| Browser opens but redirects to an error page | Double-check the Redirect URI in the Spotify dashboard matches `http://localhost:8888/callback` |
| `No track currently playing` logged repeatedly | Start playing music in a Spotify client on any device |
| `Pillow` import error | Run `pip install -r requirements.txt` |