from flask import Blueprint, render_template, request, redirect, url_for
from .spotify import (
    get_liked_songs,
    filter_songs_by_date,
    create_playlist,
    add_tracks_to_playlist,
)
import pandas as pd

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/create_playlists", methods=["POST"])
def create_playlists():
    user_id = request.form.get("user_id")
    month = request.form.get("month")
    year = request.form.get("year")

    if not user_id or not month or not year:
        return redirect(url_for("main.index"))

    liked_songs = get_liked_songs()
    filtered_songs = filter_songs_by_date(liked_songs)

    # Filter songs by the specified month and year
    period = f"{year}-{month}"
    songs_in_period = filtered_songs[
        filtered_songs["month_year"] == pd.Period(period, freq="M")
    ]

    if songs_in_period.empty:
        # Handle the case where no songs are found for the given month and year
        print("No songs found for the specified period.")
        return redirect(url_for("main.index"))

    # Create a playlist for the specified month and year
    playlist_name = f"Liked Songs - {period}"
    playlist_description = f"Songs liked in {period}"

    playlist_id = create_playlist(user_id, playlist_name, playlist_description)

    track_uris = songs_in_period["track_uri"].tolist()
    for i in range(0, len(track_uris), 100):
        add_tracks_to_playlist(playlist_id, track_uris[i : i + 100])

    return redirect(url_for("main.index"))
