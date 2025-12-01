# Working Services Snapshot
**Date:** 2025-11-23
**Before AppFlowy Clean Restart**

## Working Services in Cluster

### Infrastructure Services
- **cert-manager** - Running (SSL certificate management)
- **ingress-nginx** - Running at 192.168.2.159 (nginx ingress controller)
- **coredns** - Running (DNS)
- **local-path-provisioner** - Running (storage)
- **metrics-server** - Running

### Application Services (CONFIRMED WORKING)
- **heimdall** (namespace: heimdall) - Dashboard at sector7.helloworlddao.com
- **n8n** (namespace: n8n) - Workflow automation at n8n.sector7.helloworlddao.com
- **nextcloud** (namespace: nextcloud) - File storage at nextcloud.sector7.helloworlddao.com
- **nocodb** (namespace: nocodb) - Database UI at nocodb.sector7.helloworlddao.com
- **supabase-db** (namespace: supabase) - PostgreSQL database

### Plex Service
- Running as external service (mapped in ingress)

## Network Configuration
- **Cluster IPs:** 10.43.0.0/16 (services)
- **Pod Network:** 10.42.0.0/16
- **External Access:** 192.168.2.159 (nginx ingress controller)
- **Nodes:**
  - aurora: 192.168.2.159 (control-plane + worker)
  - optiplex: 192.168.2.231 (worker)

## AppFlowy Issues Encountered
- GoTrue container startup command fails with admin credentials
- Database schema mismatch (missing types, table search path issues)
- Admin portal returns "server error" with manually created users
- Need fresh deployment following official documentation exactly

## Action Taken
- Preserving supabase-db namespace (shared database)
- Cleaning appflowy namespace completely
- Will redeploy AppFlowy from scratch using official method
