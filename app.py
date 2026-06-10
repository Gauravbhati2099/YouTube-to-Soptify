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

def extract_yt_playlist_id(url):
    query = urlparse(url).query
    params = parse_qs(query)
    return params.get("list", [None])[0]


def extract_spotify_playlist_id(url):
    """Extract playlist ID from Spotify URL"""
    # Handle different Spotify URL formats
    # https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
    # spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
    
    if "spotify:playlist:" in url:
        return url.split("spotify:playlist:")[1]
    
    if "open.spotify.com/playlist/" in url:
        playlist_id = url.split("open.spotify.com/playlist/")[1]
        # Remove query parameters
        return playlist_id.split("?")[0]
    
    raise ValueError("Invalid Spotify Playlist URL")


def get_playlist_titles(url):

    playlist_id = extract_yt_playlist_id(url)

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


def get_spotify_playlist_tracks(playlist_url):
    """Extract tracks from a Spotify playlist URL"""
    
    playlist_id = extract_spotify_playlist_id(playlist_url)
    
    tracks = []
    next_page_token = None
    
    while True:
        result = sp.playlist_items(
            playlist_id,
            limit=50,
            offset=next_page_token or 0
        )
        
        for item in result["items"]:
            if item["track"]:
                track = item["track"]
                tracks.append({
                    "song": track["name"],
                    "artist": track["artists"][0]["name"] if track["artists"] else "",
                    "spotify_uri": track["uri"],
                    "album": track["album"]["name"]
                })
        
        if result.get("next"):
            next_page_token = (next_page_token or 0) + 50
        else:
            break
    
    return tracks


def search_youtube_video(song, artist):
    """Search for a song on YouTube"""
    
    query = f"{song}"
    if artist:
        query += f" {artist}"
    
    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=1,
            fields="items(snippet(title,channelTitle),id(videoId))"
        )
        
        result = request.execute()
        
        if result["items"]:
            video = result["items"][0]
            video_id = video["id"]["videoId"]
            return {
                "video_id": video_id,
                "title": video["snippet"]["title"],
                "channel": video["snippet"]["channelTitle"],
                "youtube_url": f"https://www.youtube.com/watch?v={video_id}"
            }
        
        return None
        
    except Exception as e:
        print(f"Error searching YouTube: {e}")
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
# Reverse Convert Endpoint
# =========================

@app.route("/convert-reverse", methods=["POST"])
def convert_reverse():
    """Convert Spotify playlist to YouTube videos"""
    
    spotify_url = request.form["spotify_url"]
    
    try:
        tracks = get_spotify_playlist_tracks(spotify_url)
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    
    report = []
    matched_videos = []
    
    for track in tracks:
        youtube_video = search_youtube_video(
            track["song"],
            track["artist"]
        )
        
        if youtube_video:
            matched_videos.append(youtube_video)
            
            report.append({
                "spotify_track": track["song"],
                "spotify_artist": track["artist"],
                "spotify_uri": track["spotify_uri"],
                "youtube_title": youtube_video["title"],
                "youtube_channel": youtube_video["channel"],
                "youtube_url": youtube_video["youtube_url"],
                "youtube_video_id": youtube_video["video_id"],
                "success": True
            })
        else:
            report.append({
                "spotify_track": track["song"],
                "spotify_artist": track["artist"],
                "spotify_uri": track["spotify_uri"],
                "youtube_url": None,
                "success": False
            })
    
    return jsonify({
        "success": True,
        "total_tracks": len(tracks),
        "matched_videos": len(matched_videos),
        "failed_tracks": len(tracks) - len(matched_videos),
        "youtube_videos": [v["youtube_url"] for v in matched_videos],
        "results": report
    })

# =========================
# Run
# =========================

if __name__ == "__main__":
    app.run(debug=True)
