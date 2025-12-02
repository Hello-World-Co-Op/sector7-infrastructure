# Sector7 Infrastructure - Current State Documentation

**Generated**: 2025-12-01
**Cluster Age**: 5 days
**Last Verified**: 2025-12-01 21:00 EST

---

## Executive Summary

**Status**: ✅ **FULLY OPERATIONAL**

- **Cluster**: k3s v1.33.5+k3s1 running on 2 nodes
- **Network**: 192.168.2.0/24 with MetalLB L2 (192.168.2.200-220)
- **Ingress**: ingress-nginx with Let's Encrypt SSL
- **Storage**: local-path-provisioner (default)
- **Working Services**: 8/8 (all services operational with HTTPS)
- **Repository**: https://github.com/Hello-World-Co-Op/sector7-infrastructure

---

## Cluster Infrastructure

### Nodes

| Node | Role | IP Address | Status | OS | Kernel | Container Runtime |
|------|------|------------|--------|----|----|-------------------|
| aurora | control-plane, master, worker | 192.168.2.159 | Ready | Ubuntu 25.10 | 6.17.0-6-generic | containerd 2.1.4-k3s1 |
| library-wa-shi-tan | worker | 192.168.2.231 | Ready | Ubuntu 25.10 | 6.17.0-6-generic | containerd 2.1.4-k3s1 |

**Node Specifications:**
- **Aurora**: AMD Ryzen 5 5500 (6 cores, 12 threads), 30GB RAM
- **library-wa-shi-tan**: Intel i7-4790 @ 3.60GHz (4 cores, 8 threads), 30GB RAM

### Kubernetes Versions

- **Server**: v1.33.5+k3s1
- **Client (kubectl)**: v1.34.2
- **Kustomize**: v5.7.1

### Core System Components

| Component | Namespace | Status | Purpose |
|-----------|-----------|--------|---------|
| coredns | kube-system | Running | Cluster DNS |
| local-path-provisioner | kube-system | Running | Storage provisioning |
| metrics-server | kube-system | Running | Resource metrics |
| cert-manager | cert-manager | Running | SSL certificate management |
| ingress-nginx | ingress-nginx | Running | Ingress controller |
| metallb | metallb-system | Running | L2 load balancer |

---

## Application Services

### Service Status Overview

| Service | URL | Status | SSL | Admin Setup |
|---------|-----|--------|-----|-------------|
| Heimdall | https://dashboard.sector7.helloworlddao.com | ✅ Running | ✅ Valid | ✅ Complete |
| AppFlowy | https://appflowy.sector7.helloworlddao.com | ✅ Running | ✅ Valid | ✅ Complete |
| n8n | https://n8n.sector7.helloworlddao.com | ✅ Running | ✅ Valid | ✅ Complete |
| Nextcloud | https://nextcloud.sector7.helloworlddao.com | ✅ Running | ✅ Valid | ✅ Complete |
| NocoDB | https://nocodb.sector7.helloworlddao.com | ✅ Running | ✅ Valid | ✅ Complete |
| Grafana | https://grafana.sector7.helloworlddao.com | ✅ Running | ✅ Valid | ✅ Complete |
| Ollama | https://ollama.sector7.helloworlddao.com | ✅ Running | ⚠️ Pending | N/A (API) |
| MinIO | https://minio.sector7.helloworlddao.com | ✅ Running | ⚠️ Pending | N/A (Internal) |

### 1. Heimdall Dashboard ✅

**Purpose**: Central application dashboard and launcher

- **Namespace**: heimdall
- **URL**: https://dashboard.sector7.helloworlddao.com
- **Image**: lscr.io/linuxserver/heimdall:latest
- **Status**: ✅ **OPERATIONAL**
- **SSL**: ✅ Let's Encrypt (valid)
- **Storage**: 1Gi PVC (heimdall-config)

### 2. AppFlowy (Collaboration Platform) ✅

**Purpose**: Open-source Notion alternative with AI features

- **Namespace**: appflowy
- **URL**: https://appflowy.sector7.helloworlddao.com
- **Status**: ✅ **OPERATIONAL**
- **SSL**: ✅ Let's Encrypt (valid)
- **Team Plan**: 4 seats (paid annual subscription)

**Components**:

| Component | Status | Image |
|-----------|--------|-------|
| appflowy-postgres | ✅ Running | postgres:15 |
| appflowy-redis | ✅ Running | redis:7-alpine |
| appflowy-minio | ✅ Running | minio/minio:latest |
| appflowy-gotrue | ✅ Running | appflowyinc/gotrue:latest |
| appflowy-cloud | ✅ Running | appflowyinc/appflowy_cloud:latest |
| appflowy-worker | ✅ Running | appflowyinc/appflowy_worker:latest |
| appflowy-web | ✅ Running | appflowyinc/appflowy_web:latest |
| appflowy-admin-frontend | ✅ Running | appflowyinc/admin_frontend:latest |

**AI Integration**:
- Connected to local Ollama LLM service
- Models available: llama3.2 (2.0GB), mistral (4.4GB), llama2 (3.8GB)
- Endpoint: http://ollama.ollama.svc.cluster.local:11434/v1

