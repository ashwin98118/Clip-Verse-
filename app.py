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


def get_extension_from_url(media_url):

    try:
        path = urlparse(
            media_url
        ).path

        extension = os.path.splitext(
            path
        )[1].lower()

        allowed = {
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

        if extension in allowed:
            return extension

    except Exception:
        pass

    return ".mp4"


def download_media(
    media_url,
    destination
):

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    response = requests.get(
        media_url,
        headers=headers,
        stream=True,
        timeout=30,
        allow_redirects=True
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    valid_media = (
        content_type.startswith("video/")
        or content_type.startswith("audio/")
        or "octet-stream" in content_type
    )

    if not valid_media:
        raise ValueError(
            "This is not a direct media URL."
        )

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
                    "Maximum size is 500 MB."
                )

            output_file.write(chunk)


@app.route("/")
def home():

    return render_template(
        "index.html"
    )


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

    if output_format not in {
        "mp4",
        "mp3"
    }:

        flash(
            "Invalid format.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    if quality not in RESOLUTIONS:

        quality = "1080p"

    unique_id = str(
        uuid.uuid4()
    )

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

    try:

        download_media(
            media_url,
            input_path
        )

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

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            print(
                "FFmpeg ERROR:"
            )

            print(
                result.stderr
            )

            raise RuntimeError(
                "Media conversion failed."
            )

        if not os.path.exists(
            output_path
        ):

            raise RuntimeError(
                "Output file was not created."
            )

        return render_template(
            "result.html",
            filename=output_filename,
            original_name="Media from URL",
            output_format=output_format.upper(),
            quality=quality
        )

    except requests.RequestException as error:

        print(
            "DOWNLOAD ERROR:",
            error
        )

        flash(
            "Unable to download this media URL. "
            "Use a direct media URL that you "
            "are authorized to download.",
            "error"
        )

        return redirect(
            url_for("home")
        )

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


@app.route(
    "/download/<filename>"
)
def download(filename):

    return send_from_directory(
        app.config["OUTPUT_FOLDER"],
        filename,
        as_attachment=True
    )


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
        "File deleted from the server.",
        "success"
    )

    return redirect(
        url_for("home")
    )


@app.route("/health")
def health():

    return "ClipVerse is running!"


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
