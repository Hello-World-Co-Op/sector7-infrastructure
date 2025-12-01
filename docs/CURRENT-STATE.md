# Sector7 Infrastructure - Current State Documentation

**Generated**: 2025-11-25
**Cluster Age**: 5 days 21 hours
**Last Verified**: 2025-11-25 13:30 EST

---

## Executive Summary

**Status**: ✅ **OPERATIONAL** (with 1 failing service)

- **Cluster**: k3s v1.33.5+k3s1 running on 2 nodes
- **Network**: 192.168.2.0/24 (migrated from 192.168.1.0/24)
- **Ingress**: ingress-nginx (NodePort mode)
- **Storage**: local-path-provisioner (default)
- **Working Services**: 5/6 (Heimdall, n8n, Nextcloud, NocoDB, Supabase)
- **Failing Services**: 1 (AppFlowy - GoTrue CrashLoopBackOff)

---

## Cluster Infrastructure

### Nodes

| Node | Role | IP Address | Status | OS | Kernel | Container Runtime |
|------|------|------------|--------|----|----|-------------------|
| aurora | control-plane, master, worker | 192.168.2.159 | Ready | Ubuntu 25.10 | 6.17.0-6-generic | containerd 2.1.4-k3s1 |
| optiplex | worker | 192.168.2.231 | Ready | Ubuntu 25.10 | 6.17.0-6-generic | containerd 2.1.4-k3s1 |

**Node Specifications:**
- **Aurora**: AMD Ryzen 5 5500 (6 cores, 12 threads), 30GB RAM, 98GB storage
- **OptiPlex**: Intel i7-4790 @ 3.60GHz (4 cores, 8 threads), 30GB RAM, 98GB storage

### Kubernetes Versions

- **Server**: v1.33.5+k3s1
- **Client (kubectl)**: v1.34.2
- **Kustomize**: v5.7.1

### Core System Components

| Component | Namespace | Version | Status | Replicas |
|-----------|-----------|---------|--------|----------|
| coredns | kube-system | 1.12.3 | Running | 1/1 |
| local-path-provisioner | kube-system | v0.0.31 | Running | 1/1 |
| metrics-server | kube-system | v0.8.0 | Running | 1/1 |

### Infrastructure Services

#### Ingress-Nginx Controller

- **Namespace**: ingress-nginx
- **Version**: v1.11.1
- **Type**: NodePort
- **Ports**:
  - HTTP: 30154 (NodePort) → 80
  - HTTPS: 31650 (NodePort) → 443
- **Service IP**: 10.43.173.223
- **Status**: ✅ Running (1/1)

#### Cert-Manager

- **Namespace**: cert-manager
- **Version**: v1.16.2
- **Components**:
  - cert-manager-controller: ✅ Running (1/1)
  - cert-manager-cainjector: ✅ Running (1/1)
  - cert-manager-webhook: ✅ Running (1/1)
- **Cluster Issuers**: letsencrypt-prod (configured)

### Storage

#### Storage Classes

| Name | Provisioner | Reclaim Policy | Volume Binding Mode | Default |
|------|-------------|----------------|---------------------|---------|
| local-path | rancher.io/local-path | Delete | WaitForFirstConsumer | ✅ Yes |

**Note**: Manifests reference "longhorn" storage class, but cluster uses "local-path" provisioner.

#### Persistent Volumes

| PVC Name | Namespace | Size | Status | Storage Class | Used By |
|----------|-----------|------|--------|---------------|---------|
| heimdall-config | heimdall | 1Gi | Bound | local-path | heimdall |
| n8n-data | n8n | 5Gi | Bound | local-path | n8n |
| nextcloud-data | nextcloud | 20Gi | Bound | local-path | nextcloud |
| nocodb-data | nocodb | 10Gi | Bound | local-path | nocodb |
| supabase-db | supabase | 20Gi | Bound | local-path | supabase-db |

**Total Storage Allocated**: 56 GiB
**Available**: 132 GB (67GB on aurora + 65GB on optiplex)

---

## Application Services

### 1. Heimdall (Dashboard) ✅

**Purpose**: Application dashboard and launcher

