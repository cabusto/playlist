import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from datetime import datetime
import time
from flask import current_app


def get_spotify_client():
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=current_app.config["SPOTIPY_CLIENT_ID"],
            client_secret=current_app.config["SPOTIPY_CLIENT_SECRET"],
            redirect_uri=current_app.config["SPOTIPY_REDIRECT_URI"],
            scope="playlist-modify-public user-library-read",
        )
    )
    return sp


def get_liked_songs():
    sp = get_spotify_client()
    results = sp.current_user_saved_tracks()
    liked_songs = results["items"]

    while results["next"]:
        results = sp.next(results)
        liked_songs.extend(results["items"])

    return liked_songs


def filter_songs_by_date(songs):
    song_data = []

    for item in songs:
        added_at = item["added_at"]
        added_at_date = datetime.strptime(added_at, "%Y-%m-%dT%H:%M:%SZ")
        song_data.append(
            {
                "track_name": item["track"]["name"],
                "artist_name": item["track"]["artists"][0]["name"],
                "album_name": item["track"]["album"]["name"],
                "added_at": added_at_date,
                "track_uri": item["track"]["uri"],
            }
        )

    df = pd.DataFrame(song_data)
    df["month_year"] = df["added_at"].dt.to_period("M")
    return df


def create_playlist(user_id, name, description):
    sp = get_spotify_client()
    playlist = sp.user_playlist_create(
        user=user_id, name=name, public=True, description=description
    )
    return playlist["id"]


def add_tracks_to_playlist(playlist_id, track_uris):
    sp = get_spotify_client()
    sp.playlist_add_items(playlist_id, track_uris)
