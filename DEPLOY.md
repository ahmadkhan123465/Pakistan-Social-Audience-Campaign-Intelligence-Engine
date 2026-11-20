# Free Cloud Deployment Guide

Your **Campaign Intelligence** app is pre-configured with `wsgi.py`, `render.yaml`, `Procfile`, and `Dockerfile` so you can deploy it **100% free** with automatic HTTPS (which also enables one-tap **Install App** on Android & iPhone).

---

## Option 1: Render.com (Easiest — Free, Auto-Deploys from GitHub)

1. Push the contents of this folder (`Pakistan-Social-Audience-Campaign-Intelligence-Engine-main`) to a GitHub repository.
2. Go to **https://render.com** and sign in with GitHub (no credit card required for the Free tier).
3. Click **New + → Blueprint** (or **New + → Web Service**).
4. Select your GitHub repository — Render automatically detects `render.yaml` with:
   - **Plan:** Free
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
   - **Health Check:** `/healthz`
   - **Auto-generated `SECRET_KEY`**
5. Click **Apply / Deploy Web Service**. In ~2 minutes you will get a live HTTPS URL like `https://pakistan-campaign-intelligence.onrender.com`.

> Note: Render Free tier sleeps after 15 minutes of inactivity (wakes in ~30s on next visit) and resets ephemeral files (`data/auth.db`) on redeploy (the seeded `admin` and `analyst` accounts are recreated automatically).

---

## Option 2: PythonAnywhere (Free + Persistent User Accounts)

Best free choice if you want newly registered users and privacy consent records in `data/auth.db` to **persist permanently** without resetting:

1. Create a free account at **https://www.pythonanywhere.com**.
2. Open a **Bash** console and clone/upload your repo, then install dependencies:
   ```bash
   pip install --user -r requirements.txt
   ```
3. Go to the **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.12**.
4. Open the **WSGI configuration file** and replace its contents with:
   ```python
   import os, sys
   path = '/home/<your-username>/pakistan-audience-intel'
   if path not in sys.path:
       sys.path.insert(0, path)
   os.environ['COOKIE_SECURE'] = '1'
   from wsgi import application
   ```
5. Click **Reload** — your app is live at `https://<your-username>.pythonanywhere.com`!

---

## Option 3: Hugging Face Spaces (Free 16 GB RAM Docker Tier — No Git Required!)

1. Create a free Write token at **https://huggingface.co/settings/tokens** (select **Write** access).
2. Run the 1-command deployer right from PowerShell (no Git or Git LFS needed!):
   ```powershell
   cd c:\Users\me\Desktop\Pakistan-Social-Audience-Campaign-Intelligence-Engine-main\Pakistan-Social-Audience-Campaign-Intelligence-Engine-main
   py deploy_hf.py
   ```
3. Paste your token and choose a Space name (e.g. `campaign-intelligence`). It automatically creates a free **Docker** Space, uploads your app + database, and prints your live HTTPS URL (both the Hugging Face Space page and your direct mobile-installable `https://<user>-<space>.hf.space` URL).

---

## Default Sign-In Accounts
- **Admin:** `admin` / `Admin@1234`
- **Analyst:** `analyst` / `Analyst@1234`
