import os
import uuid
import subprocess

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    abort
)

from werkzeug.utils import secure_filename


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# Maximum upload size: 500 MB
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)


# =========================================================
# ALLOWED FILES
# =========================================================

ALLOWED_EXTENSIONS = {
    "mp4",
    "mov",
    "mkv",
    "avi",
    "webm",
    "mp3",
    "wav",
    "m4a",
    "aac",
    "ogg"
}


# =========================================================
# QUALITY OPTIONS
# =========================================================

RESOLUTIONS = {
    "8K": "7680:4320",
    "6K": "6144:3456",
    "5K": "5120:2880",

    "4K": "3840:2160",
    "2160p": "3840:2160",

    "3K": "3200:1800",

    "2K": "2560:1440",
    "1440p": "2560:1440",

    "1080p": "1920:1080",
    "720p": "1280:720",
    "480p": "854:480",
   
