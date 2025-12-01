# Sector7 Infrastructure - Quick Reference

**Last Updated**: 2025-11-25
**Status**: ✅ OPERATIONAL

> **For detailed current state**, see [CURRENT-STATE.md](./CURRENT-STATE.md)

## Current Status

### Infrastructure: ✅ ALL RUNNING
- k3s cluster: **Running** (2 nodes)
- ingress-nginx: **Running** (NodePort mode)
- cert-manager: **Running** (v1.16.2)
- local-path-provisioner: **Running** (default storage)

### Applications: ✅ 5/5 OPERATIONAL
- Heimdall: **Running** (sector7.helloworlddao.com)
- n8n: **Running** (n8n.sector7.helloworlddao.com)
- Nextcloud: **Running** (nextcloud.sector7.helloworlddao.com)
- NocoDB: **Running** (nocodb.sector7.helloworlddao.com)
- Supabase: **Running** (PostgreSQL database)

### Network Configuration

```
Network: 192.168.2.0/24
Gateway: 192.168.2.1 (OPNsense)

Nodes:
  - aurora:    192.168.2.159  (k3s control-plane + worker)
  - optiplex:  192.168.2.231  (k3s worker)
  - mini-pc:   192.168.2.106  (kubectl management)

Ingress:
  - Controller:      ingress-nginx (NodePort mode)
  - HTTP NodePort:   30154 (maps to port 80)
  - HTTPS NodePort:  31650 (maps to port 443)
  - Access via:      192.168.2.159:30154 (HTTP)
```

## Quick Commands

### Cluster Status
```bash
# Check nodes
kubectl get nodes -o wide

# Check all pods
kubectl get pods -A

# Check services
kubectl get svc -A

# Check storage
kubectl get pvc -A
kubectl get sc

# Check ingresses
kubectl get ingress -A
```

### Ingress-Nginx Status
```bash
# Check ingress controller
kubectl get svc -n ingress-nginx

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Get NodePort mappings
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Test ingress access (from inside network)
curl -I http://192.168.2.159:30154
```

### Storage Status
```bash
# Check storage classes
kubectl get sc

# Check local-path-provisioner
kubectl get pods -n kube-system -l app=local-path-provisioner

# Check PV usage
kubectl get pv
kubectl get pvc -A

# Storage is located at: /var/lib/rancher/k3s/storage on each node
```

### cert-manager Status
```bash
# Check cert-manager pods
kubectl get pods -n cert-manager

# Check cluster issuers
kubectl get clusterissuer

# Check certificates
kubectl get certificates -A

# Check certificate requests
kubectl get certificaterequest -A
```

## Next Steps

### 1. Configure SSL/TLS Certificates

Enable HTTPS for all services:

```bash
# Check if cert-manager is issuing certificates
kubectl get certificates -A

# If no certificates exist, verify:
# 1. DNS points to your public IP
# 2. Port 80/443 forwarded to aurora:30154/31650
# 3. Let's Encrypt can reach your cluster for HTTP-01 challenges

# Manually trigger certificate issuance (if needed)
kubectl annotate ingress -n heimdall heimdall cert-manager.io/cluster-issuer=letsencrypt-prod
```

### 2. Configure External Access

Set up port forwarding through your network:

**OPNsense Firewall**:
- Forward WAN port 80 → 192.168.2.217:80 (Spectrum Router)
- Forward WAN port 443 → 192.168.2.217:443 (Spectrum Router)

**Spectrum Router**:
- Forward LAN port 80 → 192.168.2.159:30154 (aurora HTTP NodePort)
- Forward LAN port 443 → 192.168.2.159:31650 (aurora HTTPS NodePort)

### 3. Configure DNS

