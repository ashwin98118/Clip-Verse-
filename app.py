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


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "clipverse-secret-key"
)

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "outputs"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


# =========================================================
# VIDEO QUALITY OPTIONS
# =========================================================

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


# =========================================================
# GET FILE EXTENSION FROM URL
# =========================================================

def get_extension_from_url(media_url):

    try:

        path = urlparse(
            media_url
        ).path

        extension = os.path.splitext(
            path
        )[1].lower()

        allowed_extensions = {
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

        if extension in allowed_extensions:
            return extension

    except Exception:
        pass

    return ".mp4"


# =========================================================
# DOWNLOAD DIRECT MEDIA URL
# =========================================================

def download_media(
    media_url,
    destination
):

    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    }

    response = requests.get(
        media_url,
        headers=headers,
        stream=True,
        timeout=60,
        allow_redirects=True
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    # Only allow actual media responses.
    valid_media = (
        content_type.startswith("video/")
        or content_type.startswith("audio/")
        or "octet-stream" in content_type
    )

    if not valid_media:

        raise ValueError(
            "This URL does not point directly to a "
            "video or audio file."
        )

    # Maximum input size: 500 MB
    max_size = 500 * 1024 * 1024

    total_size = 0

    with open(
        destination,
        "wb"
    ) as output_file:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if not chunk:
                continue

            total_size += len(chunk)

            if total_size > max_size:

                raise ValueError(
                    "File is too large. "
                    "Maximum allowed size is 500 MB."
                )

            output_file.write(
                chunk
            )


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# CONVERT / DOWNLOAD
# =========================================================

@app.route(
    "/convert",
    methods=["POST"]
)
def convert():

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

    media_url = request.form.get(
        "url",
        ""
    ).strip()

    output_format = request.form.get(
        "format",
        "mp4"
    ).lower()

    quality = request.form.get(
        "quality",
        "1080p"
    )


    # -----------------------------------------------------
    # VALIDATE URL
    # -----------------------------------------------------

    if not media_url:

        flash(
            "Please paste a media URL.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    parsed_url = urlparse(
        media_url
    )


    if parsed_url.scheme not in {
        "http",
        "https"
    }:

        flash(
            "Please enter a valid HTTP or HTTPS URL.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    # -----------------------------------------------------
    # VALIDATE FORMAT
    # -----------------------------------------------------

    if output_format not in {
        "mp4",
        "mp3"
    }:

        flash(
            "Invalid format selected.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    # -----------------------------------------------------
    # VALIDATE QUALITY
    # -----------------------------------------------------

    if quality not in RESOLUTIONS:

        quality = "1080p"


    # -----------------------------------------------------
    # CREATE UNIQUE FILE ID
    # -----------------------------------------------------

    unique_id = str(
        uuid.uuid4()
    )


    # -----------------------------------------------------
    # INPUT FILE
    # -----------------------------------------------------

    extension = get_extension_from_url(
        media_url
    )

    input_filename = (
        unique_id + extension
    )

    input_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        input_filename
    )


    # -----------------------------------------------------
    # OUTPUT FILE
    # -----------------------------------------------------

    if output_format == "mp3":

        output_filename = (
            unique_id + ".mp3"
        )

    else:

        output_filename = (
            unique_id + ".mp4"
        )


    output_path = os.path.join(
        app.config["OUTPUT_FOLDER"],
        output_filename
    )


    # =====================================================
    # PROCESS
    # =====================================================

    try:

        # -------------------------------------------------
        # DOWNLOAD INPUT MEDIA
        # -------------------------------------------------

        download_media(
            media_url,
            input_path
        )


        # =================================================
        # MP3 CONVERSION
        # =================================================

        if output_format == "mp3":

            command = [
                "ffmpeg",

                "-y",

                "-i",
                input_path,

                "-vn",

                "-codec:a",
                "libmp3lame",

                "-q:a",
                "2",

                output_path
            ]


        # =================================================
        # MP4 CONVERSION
        # =================================================

        else:

            resolution = RESOLUTIONS[
                quality
            ]

            command = [
                "ffmpeg",

                "-y",

                "-i",
                input_path,

                "-vf",
                "scale=" + resolution,

                "-c:v",
                "libx264",

                "-preset",
                "medium",

                "-crf",
                "23",

                "-c:a",
                "aac",

                "-b:a",
                "192k",

                "-movflags",
                "+faststart",

                output_path
            ]


        # -------------------------------------------------
        # RUN FFMPEG
        # -------------------------------------------------

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )


        # -------------------------------------------------
        # CHECK FFMPEG
        # -------------------------------------------------

        if result.returncode != 0:

            print(
                "================================="
            )

            print(
                "FFMPEG ERROR"
            )

            print(
                result.stderr
            )

            print(
                "================================="
            )

            raise RuntimeError(
                "Media conversion failed."
            )


        # -------------------------------------------------
        # CHECK OUTPUT
        # -------------------------------------------------

        if not os.path.exists(
            output_path
        ):

            raise RuntimeError(
                "Output file was not created."
            )


        # -------------------------------------------------
        # SUCCESS PAGE
        # -------------------------------------------------

        return render_template(
            "result.html",

            filename=output_filename,

            original_name="Media from URL",

            output_format=output_format.upper(),

            quality=quality
        )


    # =====================================================
    # DOWNLOAD ERROR
    # =====================================================

    except requests.RequestException as error:

        print(
            "DOWNLOAD ERROR:",
            error
        )

        flash(
            "Unable to download this media URL. "
            "Make sure it is a direct media URL "
            "that you are authorized to download.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    # =====================================================
    # GENERAL ERROR
    # =====================================================

    except Exception as error:

        print(
            "CONVERSION ERROR:",
            error
        )

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("home")
        )


    # =====================================================
    # CLEAN TEMPORARY INPUT
    # =====================================================

    finally:

        if os.path.exists(
            input_path
        ):

            try:

                os.remove(
                    input_path
                )

            except OSError:

                pass


# =========================================================
# DOWNLOAD GENERATED FILE
# =========================================================

@app.route(
    "/download/<filename>"
)
def download(filename):

    return send_from_directory(
        app.config["OUTPUT_FOLDER"],
        filename,
        as_attachment=True
    )


# =========================================================
# DELETE GENERATED FILE
# =========================================================

@app.route(
    "/delete/<filename>"
)
def delete_file(filename):

    file_path = os.path.join(
        app.config["OUTPUT_FOLDER"],
        filename
    )


    if os.path.exists(
        file_path
    ):

        try:

            os.remove(
                file_path

            )

        except OSError:

            pass


    flash(
        "File deleted from server.",
        "success"
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/health"
)
def health():

    return "ClipVerse is running!"


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
        )
