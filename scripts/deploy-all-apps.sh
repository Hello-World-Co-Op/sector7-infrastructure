#!/bin/bash
# Deploy all applications to the cluster

set -e

echo "Deploying all applications..."

# Deploy Supabase
echo "Deploying Supabase..."
kubectl apply -f apps/supabase/

# Deploy n8n
echo "Deploying n8n..."
kubectl apply -f apps/n8n/

# Deploy Nextcloud
echo "Deploying Nextcloud..."
kubectl apply -f apps/nextcloud/

# Deploy NocoDB
echo "Deploying NocoDB..."
kubectl apply -f apps/nocodb/

# Deploy AppFlowy
echo "Deploying AppFlowy..."
kubectl apply -f apps/appflowy/

echo "All applications deployed!"
echo "Check status with: kubectl get pods --all-namespaces"