**Option A: Local DNS (OPNsense)**
- Add host overrides in OPNsense for internal access
- See: [OPNSENSE-CONFIGURATION.md Step 5](./OPNSENSE-CONFIGURATION.md#step-5-local-dns-configuration)

**Option B: Public DNS**
- Point `*.sector7.helloworlddao.com` to your public IP
- Configure port forwarding in OPNsense (80/443 → 192.168.1.200)
- Let's Encrypt will automatically issue certificates

### 4. Access Services

**Current access (HTTP only, internal network):**
- Heimdall: http://sector7.helloworlddao.com
- n8n: http://n8n.sector7.helloworlddao.com
- Nextcloud: http://nextcloud.sector7.helloworlddao.com
- NocoDB: http://nocodb.sector7.helloworlddao.com

**After SSL configuration:**
- All URLs will be accessible via HTTPS
- Same URLs work externally after port forwarding configured

## Troubleshooting

### Services not accessible

```bash
# 1. Check if service is running
kubectl get pods -n [namespace]

# 2. Check if service has endpoint
kubectl get svc -n [namespace]
kubectl get endpoints -n [namespace]

# 3. Check if ingress exists
kubectl get ingress -n [namespace]

# 4. Check Traefik logs
kubectl logs -n traefik -l app.kubernetes.io/name=traefik --tail=100

# 5. Check firewall rules in OPNsense
# Firewall → Log Files → Live View
```

### Certificate issues

```bash
# Check certificate status
kubectl get certificates -A

# Check certificate request
kubectl describe certificaterequest -n [namespace]

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager --tail=100

# Check if ACME challenge is working
kubectl describe challenge -A
```

### Storage issues

```bash
# Check Longhorn status
kubectl get pods -n longhorn-system

# Check PVC status
kubectl get pvc -A

# Check PV status
kubectl get pv

# Describe PVC for events
kubectl describe pvc -n [namespace] [pvc-name]
```

## Useful Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Kubectl aliases
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgi='kubectl get ingress'
alias kgn='kubectl get nodes'
alias kga='kubectl get all -A'
alias klog='kubectl logs -f'
alias kdesc='kubectl describe'

# Sector7 specific
alias s7='cd ~/sector7-infrastructure'
alias s7-pods='kubectl get pods -A | grep -E "(heimdall|n8n|nextcloud|nocodb|supabase)"'
alias s7-status='kubectl get svc -n ingress-nginx && kubectl get ingress -A'
```

## Important Files

```
~/sector7-infrastructure/
├── docs/
│   ├── NETWORK-TOPOLOGY.md          # Network diagram and IP allocations
│   ├── OPNSENSE-CONFIGURATION.md    # Step-by-step OPNsense setup
│   ├── QUICK-REFERENCE.md           # This file
│   ├── SECURITY-GUIDE.md            # Security best practices
│   └── setup-guide.md               # Original setup guide
├── cluster/                         # Infrastructure manifests
│   ├── 00-namespaces/
│   ├── 01-metallb/
│   ├── 02-cert-manager/
│   ├── 03-traefik/
│   └── 04-longhorn/
├── apps/                            # Application manifests
│   ├── supabase/
│   ├── n8n/
│   ├── nextcloud/
│   ├── nocodb/
│   └── appflowy/
└── scripts/
    ├── deploy-all-apps.sh
    └── backup.sh
```

## Emergency Procedures

### Cluster is down

```bash
# Check node status
kubectl get nodes

# If nodes are down, SSH to each node and check k3s
ssh aurora@192.168.1.50
sudo systemctl status k3s

ssh aurora@192.168.1.51
sudo systemctl status k3s-agent

# Restart k3s if needed
sudo systemctl restart k3s         # on control plane
sudo systemctl restart k3s-agent   # on worker node
```

### Reset a namespace

```bash
# Delete everything in a namespace
kubectl delete all --all -n [namespace]

# Delete PVCs (THIS DELETES DATA!)
kubectl delete pvc --all -n [namespace]

# Redeploy
kubectl apply -f apps/[service]/
```

### Access cluster without kubectl

```bash
# Get kubeconfig from Aurora
scp aurora@192.168.1.50:/etc/rancher/k3s/k3s.yaml ~/.kube/config

# Edit the server address
sed -i 's/127.0.0.1/192.168.1.50/g' ~/.kube/config

# Test
kubectl get nodes
```

## Resource Monitoring

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage
kubectl top pods -A

# Check storage usage
kubectl get pv
df -h  # on each node

# Check Longhorn volume usage (via UI)
# https://longhorn.sector7.helloworlddao.com
```

## Backup

```bash
# Quick backup of all resources
kubectl get all --all-namespaces -o yaml > cluster-backup-$(date +%Y%m%d).yaml

# Backup Longhorn volumes
# Use Longhorn UI: Backup → Create Backup
# Or automated via Longhorn recurring jobs

# Backup OPNsense configuration
# System → Configuration → Backups → Download
```

## Support Resources

- Sector7 Documentation: `~/sector7-infrastructure/docs/`
- k3s Docs: https://docs.k3s.io/
- Traefik Docs: https://doc.traefik.io/traefik/
- Longhorn Docs: https://longhorn.io/docs/
- OPNsense Docs: https://docs.opnsense.org/

---

**Last Updated:** 2025-11-25
**Cluster Version:** k3s v1.33.5+k3s1
**Ingress**: ingress-nginx v1.11.1 (NodePort mode)
**Status:** ✅ OPERATIONAL - 5 services running