- **Namespace**: heimdall
- **URL**: http://sector7.helloworlddao.com
- **Image**: lscr.io/linuxserver/heimdall:latest
- **Deployment**: 1/1 replicas running on aurora
- **Status**: ✅ **OPERATIONAL**
- **Ingress**: nginx (HTTP only)
- **Storage**: 1Gi PVC (heimdall-config)
- **Environment**:
  - TZ: America/New_York
  - PUID: 1000
  - PGID: 1000

**Ports**: 80, 443

### 2. n8n (Workflow Automation) ✅

**Purpose**: Workflow automation and integration platform

- **Namespace**: n8n
- **URL**: http://n8n.sector7.helloworlddao.com
- **Image**: n8nio/n8n:latest
- **Deployment**: 1/1 replicas running on aurora
- **Status**: ✅ **OPERATIONAL**
- **Ingress**: nginx (HTTP only)
- **Storage**: 5Gi PVC (n8n-data)
- **Node Selector**: kubernetes.io/hostname=aurora
- **Resources**:
  - Requests: 500m CPU, 1Gi memory
  - Limits: 1000m CPU, 2Gi memory

**Key Environment Variables**:
- N8N_HOST: n8n.sector7.helloworlddao.com
- N8N_PROTOCOL: https
- N8N_AI_ENABLED: true
- N8N_AI_PROVIDER: ollama
- OLLAMA_HOST: http://ollama.ollama.svc.cluster.local:11434
- GENERIC_TIMEZONE: America/New_York

**Mount Path**: /home/node/.n8n (subPath: n8n)
**Security Context**: fsGroup 1000

### 3. Nextcloud (File Storage) ✅

**Purpose**: Self-hosted file sharing and collaboration

- **Namespace**: nextcloud
- **URL**: http://nextcloud.sector7.helloworlddao.com
- **Image**: nextcloud:apache
- **Deployment**: 1/1 replicas running on aurora
- **Status**: ✅ **OPERATIONAL**
- **Ingress**: nginx (HTTP only, proxy-body-size: 0)
- **Storage**: 20Gi PVC (nextcloud-data)
- **Database**: PostgreSQL (supabase-db)
- **Node Selector**: kubernetes.io/hostname=aurora
- **Resources**:
  - Requests: 1000m CPU, 2Gi memory
  - Limits: 2000m CPU, 4Gi memory

**Database Configuration**:
- POSTGRES_HOST: supabase-db.supabase.svc.cluster.local
- POSTGRES_DB: nextcloud
- POSTGRES_USER: postgres
- POSTGRES_PASSWORD: (from secret: supabase-config)

**Nextcloud Settings**:
- NEXTCLOUD_TRUSTED_DOMAINS: nextcloud.sector7.helloworlddao.com
- OVERWRITEPROTOCOL: https

**Mount Path**: /var/www/html (subPath: nextcloud)

### 4. NocoDB (Database UI) ✅

**Purpose**: No-code database and Airtable alternative

- **Namespace**: nocodb
- **URL**: http://nocodb.sector7.helloworlddao.com
- **Image**: nocodb/nocodb:latest
- **Deployment**: 1/1 replicas running on aurora
- **Status**: ✅ **OPERATIONAL**
- **Ingress**: nginx (HTTP only)
- **Storage**: 10Gi PVC (nocodb-data)
- **Database**: PostgreSQL (supabase-db)
- **Node Selector**: kubernetes.io/hostname=aurora
- **Resources**:
  - Requests: 500m CPU, 1Gi memory
  - Limits: 1000m CPU, 2Gi memory

**Database Configuration**:
- NC_DB: (from secret: nocodb-config)
- Connected to: supabase-db.supabase.svc.cluster.local

**Mount Path**: /usr/app/data (subPath: nocodb)
**Security Context**: fsGroup 1000

### 5. Supabase PostgreSQL (Database) ✅

**Purpose**: Shared PostgreSQL database for applications

- **Namespace**: supabase
- **Image**: supabase/postgres:15.1.0.147
- **Type**: StatefulSet
- **Deployment**: 1/1 replicas running on aurora
- **Status**: ✅ **OPERATIONAL**
- **Service**: ClusterIP (headless) on port 5432
- **Storage**: 20Gi PVC (supabase-db)
- **Node Selector**: kubernetes.io/hostname=aurora
- **Resources**:
  - Requests: 1000m CPU, 2Gi memory
  - Limits: 2000m CPU, 4Gi memory

