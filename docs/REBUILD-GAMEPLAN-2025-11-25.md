# Sector7 Infrastructure - Complete Rebuild Gameplan
**Created**: 2025-11-25
**Author**: Lead Developer Gameplan
**Status**: PLANNING - NO CHANGES MADE YET
**Target Network**: 192.168.2.0/24
**External Access**: Port forwarding configured via OPNsense

---

## 🎯 PROJECT GOALS

Build a production-ready, self-hosted collaboration infrastructure for HelloWorldDAO with:

1. **Team Collaboration**: AppFlowy workspace for real-time collaboration
2. **Workflow Automation**: n8n with GPU acceleration for AI workflows
3. **Data Management**: NocoDB + PostgreSQL/Supabase for structured data
4. **External Access**: Secure HTTPS access for remote team members
5. **Reliability**: Distributed storage, automatic backups, monitoring
6. **Service Dashboard**: Heimdall as team landing page

---

## 🏗️ INFRASTRUCTURE STACK DECISION

### My Recommendation: Hybrid Best-of-Both Approach

After reviewing both options, here's what I recommend as lead developer:

| Component | Choice | Reasoning |
|-----------|--------|-----------|
| **Ingress** | ingress-nginx | ✅ Already working, simpler than Traefik, excellent docs |
| **LoadBalancer** | MetalLB | ✅ CRITICAL for clean external access, proper IP management |
| **Storage** | Longhorn | ✅ Replication, snapshots, backups - essential for production |
| **SSL** | cert-manager + Let's Encrypt | ✅ Required for external HTTPS access |
| **GPU** | NVIDIA Device Plugin | ✅ Required for n8n AI workflows |
| **Monitoring** | Prometheus + Grafana | ✅ Production requirement |
| **Backup** | Velero + Longhorn snapshots | ✅ Disaster recovery |

**Why this stack?**
- ingress-nginx is simpler and battle-tested (keep what works)
- MetalLB enables clean external access with dedicated IPs
- Longhorn provides production-grade storage with replication
- GPU support enables AI-powered workflows in n8n
- Monitoring prevents outages and enables troubleshooting

---

## 🌐 NETWORK ARCHITECTURE

### Final Network Topology (192.168.2.0/24)

```
Internet (71.73.220.69)
   │
   ├─► OPNsense Firewall (Protectli)
   │      ├─ WAN: 71.73.220.69 (public IP)
   │      ├─ LAN: 192.168.2.1/24
   │      └─ Port Forwarding: 80/443 → 192.168.2.200 ✅ CONFIGURED
   │
   └─► 192.168.2.0/24 Network
          ├─ Gateway: 192.168.2.1 (OPNsense)
          │
          ├─ K8s Nodes:
          │   ├─ Aurora Tower: 192.168.2.159 (control-plane + worker)
          │   └─ Dell OptiPlex: 192.168.2.231 (worker)
          │
          ├─ Management:
          │   └─ Mini PC: 192.168.2.106 (MOVE from 192.168.1.106)
          │
          └─ MetalLB Pool: 192.168.2.200-192.168.2.220
                ├─ 192.168.2.200 → ingress-nginx (HTTP/HTTPS entry point)
                ├─ 192.168.2.201 → Available
                └─ 192.168.2.202-220 → Reserved for future services
```

### IP Allocation Plan

| IP Address | Assignment | Purpose | Status |
|------------|------------|---------|--------|
| 192.168.2.1 | OPNsense | Gateway/Firewall | ✅ Active |
| 192.168.2.106 | Mini PC | Management station | ⚠️ Need to move from .1.106 |
| 192.168.2.159 | Aurora | k3s control-plane + worker | ✅ Active |
| 192.168.2.231 | OptiPlex | k3s worker | ✅ Active |
| 192.168.2.200 | MetalLB | ingress-nginx LoadBalancer | 📋 To configure |
| 192.168.2.201-220 | MetalLB Pool | Future LoadBalancer services | 📋 Reserved |

### DNS Configuration

