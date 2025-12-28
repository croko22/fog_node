#!/bin/bash
set -e

# =============================================================================
# FogNode Audiobooks - Destroy Infrastructure
# =============================================================================

echo "⚠️  WARNING: This will destroy all FogNode infrastructure in GCP!"
echo ""

# Navigate to infrastructure directory
cd "$(dirname "$0")/../infra"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Pulumi environment not found. Run deploy.sh first."
    exit 1
fi

source venv/bin/activate

# Select stack
STACK_NAME="${PULUMI_STACK:-dev}"
pulumi stack select $STACK_NAME

# Show what will be destroyed
echo "📋 Resources that will be destroyed:"
pulumi stack --show-urns

echo ""
read -p "🤔 Are you SURE you want to destroy everything? (yes/NO): " -r
if [[ ! $REPLY == "yes" ]]; then
    echo "❌ Destruction cancelled."
    exit 0
fi

# Destroy infrastructure
echo ""
echo "💥 Destroying infrastructure..."
pulumi destroy --yes

echo ""
echo "✅ Infrastructure destroyed successfully."
echo ""
echo "💡 Stack still exists. To remove it completely, run:"
echo "   cd infra && pulumi stack rm $STACK_NAME"

deactivate
