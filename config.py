import os


class Config:
    SECRET_KEY = "your_secret_key"
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")


# 12143694436 - mine
