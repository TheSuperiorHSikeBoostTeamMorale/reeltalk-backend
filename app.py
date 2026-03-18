import os
import tempfile
import subprocess
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# ---------------------------------------------------------------------------
# Transcription endpoint
# ---------------------------------------------------------------------------

@app.route("/transcribe", methods=["POST"])
def transcribe():
    data = request.get_json(force=True, silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"success": False, "error": "Missing 'url' in request body"}), 400

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return jsonify({"success": False, "error": "OPENAI_API_KEY not set"}), 500

    try:
        transcript = _transcribe_url(url, api_key)
        return jsonify({"success": True, "transcript": transcript})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _transcribe_url(url: str, api_key: str) -> str:
    client = OpenAI(api_key=api_key)

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.mp3")

        subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "5",
                "--output", audio_path,
                "--quiet",
                url,
            ],
            check=True,
            timeout=120,
        )

        if not os.path.exists(audio_path):
            # yt-dlp may append the extension itself
            candidates = [
                os.path.join(tmpdir, f)
                for f in os.listdir(tmpdir)
                if f.startswith("audio")
            ]
            if not candidates:
                raise RuntimeError("yt-dlp produced no output file")
            audio_path = candidates[0]

        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en",
            )

        return result.text.strip()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
