import os
import uuid
import subprocess
from urllib.parse import urlparse

import requests

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "clipverse-secret-key"
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


RESOLUTIONS = {
    "8K": "7680:-2",
    "6K": "6144:-2",
    "5K": "5120:-2",
    "4K": "3840:-2",
    "3K": "2880:-2",
    "2K": "2560:-2",
    "2160p": "3840:-2",
    "1440p": "2560:-2",
    "1080p": "1920:-2",
    "720p": "1280:-2",
    "480p": "854:-2",
    "360p": "640:-2",
    "240p": "426:-2",
    "144p": "256:-2",
}


ALLOWED_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".mov",
    ".mkv",
    ".avi",
    ".m4v",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
}


def get_extension_from_url(media_url):
    try:
        path = urlparse(media_url).path
        extension = os.path.splitext(path)[1].lower()

        if extension in ALLOWED_EXTENSIONS:
            return extension

    except Exception:
        pass

    return ".mp4"


def download_media(media_url, destination):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/131 Safari/537.36"
        )
    }

    response = requests.get(
        media_url,
        headers=headers,
        stream=True,
        timeout=30,
        allow_redirects=True,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    if (
        not content_type.startswith("video/")
        and not content_type.startswith("audio/")
        and "oct