**Internal DNS (OPNsense Unbound)**:
```
*.sector7.helloworlddao.com → 192.168.2.200
sector7.helloworlddao.com → 192.168.2.200
appflowy.sector7.helloworlddao.com → 192.168.2.200
n8n.sector7.helloworlddao.com → 192.168.2.200
nocodb.sector7.helloworlddao.com → 192.168.2.200
nextcloud.sector7.helloworlddao.com → 192.168.2.200
```

**External DNS (Cloudflare/Domain Provider)**:
```
A     sector7.helloworlddao.com → 71.73.220.69
CNAME *.sector7.helloworlddao.com → sector7.helloworlddao.com
```

---

## 📦 SERVICE STACK

### Core Services (In Priority Order)

1. **Heimdall** (Dashboard)
   - Purpose: Team landing page with service links
   - Access: https://sector7.helloworlddao.com
   - Storage: 1Gi
   - Priority: HIGH

2. **PostgreSQL/Supabase** (Shared Database)
   - Purpose: Centralized database for all services
   - Access: Internal only (ClusterIP)
   - Storage: 100Gi (Longhorn, replicated)
   - Used by: Nextcloud, NocoDB, AppFlowy (separate DB)
   - Priority: CRITICAL

3. **n8n** (Workflow Automation with GPU)
   - Purpose: AI-powered workflow automation
   - Access: https://n8n.sector7.helloworlddao.com
   - Storage: 20Gi
   - GPU: NVIDIA GPU via device plugin
   - Priority: HIGH

4. **NocoDB** (Database Interface)
   - Purpose: Low-code database UI, team data management
   - Access: https://nocodb.sector7.helloworlddao.com
   - Storage: 20Gi
   - Database: Supabase PostgreSQL
   - Priority: HIGH

5. **AppFlowy** (Collaboration Workspace)
   - Purpose: Real-time team collaboration (Notion alternative)
   - Access: https://appflowy.sector7.helloworlddao.com
   - Components: 8 microservices
   - Storage: 100Gi total (dedicated PostgreSQL + MinIO)
   - Priority: CRITICAL

6. **Nextcloud** (File Storage) - OPTIONAL
   - Purpose: File collaboration
   - Access: https://nextcloud.sector7.helloworlddao.com
   - Storage: 100Gi
   - Note: May be redundant with AppFlowy
   - Priority: LOW (evaluate if needed)

### Service Dependencies Map

```
Heimdall (standalone)

PostgreSQL/Supabase
   ├─ Used by: NocoDB
   ├─ Used by: Nextcloud (if deployed)
   └─ NOT used by: AppFlowy (has dedicated DB)

n8n
   ├─ Storage: n8n-data (20Gi)
   ├─ GPU: NVIDIA device
   └─ Can integrate with: All other services via API

NocoDB
   ├─ Storage: nocodb-data (20Gi)
   └─ Database: Supabase PostgreSQL

AppFlowy (Complete Stack)
   ├─ PostgreSQL: appflowy-postgres (50Gi, dedicated)
   ├─ Redis: appflowy-redis
   ├─ MinIO: appflowy-minio (50Gi)
   ├─ GoTrue: Authentication
   ├─ AppFlowy Cloud: Backend API
   ├─ AppFlowy Worker: Background jobs
   ├─ AppFlowy Web: Frontend
   └─ Admin Frontend: Admin console
```

---

## 🔧 DEPLOYMENT PHASES

### Phase 0: Pre-Flight Checks ✅ (1 hour)

**Objectives**: Backup current data, prepare for clean slate

1. **Backup Current Services** (CRITICAL - DO NOT SKIP)
   ```bash
   # Create backup directory
   mkdir -p ~/sector7-backups/$(date +%Y%m%d)

   # Backup all Kubernetes manifests
   kubectl get all --all-namespaces -o yaml > ~/sector7-backups/$(date +%Y%m%d)/all-resources.yaml

   # Export service data
   kubectl exec -n supabase supabase-db-0 -- pg_dumpall -U postgres > ~/sector7-backups/$(date +%Y%m%d)/supabase-dump.sql

   # Backup persistent volume data (if needed)
   kubectl get pvc --all-namespaces -o yaml > ~/sector7-backups/$(date +%Y%m%d)/pvcs.yaml
   ```