**Databases Hosted**:
- nextcloud (used by Nextcloud)
- nocodb (used by NocoDB)
- postgres (default database with auth schema for Supabase)

**Schemas in postgres database**:
- auth (Supabase auth tables)
- extensions
- graphql, graphql_public
- pgbouncer
- pgsodium, pgsodium_masks
- public
- realtime
- storage
- vault

**Mount Path**: /var/lib/postgresql/data (subPath: pgdata)
**Password**: (from secret: supabase-config → POSTGRES_PASSWORD)

### 6. AppFlowy (Project Management) ❌

**Purpose**: Open-source project management (CURRENTLY FAILING)

- **Namespace**: appflowy
- **URL**: http://appflowy.sector7.helloworlddao.com
- **Status**: ❌ **DEGRADED** (GoTrue authentication service failing)

**Components**:

| Component | Status | Replicas | Image |
|-----------|--------|----------|-------|
| redis | ✅ Running | 1/1 | redis:7-alpine |
| minio | ✅ Running | 1/1 | minio/minio:latest |
| appflowy-cloud | ✅ Running | 1/1 | appflowyinc/appflowy_cloud:latest |
| appflowy-web | ✅ Running | 1/1 | appflowyinc/appflowy_web:latest |
| admin-frontend | ✅ Running | 1/1 | appflowyinc/admin_frontend:latest |
| gotrue | ❌ CrashLoopBackOff | 0/1 | appflowyinc/gotrue:latest |

**Problem**: GoTrue authentication service cannot start due to database migration failure:
```
ERROR: operator does not exist: uuid = text (SQLSTATE 42883)
Migration file: 20221208132122_backfill_email_last_sign_in_at.up.sql
```

**Root Cause**: AppFlowy's GoTrue is configured to use Supabase's PostgreSQL database with `search_path=auth`, but the Supabase auth schema is incompatible with GoTrue's expected schema. This creates a conflict between Supabase's auth tables and GoTrue's migration expectations.

**Database Connection**:
```
postgres://postgres:supabase123@supabase-db.supabase.svc.cluster.local:5432/postgres?sslmode=disable&search_path=auth
```

**Ingress Configuration**:
- /gotrue → gotrue:9999 (FAILING)
- /ws → appflowy-cloud:8000
- /api → appflowy-cloud:8000
- /console → admin-frontend:3000
- / → appflowy-web:3000

**Recommendation**: Remove AppFlowy from cluster. It requires a dedicated database separate from Supabase.

---

## Network Configuration

### Network Topology

```
Internet
   │
OPNsense Firewall (192.168.2.1)
   │
Spectrum Router (192.168.2.217)
   │
5-port Switch
   ├─ Aurora (192.168.2.159) - k3s control-plane + worker
   ├─ OptiPlex (192.168.2.231) - k3s worker
   └─ Mini PC (192.168.2.106) - kubectl management station
```

### IP Address Allocation

| Device/Service | IP Address | Network | Purpose |
|----------------|------------|---------|---------|
| OPNsense (LAN) | 192.168.2.1 | 192.168.2.0/24 | Firewall & gateway |
| Spectrum Router | 192.168.2.217 | 192.168.2.0/24 | Secondary router |
| Aurora Tower | 192.168.2.159 | 192.168.2.0/24 | k3s control-plane |
| Dell OptiPlex | 192.168.2.231 | 192.168.2.0/24 | k3s worker |
| Mini PC | 192.168.2.106 | 192.168.2.0/24 | kubectl management |

### Kubernetes Network CIDRs

- **Service CIDR**: 10.43.0.0/16
- **Pod CIDR**: 10.42.0.0/16
- **CNI**: Flannel (default k3s)

### Ingress Configuration

**Controller**: ingress-nginx
**Type**: NodePort (not LoadBalancer)
**Node Ports**:
- HTTP: 30154 → aurora:192.168.2.159:30154
- HTTPS: 31650 → aurora:192.168.2.159:31650

**External Access**:
- All services accessible via HTTP only (no SSL configured)
- DNS points to: 192.168.2.159 (aurora node)
- Ingress class: nginx
- SSL redirect: disabled (annotation: nginx.ingress.kubernetes.io/ssl-redirect: "false")

