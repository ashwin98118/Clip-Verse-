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
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clipverse-secret-key")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


# Supported video resolutions
RESOLUTIONS = {
    "8K": "7680:-2",
    "6K": "6144:-2",
    "5K": "5120:-2",
    "4K": "3840:-2",
    "2160p": "3840:-2",
    "3K": "2880:-2",
    "2K": "2560:-2",
    "1440p": "2560:-2",
    "1080p": "1920:-2",
    "720p": "1280:-2",
    "480p": "854:-2",
    "360p": "640:-2",
    "240p": "426:-2",
    "144p": "256:-2",
}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():

    if "file" not in request.files:
        flash("Please select a media file.", "error")
        return redirect(url_for("home"))

    file = request.files["file"]

    if file.filename == "":
        flash("Please select a media file.", "error")
        return redirect(url_for("home"))

    output_format = request.form.get("format", "mp4").lower()
    quality = request.form.get("quality", "1080p")

    # Create safe unique filenames
    unique_id = str(uuid.uuid4())

    original_name = file.filename

    # Get original extension
    extension = os.path.splitext(original_name)[1]

    if not extension:
        extension = ".mp4"

    input_filename = unique_id + extension
    input_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        input_filename
    )

    file.save(input_path)

    try:

        if output_format == "mp3":

            output_filename = unique_id + ".mp3"

            output_path = os.path.join(
                app.config["OUTPUT_FOLDER"],
                output_filename
            )

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

            output_filename = unique_id + ".mp4"

            output_path = os.path.join(
                app.config["OUTPUT_FOLDER"],
                output_filename
            )

            resolution = RESOLUTIONS.get(
                quality,
                "1920:-2"
            )

            command = [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-vf",
                f"scale={resolution}",
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
                output_path
            ]

        # Run FFmpeg
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )

    except subprocess.CalledProcessError as error:

        print("FFmpeg error:", error.stderr)

        flash(
            "Conversion failed. Please try another media file.",
            "error"
        )

        return redirect(url_for("home"))

    finally:

        # Remove uploaded original file
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except OSError:
                pass

    return render_template(
        "result.html",
        filename=output_filename,
        original_name=original_name,
        output_format=output_format.upper(),
        quality=quality
    )


@app.route("/download/<filename>")
def download(filename):

    return send_from_directory(
        app.config["OUTPUT_FOLDER"],
        filename,
        as_attachment=True
    )


@app.route("/delete/<filename>")
def delete_file(filename):

    file_path = os.path.join(
        app.config["OUTPUT_FOLDER"],
        filename
    )

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    flash("File deleted from the server.", "success")

    return redirect(url_for("home"))


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
            )
