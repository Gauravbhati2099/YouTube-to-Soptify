from flask import Flask, render_template, request, jsonify
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import requests
import json
import os

# =========================
# Load Environment
# =========================

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"

required = [
    YOUTUBE_API_KEY,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI
]

if not all(required):
    raise RuntimeError("Missing environment variables")

print("Environment loaded successfully")

# =========================
# Clients
# =========================

youtube = build(
    "youtube",
    "v3",
    developerKey=YOUTUBE_API_KEY
)

sp = Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-modify-public"
    )
)

# =========================
# Flask
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

# =========================
# Helpers
# =========================

def extract_playlist_id(url):
    query = urlparse(url).query
    params = parse_qs(query)
    return params.get("list", [None])[0]


def get_playlist_titles(url):

    playlist_id = extract_playlist_id(url)

    if not playlist_id:
        raise ValueError("Invalid YouTube Playlist URL")

    titles = []
    next_page_token = None

    while True:

        response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in response["items"]:
            titles.append(
                item["snippet"]["title"]
            )

        next_page_token = response.get(
            "nextPageToken"
        )

        if not next_page_token:
            break

    return titles


def extract_metadata_batch(titles):

    prompt = f"""You are a music metadata extractor.

For each YouTube title return:

{
  "song":"",
  "artist":""
}

Ignore:
- Official Video
- Lyrics
- HD
- 4K
- Live
- Remix tags

Return JSON only.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    try:
        return json.loads(
            response.json()["response"]
        )
    except Exception:
        return [
            {
                "youtube_title": t,
                "song": t,
                "artist": ""
            }
            for t in titles
        ]


def find_song(song, artist):

    query = f'track:"{song}"'

    if artist:
        query += f' artist:"{artist}"'

    result = sp.search(
        q=query,
        type="track",
        limit=1
    )

    items = result["tracks"]["items"]

    if items:
        return items[0]

    return None

# =========================
# Convert Endpoint
# =========================

@app.route("/convert", methods=["POST"])
def convert():

    yt_url = request.form["yt_url"]

    titles = get_playlist_titles(yt_url)

    metadata = []

    batch_size = 25

    for i in range(0, len(titles), batch_size):

        batch = titles[i:i + batch_size]

        metadata.extend(
            extract_metadata_batch(batch)
        )

    user = sp.current_user()

    playlist = sp.user_playlist_create(
        user["id"],
        "Imported Playlist"
    )

    matched_uris = []
    report = []

    for item in metadata:

        spotify_track = find_song(
            item["song"],
            item["artist"]
        )

        if spotify_track:

            uri = spotify_track["uri"]

            matched_uris.append(uri)

            report.append({
                "youtube_title": item["youtube_title"],
                "song": item["song"],
                "artist": item["artist"],
                "spotify_track": spotify_track["name"],
                "spotify_artist": spotify_track["artists"][0]["name"],
                "spotify_uri": uri,
                "success": True
            })

        else:

            report.append({
                "youtube_title": item["youtube_title"],
                "song": item["song"],
                "artist": item["artist"],
                "spotify_uri": None,
                "success": False
            })

    for i in range(0, len(matched_uris), 100):

        sp.playlist_add_items(
            playlist["id"],
            matched_uris[i:i + 100]
        )

    return jsonify({
        "success": True,
        "total_videos": len(titles),
        "matched_tracks": len(matched_uris),
        "failed_tracks": len(titles) - len(matched_uris),
        "spotify_playlist": playlist["external_urls"]["spotify"],
        "results": report
    })

# =========================
# Run
# =========================

if __name__ == "__main__":
    app.run(debug=True)