### Service URLs

| Service | Internal URL | Status |
|---------|-------------|--------|
| Heimdall | http://sector7.helloworlddao.com | ✅ HTTP |
| n8n | http://n8n.sector7.helloworlddao.com | ✅ HTTP |
| Nextcloud | http://nextcloud.sector7.helloworlddao.com | ✅ HTTP |
| NocoDB | http://nocodb.sector7.helloworlddao.com | ✅ HTTP |
| AppFlowy | http://appflowy.sector7.helloworlddao.com | ❌ Failing |

**Note**: All services currently use HTTP. TLS/SSL certificates are not yet issued despite cert-manager being installed.

---

## Security & Secrets

### Secrets in Use

| Secret Name | Namespace | Type | Used By | Keys |
|-------------|-----------|------|---------|------|
| supabase-config | supabase | Opaque | supabase-db, nextcloud | POSTGRES_PASSWORD |
| nocodb-config | nocodb | Opaque | nocodb | NC_DB |

**Warning**: Secrets should be reviewed and rotated. Default passwords may still be in use.

---

## Storage Analysis

### Disk Usage

**Aurora (192.168.2.159)**:
- Total: 98GB
- Used: 31GB
- Available: 67GB
- Usage: 32%

**OptiPlex (192.168.2.231)**:
- Total: 98GB
- Used: 33GB
- Available: 65GB
- Usage: 34%

**PVC Allocations**: 56GB (across both nodes)
**Remaining Capacity**: ~76GB available for new workloads

### Local-Path Storage Behavior

- **Provisioner**: rancher.io/local-path
- **Default Path**: /var/lib/rancher/k3s/storage
- **Binding Mode**: WaitForFirstConsumer (PVs created only when pods scheduled)
- **Reclaim Policy**: Delete (data deleted when PVC deleted)

---

## Key Discrepancies Between Manifests and Reality

### 1. Storage Class Mismatch

**Manifests Say**: `storageClassName: longhorn`
**Cluster Uses**: `storageClassName: local-path`

**Impact**: Longhorn is not installed. All PVCs are automatically using local-path provisioner due to it being the default storage class. This works but lacks the redundancy and replication features of Longhorn.

### 2. Ingress Class Mismatch

**Manifests Say**: `ingressClassName: traefik`
**Cluster Uses**: `ingressClassName: nginx`

**Impact**: Traefik was removed and replaced with ingress-nginx. All ingress resources have been manually updated in the cluster but manifest files still reference traefik.

### 3. Network Migration

**Old Docs Say**: 192.168.1.0/24
**Cluster Uses**: 192.168.2.0/24

**Impact**: Network migration completed successfully (Option A from INFRASTRUCTURE-AUDIT.md was implemented). Documentation needs updating.

### 4. LoadBalancer vs NodePort

**Old Docs Say**: MetalLB providing LoadBalancer IPs (192.168.1.200-220)
**Cluster Uses**: NodePort mode (30154, 31650 on aurora:192.168.2.159)

**Impact**: MetalLB is not installed. Ingress controller uses NodePort instead. External access requires port forwarding to NodePort ports on aurora node.

---

## Demo/Test Services

### Hello World (Demo)

- **Namespace**: demo
- **Image**: nginx:alpine
- **Deployment**: 2/2 replicas
- **Purpose**: Test deployment (can be removed)
- **Status**: ✅ Running
- **Ingress**: Not configured

---

## External Services (Not in Cluster)

The following services are mapped as ExternalName services but run outside the cluster:

| Service | External IP | Port | Location |
|---------|-------------|------|----------|
| nocodb | 192.168.2.231 | 8080 | OptiPlex (Docker) |
| plex | 192.168.2.231 | 32400 | OptiPlex (Docker) |

**Note**: OptiPlex is running standalone Docker containers alongside Kubernetes. This creates iptables conflicts that cause issues with some k8s services.

---

## Known Issues

### 1. AppFlowy GoTrue CrashLoopBackOff ❌ CRITICAL

**Status**: FAILING
**Restarts**: 6+
**Error**: Database migration failure (UUID type mismatch)
**Action Required**: Remove AppFlowy or provide dedicated database

