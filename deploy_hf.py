#!/usr/bin/env python3
"""One-command free deployment to Hugging Face Spaces (Docker SDK, 16 GB RAM free).

Usage:
    py deploy_hf.py
    py deploy_hf.py --repo your-username/campaign-intelligence
"""
from __future__ import annotations

import argparse
import getpass
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

IGNORE_PATTERNS = [
    ".git/**",
    ".venv/**",
    "venv/**",
    "**/__pycache__/**",
    "*.pyc",
    ".pytest_cache/**",
    ".vscode/**",
    "data/auth.db",
    "data/.secret_key",
    "docs/**",
    "*.docx",
    "*.log",
    "capture_screenshots.ps1",
    "generate_db_doc.py",
    "deploy_hf.py",
]


def ensure_hf_hub():
    try:
        import huggingface_hub  # noqa: F401
    except ImportError:
        print("Installing huggingface_hub ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub"])


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy Campaign Intelligence Engine to Hugging Face Spaces (free).")
    ap.add_argument("--repo", default="kashiif/Campaign_Engine", help="Target Space repo ID (default: kashiif/Campaign_Engine)")
    ap.add_argument("--token", help="Hugging Face Write token (or set HF_TOKEN env var)")
    ap.add_argument("--private", action="store_true", help="Create the Space as private")
    args = ap.parse_args()

    ensure_hf_hub()
    from huggingface_hub import HfApi, get_token

    token = (args.token or os.environ.get("HF_TOKEN") or get_token() or "").strip()
    if not token:
        print("\nGet a free Write token at: https://huggingface.co/settings/tokens")
        token = getpass.getpass("Paste your Hugging Face Write Token (hidden): ").strip()
    if not token:
        print("Error: Hugging Face token is required.")
        return 1

    api = HfApi(token=token)
    me = api.whoami()
    username = me["name"]
    print(f"Authenticated as Hugging Face user: {username}")

    repo_id = (args.repo or "kashiif/Campaign_Engine").strip()
    if "/" not in repo_id:
        repo_id = f"{username}/{repo_id}"

    print(f"\n1/2 Creating or reusing Docker Space: {repo_id} ...")
    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="docker",
        private=args.private,
        exist_ok=True,
    )

    print("2/2 Uploading project files (handles campaign.db & model via LFS automatically) ...")
    api.upload_folder(
        folder_path=str(ROOT),
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=IGNORE_PATTERNS,
        commit_message="Deploy Campaign Intelligence Engine (Auth + CAPTCHA + Privacy Consent + Mobile PWA)",
    )

    owner, space_name = repo_id.split("/", 1)
    direct_slug = f"{owner}-{space_name}".lower().replace("_", "-")
    print("\nDeployment uploaded successfully! Hugging Face is building your Docker image now (~2-3 min).")
    print(f"  Space page        : https://huggingface.co/spaces/{repo_id}")
    print(f"  Direct Mobile URL : https://{direct_slug}.hf.space")
    print("  Demo login        : admin / Admin@1234  or  analyst / Analyst@1234")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
