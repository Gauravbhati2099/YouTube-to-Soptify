# streamlit_app.py
import streamlit as st
import time

st.set_page_config(page_title="Y2Spotify Converter", layout="centered")
st.title("🎵 YouTube → Spotify Playlist Converter")

# Step 1: Paste YouTube Playlist URL
youtube_url = st.text_input("Paste your YouTube Playlist Link")

if youtube_url:
    st.info("🔗 Detected YouTube playlist...")
    with st.spinner("Fetching playlist..."):
        time.sleep(1.5)
        # Mock fetched data
        yt_songs = [
            {"title": "Blinding Lights", "artist": "The Weeknd"},
            {"title": "Stay", "artist": "The Kid LAROI & Justin Bieber"},
            {"title": "Shape of You", "artist": "Ed Sheeran"},
            {"title": "Unknown Lo-Fi Track", "artist": "N/A"},
        ]
    st.success(f"✅ Found {len(yt_songs)} songs in playlist!")
    
    # Display fetched songs
    st.subheader("🎧 Songs from YouTube:")
    for s in yt_songs:
        st.markdown(f"- {s['title']} — *{s['artist']}*")

    # Step 2: Ask for Spotify login (simulated)
    st.subheader("🔐 Step 2: Spotify Authorization")
    login_clicked = st.button("🔓 Login with Spotify")

    if login_clicked:
        st.success("✅ Logged in as: testuser123 (simulated)")
        st.write("Starting matching process...")

        # Step 3: Simulate Matching
        st.subheader("🎯 Matching Songs to Spotify")
        matched = []
        for song in yt_songs:
            with st.spinner(f"Searching Spotify for: {song['title']}..."):
                time.sleep(1)
                if song["title"] == "Unknown Lo-Fi Track":
                    st.warning("❌ Not found on Spotify")
                    continue
                matched.append(song)
                st.success(f"✅ Found: {song['title']}")

        # Step 4: Create Playlist Preview
        if matched:
            st.subheader("📦 Create Spotify Playlist")
            new_name = st.text_input("Name your new Spotify playlist:", value="YouTube Migrated Playlist")

            if st.button("🚀 Create Playlist"):
                with st.spinner("Creating playlist on Spotify..."):
                    time.sleep(2)
                st.success(f"🎉 Playlist '{new_name}' created with {len(matched)} songs!")
                st.markdown("🔗 [Open in Spotify](https://open.spotify.com/playlist/fake1234) (simulated)")