2. **Document Current Credentials**
   - Access each service UI and export/document credentials
   - Save to password manager
   - Create credentials.txt in secure location

3. **Network Preparation**
   - Move Mini PC to 192.168.2.106 (from 192.168.1.106)
   - Verify Mini PC can reach 192.168.2.159 (Aurora)
   - Test: `ping 192.168.2.159` from Mini PC

4. **Verify OPNsense Configuration**
   - Confirm port forwarding: 80/443 → 192.168.2.200
   - Verify firewall rules allow 192.168.2.200-220
   - Enable logging for troubleshooting

**Validation**:
- [ ] All data backed up to ~/sector7-backups/
- [ ] Credentials documented
- [ ] Mini PC on 192.168.2.106
- [ ] OPNsense port forwarding verified

---

### Phase 1: Nuclear Option - Clean Slate (30 minutes)

**Objectives**: Remove all existing services, keep cluster infrastructure

```bash
# Delete all application namespaces (DESTRUCTIVE)
kubectl delete namespace appflowy --grace-period=0 --force
kubectl delete namespace heimdall --grace-period=0 --force
kubectl delete namespace n8n --grace-period=0 --force
kubectl delete namespace nextcloud --grace-period=0 --force
kubectl delete namespace nocodb --grace-period=0 --force
kubectl delete namespace supabase --grace-period=0 --force
kubectl delete namespace demo --grace-period=0 --force

# Clean up PVCs (data will be lost - backup first!)
kubectl get pvc --all-namespaces
# Verify all application PVCs are gone

# Keep infrastructure: cert-manager, ingress-nginx, kube-system
# These stay intact
```

**Validation**:
- [ ] Only infrastructure namespaces remain
- [ ] All application PVCs deleted
- [ ] Cluster still healthy: `kubectl get nodes`

---

### Phase 2: Install Core Infrastructure (2 hours)

#### 2.1 Install MetalLB (30 min)

```bash
# Apply MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.0/config/manifests/metallb-native.yaml

# Wait for MetalLB to be ready
kubectl wait --namespace metallb-system \
  --for=condition=ready pod \
  --selector=app=metallb \
  --timeout=90s

# Configure IP pool
cat <<EOF | kubectl apply -f -
---
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: sector7-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.2.200-192.168.2.220
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: sector7-l2
  namespace: metallb-system
spec:
  ipAddressPools:
  - sector7-pool
EOF
```

**Validation**:
- [ ] MetalLB pods running in metallb-system namespace
- [ ] IPAddressPool created: `kubectl get ipaddresspool -n metallb-system`

#### 2.2 Install Longhorn Storage (1 hour)

```bash
# Install prerequisites on BOTH nodes (Aurora + OptiPlex)
ssh aurora "sudo apt update && sudo apt install -y open-iscsi nfs-common && sudo systemctl enable --now iscsid"
ssh optiplex "sudo apt update && sudo apt install -y open-iscsi nfs-common && sudo systemctl enable --now iscsid"

# Install Longhorn
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.6.0/deploy/longhorn.yaml

# Wait for Longhorn (takes 3-5 minutes)
kubectl get pods -n longhorn-system -w
# Wait until all pods are Running

# Set Longhorn as default storage class
kubectl patch storageclass longhorn -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

**Validation**:
- [ ] All Longhorn pods running
- [ ] Longhorn is default storage class: `kubectl get sc`

#### 2.3 Configure ingress-nginx with MetalLB (30 min)

```bash
# Update ingress-nginx to use LoadBalancer instead of NodePort
kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec": {"type": "LoadBalancer"}}'

