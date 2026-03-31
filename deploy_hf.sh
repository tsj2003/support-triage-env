#!/bin/bash
# Deploy to Hugging Face Spaces

set -e

echo "🚀 Hugging Face Spaces Deployment Script"
echo "=========================================="

# Check if huggingface-cli is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "❌ huggingface-cli not found. Installing..."
    pip install huggingface_hub
fi

# Check login status
echo ""
echo "🔑 Checking Hugging Face authentication..."
huggingface-cli whoami || (echo "❌ Not logged in. Run: huggingface-cli login" && exit 1)

# Get username
HF_USER=$(huggingface-cli whoami | head -1 | cut -d' ' -f2)
echo "✅ Logged in as: $HF_USER"

# Space name
SPACE_NAME="${1:-support-triage-env}"
echo ""
echo "📦 Space name: $SPACE_NAME"
echo "URL will be: https://huggingface.co/spaces/$HF_USER/$SPACE_NAME"

# Create Space if it doesn't exist
echo ""
echo "🔧 Creating Space (if needed)..."
huggingface-cli repo create "$SPACE_NAME" --type space --sdk docker 2>/dev/null || echo "Space already exists or creation skipped"

# Add remote
echo ""
echo "🔗 Setting up Git remote..."
if ! git remote | grep -q "space"; then
    git remote add space "https://huggingface.co/spaces/$HF_USER/$SPACE_NAME"
fi

# Commit any changes
echo ""
echo "💾 Committing changes..."
git add -A
git commit -m "Pre-deployment commit $(date +%Y%m%d_%H%M%S)" || echo "No changes to commit"

# Push to Space
echo ""
echo "📤 Pushing to Hugging Face Spaces..."
echo "This may take 2-3 minutes for the build..."
git push space main --force

# Wait for build
echo ""
echo "⏳ Waiting for build to start..."
sleep 10

# Check status
echo ""
echo "🔍 Checking deployment status..."
HF_URL="https://huggingface.co/spaces/$HF_USER/$SPACE_NAME"
echo "Space URL: $HF_URL"
echo ""
echo "Build logs: $HF_URL/logs"
echo ""
echo "✅ Deployment initiated!"
echo ""
echo "To check if it's running:"
echo "  curl https://$HF_USER-$SPACE_NAME.hf.space/health"
