#!/bin/bash
# Backup script for cluster data

set -e

BACKUP_DIR="${HOME}/backups/sector7-$(date +%Y%m%d-%H%M%S)"
mkdir -p "${BACKUP_DIR}"

echo "Creating backup in ${BACKUP_DIR}..."

# Backup all Kubernetes resources
echo "Backing up Kubernetes resources..."
kubectl get all --all-namespaces -o yaml > "${BACKUP_DIR}/cluster-resources.yaml"
kubectl get pvc --all-namespaces -o yaml > "${BACKUP_DIR}/pvcs.yaml"
kubectl get ingress --all-namespaces -o yaml > "${BACKUP_DIR}/ingresses.yaml"

# Backup Supabase database
echo "Backing up Supabase database..."
kubectl exec -n supabase supabase-db-0 -- pg_dumpall -U postgres > "${BACKUP_DIR}/supabase-db.sql"

echo "Backup completed: ${BACKUP_DIR}"
echo "Files:"
ls -lh "${BACKUP_DIR}"
