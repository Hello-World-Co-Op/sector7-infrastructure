#!/bin/bash
# Aurora Forester Deployment Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$PROJECT_DIR/k8s"

echo "=========================================="
echo "Aurora Forester Deployment"
echo "=========================================="

# Check if Discord token is set
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo ""
    echo "ERROR: DISCORD_BOT_TOKEN not set"
    echo ""
    echo "Please set the Discord bot token:"
    echo "  export DISCORD_BOT_TOKEN='your_token_here'"
    echo ""
    exit 1
fi

# Check if channel ID is set
if [ -z "$DISCORD_CHANNEL_ID" ]; then
    echo ""
    echo "ERROR: DISCORD_CHANNEL_ID not set"
    echo ""
    echo "Please set the Discord channel ID:"
    echo "  export DISCORD_CHANNEL_ID='your_channel_id_here'"
    echo ""
    exit 1
fi

echo ""
echo "1. Creating namespace..."
kubectl apply -f "$K8S_DIR/namespace.yaml"

echo ""
echo "2. Creating secrets..."
# Create secret from environment variables
kubectl create secret generic aurora-secrets \
    --namespace=aurora-system \
    --from-literal=DISCORD_BOT_TOKEN="$DISCORD_BOT_TOKEN" \
    --from-literal=DISCORD_CHANNEL_ID="$DISCORD_CHANNEL_ID" \
    --from-literal=POSTGRES_USER="aurora_forester" \
    --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
    --from-literal=POSTGRES_DB="aurora_db" \
    --from-literal=HF_TOKEN="${HF_TOKEN:-}" \
    --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "3. Deploying PostgreSQL..."
kubectl apply -f "$K8S_DIR/postgres.yaml"

echo ""
echo "4. Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available deployment/aurora-postgres -n aurora-system --timeout=120s

echo ""
echo "5. Building Aurora Docker image..."
cd "$PROJECT_DIR"
docker build -t localhost:5000/aurora-forester:latest .

echo ""
echo "6. Pushing to local registry..."
docker push localhost:5000/aurora-forester:latest

echo ""
echo "7. Deploying Aurora bot..."
kubectl apply -f "$K8S_DIR/aurora-bot.yaml"

echo ""
echo "8. Waiting for Aurora to be ready..."
kubectl wait --for=condition=available deployment/aurora-bot -n aurora-system --timeout=120s

echo ""
echo "=========================================="
echo "Aurora Forester Deployed!"
echo "=========================================="
echo ""
echo "Check status:"
echo "  kubectl get pods -n aurora-system"
echo ""
echo "View logs:"
echo "  kubectl logs -f deployment/aurora-bot -n aurora-system"
echo ""
