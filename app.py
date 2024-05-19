from flask import Flask, request, redirect, session, render_template, jsonify
from datetime import datetime, timedelta
import pytz
import requests
import os
import base64
from dotenv import load_dotenv
from typing import List

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Needed for session management

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    scope = "user-library-read"
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&scope={scope}&redirect_uri={REDIRECT_URI}"
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    token_headers = {
        "Authorization": f'Basic {base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()}'
    }
    token_response = requests.post(token_url, data=token_data, headers=token_headers)
    access_token = token_response.json().get("access_token")
    session["access_token"] = access_token
    return redirect("/playlists")


@app.route("/liked-songs", methods=["GET"])
def liked_songs():
    if "access_token" not in session:
        return redirect("/")
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    response = requests.get("https://api.spotify.com/v1/me/tracks", headers=headers)
    items = response.json().get("items", [])

    if "filter_recent" in request.args:
        thirty_days_ago = datetime.now(pytz.utc) - timedelta(
            days=30
        )  # This is now an offset-aware datetime
        items = [
            item
            for item in items
            if datetime.strptime(item["added_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=pytz.utc
            )
            > thirty_days_ago
        ]

    songs = []
    for item in items:
        track = item["track"]
        album = track["album"]
        songs.append(
            {
                "artist": ", ".join(artist["name"] for artist in track["artists"]),
                "title": track["name"],
                "album_cover": album["images"][0]["url"] if album["images"] else None,
                "year": album["release_date"][
                    :4
                ],  # Assuming the release_date is in YYYY-MM-DD format
                "added": item["added_at"][:7],
            }
        )

    return render_template("liked_songs.html", songs=songs)


@app.route("/playlists")
def playlists():
    if "access_token" not in session:
        return redirect("/")
    access_token = session["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me/playlists", headers=headers)
    playlists = response.json().get("items", [])
    return render_template("playlists.html", playlists=playlists)


@app.route("/api/playlist/<playlist_id>")
def get_playlist(playlist_id):
    if "access_token" not in session:
        return jsonify([]), 401  # Unauthorized
    access_token = session["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers
    )
    songs = response.json().get("items", [])
    return jsonify(songs)


def fetch_spotify_playlist_details(playlist_id):
    return get_playlist(playlist_id)


def convert_tracks_to_apple_music(tracks, dev_token):
    """
    Convert Spotify track details to Apple Music track IDs.

    Args:
    tracks (list): List of dictionaries containing track details from Spotify.
    dev_token (str): Apple Music developer token for authentication.

    Returns:
    list: List of dictionaries suitable for creating a playlist in Apple Music.
    """
    apple_music_tracks = []
    headers = {"Authorization": f"Bearer {dev_token}"}

    for track in tracks:
        # Constructing a search query using track name and artist name
        track_name = track["name"]
        artist_name = track["artists"][0]["name"]  # Assuming the first artist
        query = f"{track_name} {artist_name}"

        # URL encode the query
        from urllib.parse import quote

        query = quote(query)

        url = f"https://api.music.apple.com/v1/catalog/us/search?term={query}&types=songs&limit=1"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            result = response.json()
            # Navigating through the JSON response to find the track ID
            songs = result["results"]["songs"]["data"]
            if songs:
                track_id = songs[0]["id"]  # Get the first song's ID
                apple_music_tracks.append({"id": track_id, "type": "songs"})
            else:
                print(f"No results found for {query}")
        else:
            print(f"Failed to search for {query}, status code {response.status_code}")

    return apple_music_tracks


@app.route("/transfer_playlist", methods=["POST"])
def create_apple_music_playlist(
    apple_music_dev_token, user_token, playlist_name, apple_music_tracks
):
    url = "https://api.music.apple.com/v1/me/library/playlists"
    headers = {
        "Authorization": f"Bearer {apple_music_dev_token}",
        "Music-User-Token": user_token,
    }
    payload = {
        "attributes": {"name": playlist_name, "description": "Created from Spotify"},
        "relationships": {
            "tracks": {
                "data": [
                    {"id": track_id, "type": "songs"} for track_id in apple_music_tracks
                ]
            }
        },
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()


@app.route("/api/transfer_playlist", methods=["POST"])
def transfer_playlist():
    data = request.json
    spotify_playlist_id = data.get("playlistId")
    user_token = data.get("userToken")  # This should be passed securely

    # Fetch playlist details from Spotify (implement this function)
    # playlist_name,
    tracks = fetch_spotify_playlist_details(spotify_playlist_id)

    # Convert Spotify tracks to Apple Music track IDs (implement this function)
    apple_music_tracks = convert_tracks_to_apple_music(user_token, tracks)

    # Create the playlist in Apple Music
    response = create_apple_music_playlist(
        apple_music_dev_token, user_token, playlist_name, apple_music_tracks
    )

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)
