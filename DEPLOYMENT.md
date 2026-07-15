# Deployment Guide — Streamlit Community Cloud

## Overview

The web version of the Voice Doc Agent is designed to run on **Streamlit Community Cloud**, a free hosting platform that runs your Python app with minimal setup. This guide walks you through deploying it so you can share a link with others.

## Prerequisites

- A GitHub account (if you don't have one, create one at https://github.com/signup)
- Your GitHub repository containing this code
- Your OpenAI API key

## Steps

### 1. Push Your Code to GitHub

If you haven't already, initialize a git repo and push to GitHub:

```bash
cd /path/to/voice_doc_agent
git init
git add .
git commit -m "Initial commit: voice doc agent with streamlit web UI"
git remote add origin https://github.com/YOUR_USERNAME/voice_doc_agent.git
git branch -M main
git push -u origin main
```

**Note:** The `.gitignore` already includes `.streamlit/secrets.toml`, so your actual API key and password won't be committed. Good — keep it that way.

### 2. Sign Up for Streamlit Community Cloud

Go to https://share.streamlit.io and sign up with your GitHub account. Follow the onscreen prompts to authorize GitHub access.

### 3. Deploy the App

Once signed in to share.streamlit.io:

1. Click **"Create app"**
2. Select your GitHub repo and branch (`main`)
3. Set the main file path to `streamlit_app.py`
4. Click **"Deploy"**

Streamlit will build the environment and start the app. This takes ~2–3 minutes the first time. You'll see logs in real time.

### 4. Set Secrets in Streamlit Cloud

⚠️ **Never paste secrets into the repo.** Streamlit Cloud lets you manage secrets securely in the UI.

Once your app is deployed:

1. Click the **three-dot menu** (⋮) at the top right of the app
2. Select **"Settings"**
3. Go to the **"Secrets"** tab
4. Paste the following, filling in your values:

```toml
OPENAI_API_KEY = "sk-..."
APP_PASSWORD = "choose-a-strong-password"
CHAT_MODEL = "gpt-4o-mini"
TTS_VOICE = "alloy"
RELEVANCE_THRESHOLD = "0.5"
```

5. Click **"Save"** and the app will rerun with your secrets loaded

### 5. Share the Link

Your app is now live at: `https://yourappname.streamlit.app`

Share this link with others. They'll see the password gate first — give them the `APP_PASSWORD` you set above.

## Troubleshooting

**"OPENAI_API_KEY is not configured"**
- You forgot to set the secret in the Secrets tab. Go back to step 4.

**"No such information found in the document" even for obvious questions**
- The document may not have been indexed correctly. Try re-uploading it.
- If it's a PDF, confirm it's text-based (not a scanned image).

**App is slow to respond**
- Streamlit Community Cloud has limited CPU resources. This is normal for small audiences. For high-traffic deployments, see `FRONTEND_OPTIONS.md`.

**Audio playback not working**
- Ensure your browser allows audio. Check browser console (F12) for blocked requests.
- Try a different browser.

## Limits

Streamlit Community Cloud is free but has limits:

- **CPU:** Shared, small instances (OK for light use)
- **Concurrent users:** One Python process per app; fine for family/friends sharing, not for hundreds of simultaneous users
- **Inactivity:** Apps are paused after 7 days of no use (free tier)
- **API calls:** All API costs (OpenAI) are on your own account; Streamlit doesn't bill for compute but your API key will be charged

For high-traffic or high-availability deployments, see `FRONTEND_OPTIONS.md` for a FastAPI + React architecture.

## Local Development

To test the app locally before deploying:

```bash
. venv/bin/activate
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and add your real API key and password
streamlit run streamlit_app.py
```

Then visit http://localhost:8501 in your browser.

## Updates

To push updates to your deployed app:

1. Make changes locally
2. Commit and push to GitHub: `git push origin main`
3. Streamlit Cloud auto-redeploys within seconds

(Secrets remain unchanged unless you update them in the Settings tab.)

## Support

- Streamlit docs: https://docs.streamlit.io
- Streamlit Community: https://discuss.streamlit.io
- This project: Check README.md for the full architecture
