# Reel Talk — Transcription Backend

Flask API that downloads social-media video audio with **yt-dlp** and transcribes it with **OpenAI Whisper** (base model). Deployed on [Railway](https://railway.app).

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"status":"ok"}` — used by Railway health checks |
| POST | `/transcribe` | Accepts `{"url":"..."}`, returns `{"success":true,"transcript":"..."}` |

## Deploy to Railway

### 1. Install Railway CLI (optional but handy)
```bash
npm install -g @railway/cli
railway login
```

### 2. Create a new project
Go to [railway.app](https://railway.app), click **New Project → Deploy from GitHub repo**, and connect this repo (or the `backend/` sub-folder).

Alternatively with the CLI:
```bash
cd backend/
railway init          # creates a new Railway project
railway up            # deploys
```

### 3. Note the public URL
Railway generates a URL like `https://reeltalk-backend-production.up.railway.app`.
Copy it into `ReelTalk/Config.swift`:

```swift
static let backendURL = "https://reeltalk-backend-production.up.railway.app"
```

### 4. Verify
```bash
curl https://<your-url>/health
# {"status":"ok"}

curl -X POST https://<your-url>/transcribe \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.tiktok.com/@user/video/123"}'
# {"success":true,"transcript":"..."}
```

## Local development

```bash
cd backend/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The server listens on port 8080 by default (set `PORT` env var to override).

## Notes

- **yt-dlp** is updated frequently; pin the version in `requirements.txt` and update when platforms change their APIs.
- Whisper **base** model (~140 MB) loads on first request. Subsequent requests are faster.
- For production, consider caching the loaded Whisper model as a module-level singleton (already done in `app.py`).
- Railway's free tier may cold-start; first request after idle can take ~30 s. The iOS app has a 30-second timeout for the backend call.
