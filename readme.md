# 🎵 PlaylistAI

Convert YouTube playlists into Spotify playlists using AI-powered song extraction and automatic playlist creation.

PlaylistAI uses:

* YouTube Data API v3
* Spotify Web API
* Ollama (Llama 3)
* Flask

to automatically identify songs from YouTube playlist videos, find their Spotify equivalents, and create a Spotify playlist containing the matched tracks.

---

# Features

✅ Convert entire YouTube playlists

✅ AI-powered song and artist extraction

✅ Spotify playlist auto-creation

✅ Detailed conversion report

✅ Supports large playlists

✅ Local LLM processing with Ollama

✅ JSON API response

---

# Architecture

```text
User
 │
 ▼
Flask Web App
 │
 ├── YouTube API
 │       ▼
 │   Playlist Videos
 │
 ├── Ollama (Llama 3)
 │       ▼
 │ Song + Artist Extraction
 │
 └── Spotify API
         ▼
   Playlist Creation
         ▼
      Spotify Playlist
```

---

# Tech Stack

| Component              | Technology       |
| ---------------------- | ---------------- |
| Backend                | Flask            |
| LLM                    | Ollama + Llama 3 |
| Music Source           | YouTube Data API |
| Playlist Target        | Spotify Web API  |
| Environment Management | python-dotenv    |
| HTTP Client            | requests         |

---

# Project Structure

```text
project/
│
├── app.py
├── requirements.txt
├── .env
│
├── templates/
│   └── index.html
│
└── README.md
```

---

# Prerequisites

## Python

Python 3.10+

Verify:

```bash
python --version
```

---

## Ollama

Install Ollama:

https://ollama.com

Pull the model:

```bash
ollama pull llama3.1:8b
```

Start Ollama:

```bash
ollama serve
```

Verify:

```bash
ollama list
```

---

## Spotify Developer Account

Create an application:

https://developer.spotify.com/dashboard

Collect:

* Client ID
* Client Secret

Add Redirect URI:

```text
http://127.0.0.1:8888/callback
```

---

## Google Cloud Project

Enable:

```text
YouTube Data API v3
```

Generate:

```text
API Key
```

---

# Installation

Clone repository:

```bash
git clone https://github.com/yourusername/playlistai.git

cd playlistai
```

Create virtual environment:

```bash
python -m venv venv
```

Activate:

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file:

```env
YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY

SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID

SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET

SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

OLLAMA_MODEL=llama3.1:8b
```

---

# Running the Application

Start Ollama:

```bash
ollama serve
```

Start Flask:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

# Usage

1. Paste a YouTube playlist URL.
2. Click **Convert Playlist**.
3. PlaylistAI:

   * Fetches all videos.
   * Uses Llama 3 to extract song metadata.
   * Searches Spotify.
   * Creates a Spotify playlist.
   * Adds matched tracks.
4. Returns a conversion report.

---

# Example API Response

```json
{
  "success": true,
  "total_videos": 52,
  "matched_tracks": 49,
  "failed_tracks": 3,
  "spotify_playlist": "https://open.spotify.com/playlist/xxxx",
  "results": [
    {
      "youtube_title": "Ed Sheeran - Shape of You",
      "song": "Shape of You",
      "artist": "Ed Sheeran",
      "spotify_uri": "spotify:track:xxxxx",
      "success": true
    }
  ]
}
```

---

# Workflow

```text
YouTube Playlist
        │
        ▼
Extract Video Titles
        │
        ▼
Llama 3 Metadata Extraction
        │
        ▼
Spotify Search
        │
        ▼
Playlist Creation
        │
        ▼
Track Upload
        │
        ▼
Conversion Report
```

---

# Known Limitations

* Private YouTube playlists are not supported.
* Some remixes and live performances may not map correctly.
* Accuracy depends on playlist title quality.
* Spotify catalog availability varies by region.

---

# Future Improvements

* Playlist preview before conversion
* Progress tracking
* Parallel Spotify search
* SQLite caching
* Playlist artwork synchronization
* User authentication
* Streamlit frontend
* Docker deployment
* Background task queue

---

# Security Notes

Never commit:

```text
.env
spotify cache files
API keys
OAuth tokens
```

Recommended `.gitignore`:

```gitignore
.env
__pycache__/
venv/
.cache/
*.pyc
```

---

# License

MIT License

---

# Acknowledgements

* Spotify Web API
* YouTube Data API v3
* Ollama
* Llama 3
* Flask