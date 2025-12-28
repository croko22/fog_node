#!/bin/bash
set -e

# =============================================================================
# FogNode Audiobooks - Automated GCP Deployment with Pulumi
# =============================================================================

echo "🚀 Starting FogNode deployment to GCP..."

# Check prerequisites
if ! command -v pulumi &> /dev/null; then
    echo "❌ Pulumi CLI not found. Install it first:"
    echo "   curl -fsSL https://get.pulumi.com | sh"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install it first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Authenticate with gcloud (if needed)
echo "🔐 Checking GCP authentication..."
if ! gcloud auth application-default print-access-token &> /dev/null; then
    echo "📝 Please authenticate with GCP:"
    gcloud auth application-default login
fi

# Configure Docker to use gcloud credentials
echo "🐳 Configuring Docker for Artifact Registry..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# Navigate to infrastructure directory
cd "$(dirname "$0")/../infra"

# Install Pulumi dependencies
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing Pulumi dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

# Select/create Pulumi stack
STACK_NAME="${PULUMI_STACK:-dev}"
echo "📋 Using Pulumi stack: $STACK_NAME"

if ! pulumi stack select $STACK_NAME 2>/dev/null; then
    echo "🆕 Creating new stack: $STACK_NAME"
    pulumi stack init $STACK_NAME
fi

# Preview changes
echo ""
echo "👀 Previewing infrastructure changes..."
pulumi preview

# Ask for confirmation
read -p "🤔 Do you want to deploy these changes? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 0
fi

# Deploy infrastructure
echo ""
echo "🏗️  Deploying infrastructure..."
pulumi up --yes

# Get outputs
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Stack Outputs:"
pulumi stack output --json | python3 -m json.tool

# Display service URL
SERVICE_URL=$(pulumi stack output service_url 2>/dev/null || echo "Not available yet")
if [ "$SERVICE_URL" != "Not available yet" ]; then
    echo ""
    echo "🌐 Your FogNode API is live at:"
    echo "   $SERVICE_URL"
    echo ""
    echo "🧪 Test it with:"
    echo "   curl ${SERVICE_URL}/api/v1/status"
fi

deactivate