**Ingress Paths**:
- `/gotrue/*` → appflowy-gotrue:9999 (auth endpoints)
- `/ws` → appflowy-cloud:8000 (WebSocket)
- `/api` → appflowy-cloud:8000 (API)
- `/console` → appflowy-admin-frontend:3000 (Admin)
- `/` → appflowy-web:3000 (Web UI)

### 3. n8n (Workflow Automation) ✅

**Purpose**: Workflow automation and integration platform

- **Namespace**: n8n
- **URL**: https://n8n.sector7.helloworlddao.com
- **Image**: n8nio/n8n:latest
- **Status**: ✅ **OPERATIONAL**
- **SSL**: ✅ Let's Encrypt (valid)
- **Edition**: Community (free, single user)
- **Storage**: 5Gi PVC (n8n-data)
- **AI Integration**: Connected to Ollama

### 4. Nextcloud (File Storage) ✅

**Purpose**: Self-hosted file sharing and collaboration

- **Namespace**: nextcloud
- **URL**: https://nextcloud.sector7.helloworlddao.com
- **Image**: nextcloud:apache
- **Status**: ✅ **OPERATIONAL**
- **SSL**: ✅ Let's Encrypt (valid)
- **Storage**: 20Gi PVC (nextcloud-data)
- **Database**: PostgreSQL (shared postgres namespace)

**Users Configured**:
- admin (system administrator)
- degenotterdev (Graydon)
- menley
- coby

### 5. NocoDB (Database UI) ✅

**Purpose**: No-code database and Airtable alternative

- **Namespace**: nocodb
- **URL**: https://nocodb.sector7.helloworlddao.com
- **Image**: nocodb/nocodb:latest
- **Status**: ✅ **OPERATIONAL**
- **SSL**: ✅ Let's Encrypt (valid)
- **Storage**: 10Gi PVC (nocodb-data)
- **Users**: Unlimited (free tier)

### 6. Grafana + Prometheus (Monitoring) ✅

**Purpose**: Infrastructure monitoring and visualization

- **Namespace**: monitoring
- **Grafana URL**: https://grafana.sector7.helloworlddao.com
- **Status**: ✅ **OPERATIONAL**
- **SSL**: ✅ Let's Encrypt (valid)

**Components**:

| Component | Image | Storage | Purpose |
|-----------|-------|---------|---------|
| Prometheus | prom/prometheus:v2.47.0 | 10Gi | Metrics collection |
| Grafana | grafana/grafana:10.2.0 | 5Gi | Visualization |

**Data Sources**:
- Prometheus: http://prometheus.monitoring.svc.cluster.local:9090

### 7. Ollama (LLM Service) ✅

**Purpose**: Local LLM inference for AI features

- **Namespace**: ollama
- **URL**: https://ollama.sector7.helloworlddao.com
- **Status**: ✅ **OPERATIONAL**
- **SSL**: ⚠️ Certificate pending

**Models Available**:
- llama3.2 (2.0GB) - proposal drafting
- mistral (4.4GB) - general purpose
- llama2 (3.8GB)

---

## Network Configuration

### Network Topology

```
Internet (Public IP: 71.73.220.69)
   │
OPNsense Firewall (192.168.2.1)
   │ Port Forward: 80,443 → 192.168.2.200
   │
5-port Switch
   ├─ Aurora (192.168.2.159) - k3s control-plane + worker
   ├─ library-wa-shi-tan (192.168.2.231) - k3s worker
   └─ Mini PC (192.168.2.106) - kubectl management station

MetalLB L2 Pool: 192.168.2.200-220
Ingress VIP: 192.168.2.200
```

### DNS Configuration (GoDaddy)

| Subdomain | Type | Target |
|-----------|------|--------|
| sector7.helloworlddao.com | A | 71.73.220.69 |
| *.sector7.helloworlddao.com | CNAME | sector7.helloworlddao.com |
| appflowy.sector7 | CNAME | sector7.helloworlddao.com |
| n8n.sector7 | CNAME | sector7.helloworlddao.com |
| nextcloud.sector7 | CNAME | sector7.helloworlddao.com |
| nocodb.sector7 | CNAME | sector7.helloworlddao.com |
| dashboard.sector7 | CNAME | sector7.helloworlddao.com |
| grafana.sector7 | CNAME | sector7.helloworlddao.com |

### Kubernetes Network

- **Service CIDR**: 10.43.0.0/16
- **Pod CIDR**: 10.42.0.0/16
- **CNI**: Flannel (default k3s)
- **Load Balancer**: MetalLB L2 mode

### SSL/TLS Certificates

| Service | Certificate | Status | Issuer |
|---------|-------------|--------|--------|
| appflowy | appflowy-tls | ✅ Ready | letsencrypt-production |
| heimdall | heimdall-tls | ✅ Ready | letsencrypt-production |
| n8n | n8n-tls | ✅ Ready | letsencrypt-production |
| nextcloud | nextcloud-tls | ✅ Ready | letsencrypt-production |
| nocodb | nocodb-tls | ✅ Ready | letsencrypt-production |
| grafana | grafana-tls | ✅ Ready | letsencrypt-production |
| minio | minio-tls | ⚠️ Pending | letsencrypt-production |
| ollama | ollama-tls | ⚠️ Pending | letsencrypt-production |

