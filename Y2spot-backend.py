from flask import Flask, request, render_template
from googleapiclient.discovery import build
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
import os
import re

# Load environment variables
load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SCOPE = "playlist-modify-public"

app = Flask(__name__)

def extract_playlist_id(url):
    query = urlparse(url).query
    params = parse_qs(query)
    return params.get("list", [None])[0]

def clean_title(title):
    title = re.sub(r"\(.*?\)|\[.*?\]", "", title)
    title = re.sub(r"(official|video|lyric|audio|HD|4K|feat\.?|ft\.?)", "", title, flags=re.I)
    title = re.sub(r"\s+", " ", title)
    return title.strip()

def get_first_10_video_titles(playlist_url):
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        raise ValueError("Invalid YouTube playlist URL")

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    titles = []

    print("[YOUTUBE] Fetching first 10 playlist videos...")
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=10
    )
    response = request.execute()

    for item in response["items"]:
        raw_title = item["snippet"]["title"]
        titles.append(clean_title(raw_title))

    print(f"[YOUTUBE] Retrieved {len(titles)} cleaned video titles.")
    return titles

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    yt_url = request.form['yt_url']
    print("[APP] Received playlist URL:", yt_url)

    try:
        titles = get_first_10_video_titles(yt_url)
    except Exception as e:
        return f"<h3>Error fetching YouTube playlist: {str(e)}</h3>"

    try:
        sp = Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SCOPE,
            open_browser=True
        ))

        user_id = sp.current_user()['id']
        playlist = sp.user_playlist_create(user=user_id, name="Y2Spot Playlist")

        matched_uris = []
        failed_titles = []
        result_log = []

        print("[SPOTIFY] Searching songs...")
        for title in titles:
            print(f"  🔍 Searching: {title}")
            result_log.append(f"<li>🔍 Searching: <b>{title}</b>")
            result = sp.search(q=title, type='track', limit=1)
            items = result['tracks']['items']
            if items:
                uri = items[0]['uri']
                matched_uris.append(uri)
                found_msg = f"✅ Found: {items[0]['name']} - {items[0]['artists'][0]['name']}"
                result_log[-1] += f"<br>&emsp;{found_msg}</li>"
                print(f"    {found_msg}")
            else:
                failed_titles.append(title)
                result_log[-1] += "<br>&emsp;❌ No match found</li>"
                print(f"    ❌ No match found for: {title}")

        if matched_uris:
            sp.playlist_add_items(playlist['id'], matched_uris)
            print(f"[SPOTIFY] Added {len(matched_uris)} tracks to playlist.")

        return f"""
        <h2>🎉 Spotify Playlist Created!</h2>
        <p>✅ Successfully added {len(matched_uris)} songs.</p>
        <p>❌ Failed to find {len(failed_titles)} songs.</p>
        <a href="{playlist['external_urls']['spotify']}" target="_blank">Open Playlist</a>
        <h3>Log:</h3>
        <ul>{''.join(result_log)}</ul>
        """

    except Exception as e:
        return f"<h3>Error with Spotify: {str(e)}</h3>"

if __name__ == '__main__':
    app.run(debug=True)
