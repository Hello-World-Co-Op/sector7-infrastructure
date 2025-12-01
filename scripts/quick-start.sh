#!/bin/bash
# Quick start script for setting up the cluster

set -e

echo "Sector7 Infrastructure Quick Start"
echo "==================================="
echo ""
echo "This script will guide you through the initial setup."
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "ERROR: Cannot connect to cluster. Please configure kubectl first."
    echo "See docs/setup-guide.md Phase 1 for instructions."
    exit 1
fi

echo "Cluster connection: OK"
echo ""

# Deploy cluster infrastructure
echo "Step 1: Deploy cluster infrastructure"
echo "--------------------------------------"
read -p "Deploy MetalLB, cert-manager, Traefik, and Longhorn? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f cluster/00-namespaces/
    echo "Waiting for namespaces..."
    sleep 5

    kubectl apply -f cluster/01-metallb/install.yaml
    echo "MetalLB installed. Please configure cluster/01-metallb/ip-pool.yaml and apply it manually."

    echo "Installing cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

    kubectl apply -f cluster/03-traefik/

    echo "For Longhorn, install dependencies on all nodes first:"
    echo "  sudo apt install -y open-iscsi nfs-common"
    echo "  sudo systemctl enable --now iscsid"
    echo "Then run: kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.6.0/deploy/longhorn.yaml"
fi

echo ""
echo "Next steps:"
echo "1. Configure secrets in secrets/ directory"
echo "2. Run ./scripts/deploy-all-apps.sh to deploy applications"
echo "3. Configure DNS for *.sector7.helloworlddao.com"
echo ""
echo "See docs/setup-guide.md for detailed instructions."