---

## Storage

### Storage Classes

| Name | Provisioner | Reclaim Policy | Default |
|------|-------------|----------------|---------|
| local-path | rancher.io/local-path | Delete | ✅ Yes |

### Persistent Volume Claims

| PVC | Namespace | Size | Status |
|-----|-----------|------|--------|
| heimdall-config | heimdall | 1Gi | Bound |
| n8n-data | n8n | 5Gi | Bound |
| nextcloud-data | nextcloud | 20Gi | Bound |
| nocodb-data | nocodb | 10Gi | Bound |
| prometheus-data | monitoring | 10Gi | Bound |
| grafana-data | monitoring | 5Gi | Bound |
| appflowy-* | appflowy | Various | Bound |

---

## Security

### Credentials Storage

- **Location**: `/home/knower/sector7-infrastructure/credentials.txt.gpg`
- **Encryption**: GPG symmetric (AES256)
- **Decrypt**: `gpg -d credentials.txt.gpg > credentials.txt`

### Services with Authentication

| Service | Auth Type | Multi-User |
|---------|-----------|------------|
| AppFlowy | GoTrue (JWT) | ✅ Yes (4 seats) |
| n8n | Built-in | ❌ Single user (community) |
| Nextcloud | Built-in | ✅ Yes (unlimited) |
| NocoDB | Built-in | ✅ Yes (unlimited) |
| Grafana | Built-in | ✅ Yes |

---

## Recent Changes (2025-11-26 to 2025-12-01)

### Infrastructure Migration
- ✅ Migrated repository to GitHub (Hello-World-Co-Op/sector7-infrastructure)
- ✅ Fixed network topology (192.168.1.x → 192.168.2.x in all configs)
- ✅ Corrected OPNsense port forwarding and /etc/hosts

### AppFlowy
- ✅ Fixed mixed content blocking (HTTP → HTTPS for all URLs)
- ✅ Added TLS with Let's Encrypt certificate
- ✅ Upgraded to Team Plan (4 seats, annual subscription)
- ✅ Configured Ollama LLM integration for AI features
- ✅ Set up admin console and user accounts
- ✅ Updated desktop client to v0.10.4

### Admin Account Setup
- ✅ AppFlowy: Admin console + desktop user configured
- ✅ n8n: Owner account (single user, community edition)
- ✅ Nextcloud: Admin + 3 users (degenotterdev, menley, coby)
- ✅ NocoDB: Super admin configured

### Monitoring Stack (NEW)
- ✅ Deployed Prometheus for metrics collection
- ✅ Deployed Grafana for visualization
- ✅ Configured SSL certificate for Grafana
- ✅ Added Prometheus data source to Grafana

### Dashboard
- ✅ Fixed Heimdall DNS configuration
- ✅ SSL certificate issued and valid
- ✅ Added service links for all applications

### DNS
- ✅ Added CNAME for dashboard.sector7.helloworlddao.com
- ✅ Added CNAME for grafana.sector7.helloworlddao.com

---

## Directory Structure

```
sector7-infrastructure/
├── apps/
│   ├── appflowy/          # AppFlowy collaboration platform
│   ├── heimdall/          # Dashboard
│   ├── n8n/               # Workflow automation
│   ├── nextcloud/         # File storage
│   ├── nocodb/            # Database UI
│   └── ollama/            # LLM service
├── core/
│   ├── cert-manager/      # SSL certificate management
│   ├── ingress-nginx/     # Ingress controller
│   └── metallb/           # L2 load balancer
├── monitoring/
│   ├── 00-namespace.yaml
│   ├── prometheus/        # Metrics collection
│   └── grafana/           # Visualization
├── docs/
│   ├── CURRENT-STATE.md   # This document
│   ├── NETWORK-TOPOLOGY.md
│   ├── QUICK-REFERENCE.md
│   └── runbooks/
├── credentials.txt.gpg    # Encrypted credentials (not in git)
└── .gitignore
```

---

## Quick Reference Commands

```bash
# Check all pods
kubectl get pods -A

# Check certificates
kubectl get certificates -A

# Check ingresses
kubectl get ingress -A

# View logs
kubectl logs -n <namespace> <pod-name>

# Restart deployment
kubectl rollout restart deployment/<name> -n <namespace>

# Decrypt credentials
gpg -d credentials.txt.gpg > credentials.txt
```

---

## Next Steps

1. **Fix pending SSL certificates** (minio, ollama)
2. **Set up automated backups** (Velero or manual pg_dump)
3. **Configure Grafana dashboards** for Kubernetes monitoring
4. **Implement n8n workflows** for automation pipeline
5. **Set up proposal pipeline** for HelloWorldDAO

---

## Document Information

- **File**: /home/knower/sector7-infrastructure/docs/CURRENT-STATE.md
- **Purpose**: Authoritative reference for actual cluster state
- **Last Updated**: 2025-12-01
- **Repository**: https://github.com/Hello-World-Co-Op/sector7-infrastructure
