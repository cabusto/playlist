import pytest
from unittest.mock import patch
from datetime import datetime
import pandas as pd
from app.spotify import (
    get_liked_songs,
    filter_songs_by_date,
    create_playlist,
    add_tracks_to_playlist,
)


@patch("app.spotify.sp")
def test_get_liked_songs(mock_sp):
    mock_sp.current_user_saved_tracks.return_value = {
        "items": [
            {
                "added_at": "2023-08-01T00:00:00Z",
                "track": {
                    "name": "Song1",
                    "artists": [{"name": "Artist1"}],
                    "album": {"name": "Album1"},
                    "uri": "uri1",
                },
            }
        ],
        "next": None,
    }

    liked_songs = get_liked_songs()
    assert len(liked_songs) == 1
    assert liked_songs[0]["track"]["name"] == "Song1"


def test_filter_songs_by_date():
    songs = [
        {
            "added_at": "2023-08-01T00:00:00Z",
            "track": {
                "name": "Song1",
                "artists": [{"name": "Artist1"}],
                "album": {"name": "Album1"},
                "uri": "uri1",
            },
        }
    ]

    filtered_songs = filter_songs_by_date(songs)
    assert "month_year" in filtered_songs.columns
    assert filtered_songs.iloc[0]["track_name"] == "Song1"
    assert filtered_songs.iloc[0]["month_year"] == pd.Period("2023-08", freq="M")


@patch("app.spotify.sp")
def test_create_playlist(mock_sp):
    mock_sp.user_playlist_create.return_value = {"id": "playlist_id"}
    user_id = "user_id"
    playlist_name = "Test Playlist"
    playlist_description = "Test Description"

    playlist_id = create_playlist(user_id, playlist_name, playlist_description)
    assert playlist_id == "playlist_id"


@patch("app.spotify.sp")
def test_add_tracks_to_playlist(mock_sp):
    playlist_id = "playlist_id"
    track_uris = ["uri1", "uri2"]

    add_tracks_to_playlist(playlist_id, track_uris)
    mock_sp.playlist_add_items.assert_called_once_with(playlist_id, track_uris)
