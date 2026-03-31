#!/usr/bin/env python3
"""Deploy to Hugging Face Spaces using Python API."""

import os
import subprocess
from pathlib import Path

try:
    from huggingface_hub import HfApi, create_repo, upload_folder
except ImportError:
    print("Installing huggingface_hub...")
    subprocess.run(["pip", "install", "huggingface_hub", "-q"])
    from huggingface_hub import HfApi, create_repo, upload_folder


def deploy():
    """Deploy to Hugging Face Spaces."""
    print("🚀 Deploying to Hugging Face Spaces")
    print("=" * 50)
    
    # Get API token from env or login
    token = os.getenv("HF_TOKEN")
    if not token:
        print("\n❌ HF_TOKEN not found in environment")
        print("Please set it with: export HF_TOKEN='your_token'")
        print("Or login with: python -c \"from huggingface_hub import login; login()\"")
        return False
    
    api = HfApi(token=token)
    
    # Get username
    user_info = api.whoami()
    username = user_info.get("name", user_info.get("fullname", "unknown"))
    print(f"✅ Logged in as: {username}")
    
    # Space config
    space_name = os.getenv("SPACE_NAME", "support-triage-env")
    repo_id = f"{username}/{space_name}"
    
    print(f"\n📦 Space: {space_name}")
    print(f"🌐 URL: https://huggingface.co/spaces/{repo_id}")
    
    # Create space if needed
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="docker",
            token=token,
            exist_ok=True,
        )
        print(f"✅ Space ready: {repo_id}")
    except Exception as e:
        print(f"⚠️ Space creation: {e}")
    
    # Upload files
    print("\n📤 Uploading files...")
    upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        token=token,
        ignore_patterns=[
            "*.pyc", "__pycache__", ".git", ".pytest_cache",
            "*.egg-info", ".env", "venv", ".venv"
        ],
    )
    
    print("\n✅ Deployment complete!")
    print(f"\n🌐 Your Space: https://huggingface.co/spaces/{repo_id}")
    print(f"🔍 Build logs: https://huggingface.co/spaces/{repo_id}/logs")
    print("\n⏳ Wait 2-3 minutes for build, then test:")
    print(f"   curl https://{username}-{space_name}.hf.space/health")
    
    return True


if __name__ == "__main__":
    deploy()
