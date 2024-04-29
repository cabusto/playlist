from flask import Flask, request, redirect, session, render_template
from datetime import datetime, timedelta
import pytz
import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Needed for session management

# Replace these with your Spotify app credentials
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT")


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
    return redirect("/liked-songs")


@app.route("/liked-songs", methods=["GET"])
def liked_songs():
    if "access_token" not in session:
        return redirect("/login")
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


@app.route("/test")
def test():
    return render_template("test.html")


if __name__ == "__main__":
    app.run(debug=True)