# Wait for EXTERNAL-IP assignment
kubectl get svc -n ingress-nginx -w
# Should show EXTERNAL-IP: 192.168.2.200
```

**Validation**:
- [ ] ingress-nginx has EXTERNAL-IP 192.168.2.200
- [ ] Can access: `curl http://192.168.2.200` (should return 404 - nginx default)

#### 2.4 Configure cert-manager for SSL (30 min)

```bash
# Create Let's Encrypt ClusterIssuer
cat <<EOF | kubectl apply -f -
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: graydon@helloworlddao.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

**Validation**:
- [ ] ClusterIssuer created: `kubectl get clusterissuer`
- [ ] Ready status: `kubectl describe clusterissuer letsencrypt-prod`

---

### Phase 3: Install NVIDIA GPU Support (1 hour)

#### 3.1 Install NVIDIA Device Plugin

```bash
# Identify which node has GPU
kubectl get nodes
# Assuming Aurora has the GPU

# Label the GPU node
kubectl label nodes aurora nvidia.com/gpu=present

# Install NVIDIA device plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Verify GPU is detected
kubectl describe node aurora | grep -A 5 "nvidia.com/gpu"
# Should show: nvidia.com/gpu: 1 (or however many GPUs)
```

**Validation**:
- [ ] NVIDIA device plugin pod running
- [ ] GPU visible: `kubectl get nodes -o json | jq '.items[].status.capacity'`

---

### Phase 4: Deploy Core Services (4 hours)

#### 4.1 Deploy Heimdall Dashboard (30 min)

```bash
# Create namespace
kubectl create namespace heimdall

# Apply Heimdall manifests
kubectl apply -f ~/sector7-infrastructure/apps/heimdall/

# Create ingress with SSL
cat <<EOF | kubectl apply -f -
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: heimdall
  namespace: heimdall
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - sector7.helloworlddao.com
    secretName: heimdall-tls
  rules:
  - host: sector7.helloworlddao.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: heimdall
            port:
              number: 80
EOF
```

**Validation**:
- [ ] Heimdall pod running
- [ ] SSL certificate issued: `kubectl get certificate -n heimdall`
- [ ] Accessible: https://sector7.helloworlddao.com

#### 4.2 Deploy PostgreSQL/Supabase (1 hour)

**Design Decision**: Single PostgreSQL instance with multiple databases

```bash
# Create namespace
kubectl create namespace supabase

# Create secret for database credentials
kubectl create secret generic supabase-secrets -n supabase \
  --from-literal=POSTGRES_PASSWORD='YOUR_SECURE_PASSWORD_HERE' \
  --from-literal=JWT_SECRET='generate-32-char-secret' \
  --from-literal=ANON_KEY='generate-anon-key' \
  --from-literal=SERVICE_ROLE_KEY='generate-service-key'

# Deploy PostgreSQL StatefulSet
# (Use manifest from apps/supabase/ with Longhorn storage)
kubectl apply -f ~/sector7-infrastructure/apps/supabase/
```

**Validation**:
- [ ] PostgreSQL pod running
- [ ] Can exec into pod: `kubectl exec -it -n supabase supabase-db-0 -- psql -U postgres`
- [ ] Create test database: `CREATE DATABASE test;`

#### 4.3 Deploy n8n with GPU Support (1 hour)

```yaml
# Key configuration for GPU access
apiVersion: v1
kind: Pod
metadata:
  name: n8n
  namespace: n8n
spec:
  containers:
  - name: n8n
    image: n8nio/n8n:latest
    resources:
      limits:
        nvidia.com/gpu: 1  # Request GPU
```

**Validation**:
- [ ] n8n pod running with GPU: `kubectl describe pod -n n8n | grep nvidia`
- [ ] Accessible: https://n8n.sector7.helloworlddao.com
- [ ] GPU available in n8n workflows

#### 4.4 Deploy NocoDB (30 min)

```bash
# Create namespace
kubectl create namespace nocodb

# Connect to Supabase PostgreSQL
# (Configure DATABASE_URL to point to supabase-db)