### 2. No SSL/TLS Certificates 🔒 MEDIUM

**Status**: WARNING
**Issue**: cert-manager installed but certificates not issuing
**Impact**: All services use HTTP only (no HTTPS)
**Possible Causes**:
- Let's Encrypt ACME challenges not completing
- DNS not properly configured for external validation
- Port 80/443 not forwarded from internet to cluster

### 3. Manifest File Drift 📋 LOW

**Status**: DOCUMENTATION
**Issue**: Manifest files don't match deployed resources
**Impact**: `kubectl apply -f apps/` would fail or create conflicts
**Action Required**: Update manifest files to match actual state

---

## Resource Utilization

### CPU and Memory (Approximate)

| Node | CPU Usage | Memory Usage | CPU Capacity | Memory Capacity |
|------|-----------|--------------|--------------|-----------------|
| aurora | < 2000m | ~8Gi | 12 cores | 30Gi |
| optiplex | < 1000m | ~4Gi | 8 cores | 30Gi |

**Total Cluster**:
- CPU: ~3000m used / 20 cores available (15% utilization)
- Memory: ~12Gi used / 60Gi available (20% utilization)

**Note**: Cluster is lightly loaded with significant capacity for additional workloads.

---

## Recommendations

### Immediate Actions

1. **Remove AppFlowy from cluster** (per user request)
   - Delete appflowy namespace: `kubectl delete namespace appflowy`
   - Remove manifest files from apps/appflowy/
   - Update documentation

2. **Update Manifest Files**
   - Change all `storageClassName: longhorn` → `storageClassName: local-path`
   - Change all `ingressClassName: traefik` → `ingressClassName: nginx`
   - Update network IPs from 192.168.1.x → 192.168.2.x

3. **Fix SSL Certificates**
   - Verify DNS records point to public IP
   - Check port forwarding (80/443) from OPNsense → Spectrum Router → aurora:30154/31650
   - Test ACME HTTP-01 challenge completion

### Short Term Improvements

1. **Install Longhorn** (if distributed storage desired)
   - Provides replication across nodes
   - Enables volume snapshots and backups
   - Requires updating PVCs to use longhorn storage class

2. **Configure External Access**
   - Set up proper port forwarding through double NAT
   - OR: Migrate to single NAT (connect switch directly to OPNsense)

3. **Security Hardening**
   - Rotate all default passwords
   - Create proper Kubernetes secrets (not ConfigMaps)
   - Enable network policies
   - Configure Pod Security Standards

### Long Term Architecture

1. **Consider LoadBalancer Setup**
   - Install MetalLB or use cloud load balancer
   - Eliminate NodePort dependencies
   - Simplify external access

2. **Implement Monitoring**
   - Deploy Prometheus + Grafana
   - Set up alerts for pod failures
   - Track resource utilization trends

3. **Backup Strategy**
   - Automated PV backups (Velero or Longhorn snapshots)
   - PostgreSQL dumps (pg_dumpall)
   - GitOps for manifests (already in git)

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-20 | Initial cluster deployment | Previous Claude |
| 2025-11-21 | Network migration (192.168.1.x → 192.168.2.x) | Previous Claude |
| 2025-11-21 | Replaced Traefik with ingress-nginx | Previous Claude |
| 2025-11-22 | Removed Longhorn, using local-path | Previous Claude |
| 2025-11-23 | AppFlowy deployed (failing) | Previous Claude |
| 2025-11-25 | **This document created** | Claude (current) |

---

## Document Information

- **File**: /home/knower/sector7-infrastructure/docs/CURRENT-STATE.md
- **Purpose**: Authoritative reference for actual cluster state
- **Maintained By**: Manual updates after each significant change
- **Review Frequency**: After any infrastructure changes
- **Related Docs**:
  - INFRASTRUCTURE-AUDIT.md (historical audit from 2025-11-15)
  - WORKING-SERVICES-SNAPSHOT.md (snapshot from 2025-11-23)
  - QUICK-REFERENCE.md (operational commands - needs update)
  - README.md (project overview - needs update)

---

**Status**: This document represents the verified current state as of 2025-11-25 13:30 EST.
**Next Action**: Remove AppFlowy components and update all documentation to match reality.
