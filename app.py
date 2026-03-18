import os
import tempfile
import subprocess
import json
from flask import Flask, request, jsonify

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

    try:
        transcript = _transcribe_url(url)
        return jsonify({"success": True, "transcript": transcript})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _transcribe_url(url: str) -> str:
    """Download audio with yt-dlp, transcribe with Whisper, return text."""
    import whisper  # imported lazily so health check starts fast

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.%(ext)s")
        out_template = os.path.join(tmpdir, "audio")

        # Download best audio-only stream
        subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "5",   # ~128 kbps — good enough for speech
                "--output", audio_path,
                "--quiet",
                url,
            ],
            check=True,
            timeout=120,
        )

        # Find the downloaded file (yt-dlp fills in the extension)
        mp3_path = out_template + ".mp3"
        if not os.path.exists(mp3_path):
            # Fallback: find any audio file in tmpdir
            candidates = [
                os.path.join(tmpdir, f)
                for f in os.listdir(tmpdir)
                if f.startswith("audio.")
            ]
            if not candidates:
                raise RuntimeError("yt-dlp produced no output file")
            mp3_path = candidates[0]

        # Transcribe with Whisper (base model — fast, good accuracy for speech)
        model = whisper.load_model("base")
        result = model.transcribe(mp3_path, language="en", fp16=False)
        text = result.get("text", "").strip()

        if not text:
            raise RuntimeError("Whisper returned an empty transcript")

        return text

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