kubectl apply -f ~/sector7-infrastructure/apps/nocodb/
```

**Validation**:
- [ ] NocoDB pod running
- [ ] Accessible: https://nocodb.sector7.helloworlddao.com
- [ ] Can create database projects

---

### Phase 5: Deploy AppFlowy (Full Stack) (3 hours)

**CRITICAL**: Follow official AppFlowy-Cloud setup exactly

#### 5.1 Preparation (30 min)

```bash
# Create namespace
kubectl create namespace appflowy

# Create comprehensive secrets
kubectl create secret generic appflowy-secrets -n appflowy \
  --from-literal=POSTGRES_USER='appflowy_admin' \
  --from-literal=POSTGRES_PASSWORD='SECURE_PASSWORD' \
  --from-literal=POSTGRES_DB='appflowy' \
  --from-literal=GOTRUE_JWT_SECRET='minimum-32-character-jwt-secret-for-appflowy-security' \
  --from-literal=GOTRUE_ADMIN_EMAIL='graydon@helloworlddao.com' \
  --from-literal=GOTRUE_ADMIN_PASSWORD='YOUR_ADMIN_PASSWORD' \
  --from-literal=APPFLOWY_S3_ACCESS_KEY='minio_admin' \
  --from-literal=APPFLOWY_S3_SECRET_KEY='SECURE_MINIO_PASSWORD'
```

#### 5.2 Deploy Services in Order (2.5 hours)

**Order matters!**

1. PostgreSQL (with pgvector)
2. Redis
3. MinIO
4. GoTrue (depends on PostgreSQL)
5. AppFlowy Cloud (depends on all above)
6. AppFlowy Worker
7. AppFlowy Web
8. Admin Frontend

**Key Configuration Points**:

- PostgreSQL must have pgvector extension
- GoTrue needs `search_path=auth` in DATABASE_URL
- All services must use INTERNAL service URLs
- Web frontend uses EXTERNAL URLs (for browser)
- Admin frontend needs both internal AND external URLs

#### 5.3 Ingress Configuration

```yaml
# Two separate ingresses:
# 1. GoTrue with path rewriting
# 2. All other services without rewriting
```

**Validation**:
- [ ] All 8 AppFlowy pods running
- [ ] PostgreSQL has pgvector: `kubectl exec -it appflowy-postgres-0 -n appflowy -- psql -U appflowy_admin -d appflowy -c "SELECT * FROM pg_extension WHERE extname='vector';"`
- [ ] GoTrue health: `curl https://appflowy.sector7.helloworlddao.com/gotrue/health`
- [ ] API health: `curl https://appflowy.sector7.helloworlddao.com/api/health`
- [ ] Web interface accessible: https://appflowy.sector7.helloworlddao.com
- [ ] Admin console accessible: https://appflowy.sector7.helloworlddao.com/console
- [ ] Can log in with admin credentials
- [ ] Can create workspace
- [ ] Can create documents

---

### Phase 6: Monitoring & Backups (2 hours)

#### 6.1 Deploy Prometheus + Grafana (1.5 hours)

```bash
kubectl create namespace monitoring

# Install kube-prometheus-stack
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/setup/
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/
```

**Validation**:
- [ ] Grafana accessible: https://grafana.sector7.helloworlddao.com
- [ ] Default dashboards working
- [ ] All nodes being monitored

#### 6.2 Configure Longhorn Backups (30 min)

```bash
# Configure recurring backup jobs
# Set backup target (NFS or S3)
# Enable automatic snapshots
```

**Validation**:
- [ ] Backup schedule created
- [ ] Test backup/restore

---

## 📋 DEPLOYMENT CHECKLIST

### Phase 0: Pre-Flight ✅
- [ ] All current data backed up
- [ ] Credentials documented
- [ ] Mini PC moved to 192.168.2.106
- [ ] Network connectivity verified

### Phase 1: Clean Slate
- [ ] All application namespaces deleted
- [ ] All application PVCs deleted
- [ ] Cluster still healthy

