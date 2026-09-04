import os
import uuid
import subprocess
import shutil
from urllib.parse import urlparse

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
# CLIPVERSE APP
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "clipverse-secret-key"
)

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "outputs"
)

TEMP_FOLDER = os.path.join(
    BASE_DIR,
    "temp"
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)

os.makedirs(
    TEMP_FOLDER,
    exist_ok=True
)

app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["TEMP_FOLDER"] = TEMP_FOLDER


# =========================================================
# QUALITY OPTIONS
# =========================================================

RESOLUTIONS = {
    "8K": 4320,
    "6K": 2880,
    "5K": 2560,
    "4K": 2160,
    "3K": 1620,
    "2K": 1440,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
    "360p": 360,
    "240p": 240,
    "144p": 144,
}


# =========================================================
# ALLOWED URL CHECK
# =========================================================

def valid_url(media_url):

    try:

        parsed = urlparse(
            media_url
        )

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )

    except Exception:

        return False


# =========================================================
# CHECK FFMPEG
# =========================================================

def ffmpeg_available():

    return shutil.which(
        "ffmpeg"
    ) is not None


# =========================================================
# CHECK MEDIA DOWNLOADER
# =========================================================

def downloader_available():

    return shutil.which(
        "yt-dlp"
    ) is not None


# =========================================================
# GET FILE INFORMATION
# =========================================================

def get_media_info(
    media_url
):

    command = [
        "yt-dlp",
        "--dump-single-json",
        "--no-playlist",
        "--skip-download",
        "--no-warnings",
        "--",
        media_url
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:

        raise RuntimeError(
            result.stderr.strip()
            or "Unable to read this media URL."
        )

    return result.stdout


# =========================================================
# DOWNLOAD MEDIA
# =========================================================

def download_media(
    media_url,
    output_template
):

    command = [
        "yt-dlp",

        "--no-playlist",

        "--no-warnings",

        "--restrict-filenames",

        "-o",
        output_template,

        "--",
        media_url
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=600
    )

    if result.returncode != 0:

        print(
            "========================================"
        )

        print(
            "YT-DLP DOWNLOAD ERROR"
        )

        print(
            result.stderr
        )

        print(
            "========================================"
        )

        raise RuntimeError(
            "Unable to download this media URL."
        )


# =========================================================
# FIND DOWNLOADED FILE
# =========================================================

def find_downloaded_file(
    folder,
    unique_id
):

    files = os.listdir(
        folder
    )

    matching_files = []

    for filename in files:

        if filename.startswith(
            unique_id
        ):

            full_path = os.path.join(
                folder,
                filename
            )

            if os.path.isfile(
                full_path
            ):

                matching_files.append(
                    full_path
                )

    if not matching_files:

        return None

    return matching_files[0]


# =========================================================
# CONVERT TO MP3
# =========================================================

def convert_to_mp3(
    input_file,
    output_file
):

    command = [
        "ffmpeg",

        "-y",

        "-i",
        input_file,

        "-vn",

        "-codec:a",
        "libmp3lame",

        "-q:a",
        "2",

        output_file
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=600
    )

    if result.returncode != 0:

        print(
            "FFMPEG MP3 ERROR:"
        )

        print(
            result.stderr
        )

        raise RuntimeError(
            "MP3 conversion failed."
        )


# =========================================================
# CONVERT TO MP4
# =========================================================

def convert_to_mp4(
    input_file,
    output_file,
    quality
):

    height = RESOLUTIONS.get(
        quality,
        1080
    )

    # Let FFmpeg scale while preserving
    # aspect ratio.

    video_filter = (
        f"scale=-2:min({height}\\,ih)"
    )

    command = [
        "ffmpeg",

        "-y",

        "-i",
        input_file,

        "-vf",
        video_filter,

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

        output_file
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=900
    )

    if result.returncode != 0:

        print(
            "========================================"
        )

        print(
            "FFMPEG MP4 ERROR"
        )

        print(
            result.stderr
        )

        print(
            "========================================"
        )

        raise RuntimeError(
            "MP4 conversion failed."
        )


# =========================================================
# HOME
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
    # URL VALIDATION
    # -----------------------------------------------------

    if not media_url:

        flash(
            "Please paste a video or media URL.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    if not valid_url(
        media_url
    ):

        flash(
            "Please enter a valid HTTP or HTTPS URL.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    # -----------------------------------------------------
    # FORMAT VALIDATION
    # -----------------------------------------------------

    if output_format not in (
        "mp4",
        "mp3"
    ):

        flash(
            "Invalid format selected.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    # -----------------------------------------------------
    # QUALITY VALIDATION
    # -----------------------------------------------------

    if quality not in RESOLUTIONS:

        quality = "1080p"


    # -----------------------------------------------------
    # CHECK DEPENDENCIES
    # -----------------------------------------------------

    if not downloader_available():

        flash(
            "Media downloader is not installed on the server.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    if not ffmpeg_available():

        flash(
            "FFmpeg is not installed on the server.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    # -----------------------------------------------------
    # UNIQUE ID
    # -----------------------------------------------------

    unique_id = str(
        uuid.uuid4()
    )


    input_template = os.path.join(
        app.config["TEMP_FOLDER"],
        unique_id + ".%(ext)s"
    )


    downloaded_file = None


    try:

        # =================================================
        # DOWNLOAD SOURCE
        # =================================================

        download_media(
            media_url,
            input_template
        )


        # =================================================
        # FIND DOWNLOADED FILE
        # =================================================

        downloaded_file = find_downloaded_file(
            app.config["TEMP_FOLDER"],
            unique_id
        )


        if not downloaded_file:

            raise RuntimeError(
                "The media file could not be found "
                "after downloading."
            )


        # =================================================
        # CREATE OUTPUT NAME
        # =================================================

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


        # =================================================
        # MP3
        # =================================================

        if output_format == "mp3":

            convert_to_mp3(
                downloaded_file,
                output_path
            )


        # =================================================
        # MP4
        # =================================================

        else:

            convert_to_mp4(
                downloaded_file,
                output_path,
                quality
            )


        # =================================================
        # CHECK OUTPUT
        # =================================================

        if not os.path.exists(
            output_path
        ):

            raise RuntimeError(
                "Output file was not created."
            )


        if os.path.getsize(
            output_path
        ) == 0:

            raise RuntimeError(
                "The output file is empty."
            )


        # =================================================
        # SUCCESS
        # =================================================

        return render_template(
            "result.html",

            filename=output_filename,

            original_name="ClipVerse Media",

            output_format=output_format.upper(),

            quality=quality
        )


    except subprocess.TimeoutExpired:

        flash(
            "The conversion took too long. "
            "Please try a shorter video.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    except Exception as error:

        print(
            "========================================"
        )

        print(
            "CLIPVERSE ERROR:"
        )

        print(
            str(error)
        )

        print(
            "========================================"
        )

        flash(
            "Unable to process this URL. "
            "Make sure the media is publicly accessible "
            "and that you are authorized to download it.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    finally:

        # -------------------------------------------------
        # DELETE TEMPORARY DOWNLOADED SOURCE
        # -------------------------------------------------

        if downloaded_file:

            try:

                if os.path.exists(
                    downloaded_file
                ):

                    os.remove(
                        downloaded_file
                    )

            except OSError:

                pass


# =========================================================
# DOWNLOAD RESULT
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
# DELETE RESULT
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
# SERVER START
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