### Phase 2: Core Infrastructure
- [ ] MetalLB installed and configured
- [ ] Longhorn installed and set as default
- [ ] ingress-nginx using LoadBalancer (192.168.2.200)
- [ ] cert-manager configured for Let's Encrypt

### Phase 3: GPU Support
- [ ] NVIDIA device plugin installed
- [ ] GPU visible to Kubernetes

### Phase 4: Core Services
- [ ] Heimdall deployed with SSL
- [ ] PostgreSQL/Supabase deployed
- [ ] n8n deployed with GPU access
- [ ] NocoDB deployed

### Phase 5: AppFlowy
- [ ] All 8 microservices deployed
- [ ] PostgreSQL has pgvector
- [ ] Web interface working
- [ ] Admin console working
- [ ] Can create workspaces

### Phase 6: Production Readiness
- [ ] Monitoring deployed
- [ ] Backups configured
- [ ] All services have SSL certificates
- [ ] External access tested

---

## 🔐 CREDENTIALS MANAGEMENT

### Strategy

**DO NOT** store credentials in git. Use:

1. **Kubernetes Secrets** (for active services)
2. **Password Manager** (1Password, Bitwarden, etc.)
3. **Encrypted local file** (`~/sector7-infrastructure/secrets/.env` - git-ignored)

### Services Requiring Credentials

```bash
# Format: SERVICE: username / password / additional
Heimdall: admin / <set-during-setup>
PostgreSQL: postgres / <secure-password>
n8n: <email> / <password>
NocoDB: <email> / <password>
AppFlowy Admin: graydon@helloworlddao.com / <secure-password>
Grafana: admin / <secure-password>
```

---

## 🚀 ESTIMATED TIMELINE

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0: Pre-Flight | 1 hour | None |
| Phase 1: Clean Slate | 30 min | Phase 0 complete |
| Phase 2: Infrastructure | 2 hours | Phase 1 complete |
| Phase 3: GPU Support | 1 hour | Phase 2 complete |
| Phase 4: Core Services | 4 hours | Phase 2, 3 complete |
| Phase 5: AppFlowy | 3 hours | Phase 4 complete |
| Phase 6: Monitoring | 2 hours | Phase 5 complete |
| **TOTAL** | **~14 hours** | Spread over 2-3 days |

---

## ⚠️ RISK MITIGATION

### Backup Strategy
- Before deletion: Full pg_dump of all databases
- Export all Kubernetes manifests
- Document all credentials
- Test restore procedure BEFORE starting

### Rollback Plan
- Keep old PVCs for 7 days (rename, don't delete)
- Keep backups for 30 days
- Document rollback procedure

### Communication
- Notify team before starting
- Set maintenance window
- Provide status updates

---

## 📝 POST-DEPLOYMENT TASKS

1. **Update documentation**
   - CURRENT-STATE.md
   - NETWORK-TOPOLOGY.md
   - Service credentials in password manager

2. **Team onboarding**
   - Create team accounts
   - Share access credentials (securely)
   - Provide service overview

3. **Testing**
   - Test all services from external network
   - Verify SSL certificates
   - Test backup/restore
   - Load testing (if needed)

4. **Optimization**
   - Review resource usage
   - Tune replica counts
   - Optimize storage allocation

---

## 🎯 SUCCESS CRITERIA

Deployment is successful when:

- [ ] All services accessible via HTTPS externally
- [ ] Team members can access from outside network
- [ ] AppFlowy fully functional (create/edit documents)
- [ ] n8n has GPU access and can run AI workflows
- [ ] NocoDB connected to PostgreSQL
- [ ] Monitoring shows all services healthy
- [ ] Backups running automatically
- [ ] No manual intervention needed for 48 hours

---

## 🔄 NEXT STEPS

1. **Review this plan** with you
2. **Answer any questions**
3. **Get approval to proceed**
4. **Start Phase 0 backup**
5. **Execute plan systematically**

---

**END OF GAMEPLAN**

**Status**: Awaiting approval to proceed
**Estimated Start**: Upon your confirmation
**Estimated Completion**: 2-3 days from start
