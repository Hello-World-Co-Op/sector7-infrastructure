# Self-Hosted Infrastructure Setup Guide

## Architecture Overview

Given that `sector7.helloworlddao.com` points to your Aurora Tower, here's the optimized setup:

- **Aurora Tower** (AMD Ryzen 5000, 32GB RAM, 2TB): k3s control plane + worker
- **OptiPlex** (i7 vPro, 32GB RAM, 2TB): k3s worker node
- **Mini PC** (Ryzen 7 PRO, 32GB RAM, 2TB): Your desktop + kubectl management

---

## Phase 1: K3s Cluster Setup

### Step 1.1: Prepare Aurora Tower (Control Plane)

SSH into your Aurora Tower and run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install k3s as control plane (server)
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --disable traefik \
  --disable servicelb \
  --write-kubeconfig-mode=644 \
  --node-name=aurora \
  --tls-san=sector7.helloworlddao.com \
  --tls-san=$(hostname -I | awk '{print $1}')" sh -

# Wait for k3s to be ready
sudo systemctl status k3s

# Get the node token (you'll need this for worker nodes)
sudo cat /var/lib/rancher/k3s/server/node-token
```

**Save the token output!** It will look like: `K10abc123def456...::server:xyz789`

Get the Aurora's IP address:
```bash
hostname -I | awk '{print $1}'
```

**Save this IP!** (e.g., `192.168.1.100`)

---

### Step 1.2: Join OptiPlex as Worker Node

SSH into OptiPlex:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Join cluster (replace AURORA_IP and TOKEN)
curl -sfL https://get.k3s.io | K3S_URL=https://AURORA_IP:6443 \
  K3S_TOKEN=YOUR_NODE_TOKEN \
  INSTALL_K3S_EXEC="agent --node-name=optiplex" sh -

# Check status
sudo systemctl status k3s-agent
```

---

### Step 1.3: Configure kubectl on Mini PC

On your Mini PC desktop:

```bash
# Install kubectl
sudo snap install kubectl --classic

# Create kubeconfig directory
mkdir -p ~/.kube

# Copy kubeconfig from Aurora (replace AURORA_IP)
scp your-user@AURORA_IP:/etc/rancher/k3s/k3s.yaml ~/.kube/config

# Edit the config to use the correct server address
sed -i 's/127.0.0.1/AURORA_IP/g' ~/.kube/config

# Test connection
kubectl get nodes
```

**Expected output:**
```
NAME       STATUS   ROLES                  AGE   VERSION
aurora     Ready    control-plane,master   5m    v1.28.x
optiplex   Ready    <none>                 2m    v1.28.x
```

---

## Phase 2: MetalLB Load Balancer

MetalLB provides LoadBalancer IP addresses for services in your cluster.

Create `metallb-install.yaml`:

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: metallb-system
---
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: metallb
  namespace: kube-system
spec:
  repo: https://metallb.github.io/metallb
  chart: metallb
  targetNamespace: metallb-system
  createNamespace: true
```

Apply it:
```bash
kubectl apply -f metallb-install.yaml

# Wait for MetalLB to be ready
kubectl wait --namespace metallb-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=metallb \
  --timeout=90s
```

Now configure the IP address pool (adjust the IP range to match your network):

Create `metallb-config.yaml`:

```yaml
---
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.200-192.168.1.220  # Adjust to your network range
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
spec:
  ipAddressPools:
  - default-pool
```

Apply:
```bash
kubectl apply -f metallb-config.yaml
```

---

## Phase 3: Cert-Manager for SSL Certificates

Install cert-manager for automatic SSL certificates:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --namespace cert-manager \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=cert-manager \
  --timeout=90s
```

Create Let's Encrypt issuer - `letsencrypt-issuer.yaml`:

```yaml
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@helloworlddao.com  # CHANGE THIS
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: traefik
```

Apply:
```bash
kubectl apply -f letsencrypt-issuer.yaml
```

---

## Phase 4: Traefik Ingress Controller

Create `traefik-install.yaml`:

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: traefik
---
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: traefik
  namespace: kube-system
spec:
  repo: https://traefik.github.io/charts
  chart: traefik
  targetNamespace: traefik
  createNamespace: true
  valuesContent: |-
    service:
      type: LoadBalancer
    ports:
      web:
        redirectTo:
          port: websecure
      websecure:
        tls:
          enabled: true
    ingressRoute:
      dashboard:
        enabled: true
```

Apply:
```bash
kubectl apply -f traefik-install.yaml

# Get the LoadBalancer IP (this is where traffic will come in)
kubectl get svc -n traefik traefik -w
```

**Wait for `EXTERNAL-IP`** - this should be one of your MetalLB IPs (e.g., `192.168.1.200`).

---

## Phase 5: Longhorn Distributed Storage

Install dependencies on **BOTH Aurora and OptiPlex**:

```bash
sudo apt install -y open-iscsi nfs-common
sudo systemctl enable --now iscsid
```

Install Longhorn:

```bash
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.6.0/deploy/longhorn.yaml

# Wait for Longhorn to be ready (this takes 3-5 minutes)
kubectl get pods -n longhorn-system -w
```

Create Ingress for Longhorn UI - `longhorn-ingress.yaml`:

```yaml
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: longhorn-ingress
  namespace: longhorn-system
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    traefik.ingress.kubernetes.io/router.middlewares: longhorn-system-auth@kubernetescrd
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - longhorn.sector7.helloworlddao.com
    secretName: longhorn-tls
  rules:
  - host: longhorn.sector7.helloworlddao.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: longhorn-frontend
            port:
              number: 80
```

Set Longhorn as default storage class:

```bash
kubectl patch storageclass longhorn -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

---

## Phase 6: Deploy Core Services

### Step 6.1: Supabase

Create namespace and deploy Supabase:

```bash
kubectl create namespace supabase
```

Create `supabase-deploy.yaml`:

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: supabase-config
  namespace: supabase
data:
  POSTGRES_PASSWORD: "your-secure-password-here"  # CHANGE THIS
  JWT_SECRET: "your-jwt-secret-32-chars-min"      # CHANGE THIS
  ANON_KEY: "generate-this-key"                   # CHANGE THIS
  SERVICE_ROLE_KEY: "generate-this-key"           # CHANGE THIS
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: supabase-db
  namespace: supabase
spec:
  serviceName: supabase-db
  replicas: 1
  selector:
    matchLabels:
      app: supabase-db
  template:
    metadata:
      labels:
        app: supabase-db
    spec:
      containers:
      - name: postgres
        image: supabase/postgres:15.1.0.117
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            configMapKeyRef:
              name: supabase-config
              key: POSTGRES_PASSWORD
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: longhorn
      resources:
        requests:
          storage: 200Gi
---
apiVersion: v1
kind: Service
metadata:
  name: supabase-db
  namespace: supabase
spec:
  selector:
    app: supabase-db
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: supabase-ingress
  namespace: supabase
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - supabase.sector7.helloworlddao.com
    secretName: supabase-tls
  rules:
  - host: supabase.sector7.helloworlddao.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: supabase-api
            port:
              number: 8000
```

### Step 6.2: n8n Workflow Automation

Create `n8n-deploy.yaml`:

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: n8n
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: n8n-data
  namespace: n8n
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 50Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: n8n
  namespace: n8n
spec:
  replicas: 1
  selector:
    matchLabels:
      app: n8n
  template:
    metadata:
      labels:
        app: n8n
    spec:
      containers:
      - name: n8n
        image: n8nio/n8n:latest
        ports:
        - containerPort: 5678
        env:
        - name: N8N_HOST
          value: "n8n.sector7.helloworlddao.com"
        - name: N8N_PORT
          value: "5678"
        - name: N8N_PROTOCOL
          value: "https"
        - name: WEBHOOK_URL
          value: "https://n8n.sector7.helloworlddao.com/"
        - name: GENERIC_TIMEZONE
          value: "America/New_York"  # Adjust to your timezone
        volumeMounts:
        - name: n8n-data
          mountPath: /home/node/.n8n
      volumes:
      - name: n8n-data
        persistentVolumeClaim:
          claimName: n8n-data
---
apiVersion: v1
kind: Service
metadata:
  name: n8n
  namespace: n8n
spec:
  selector:
    app: n8n
  ports:
  - port: 5678
    targetPort: 5678
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: n8n-ingress
  namespace: n8n
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - n8n.sector7.helloworlddao.com
    secretName: n8n-tls
  rules:
  - host: n8n.sector7.helloworlddao.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: n8n
            port:
              number: 5678
```

Apply:
```bash
kubectl apply -f n8n-deploy.yaml
```

### Step 6.3: Nextcloud

Create `nextcloud-deploy.yaml`:

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: nextcloud
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nextcloud-data
  namespace: nextcloud
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 1Ti
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nextcloud
  namespace: nextcloud
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nextcloud
  template:
    metadata:
      labels:
        app: nextcloud
    spec:
      containers:
      - name: nextcloud
        image: nextcloud:latest
        ports:
        - containerPort: 80
        env:
        - name: POSTGRES_HOST
          value: "supabase-db.supabase.svc.cluster.local"
        - name: POSTGRES_DB
          value: "nextcloud"
        - name: POSTGRES_USER
          value: "postgres"
        - name: POSTGRES_PASSWORD
          value: "your-postgres-password"  # Match Supabase password
        - name: NEXTCLOUD_TRUSTED_DOMAINS
          value: "nextcloud.sector7.helloworlddao.com"
        - name: OVERWRITEPROTOCOL
          value: "https"
        volumeMounts:
        - name: nextcloud-data
          mountPath: /var/www/html
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: nextcloud-data
        persistentVolumeClaim:
          claimName: nextcloud-data
---
apiVersion: v1
kind: Service
metadata:
  name: nextcloud
  namespace: nextcloud
spec:
  selector:
    app: nextcloud
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nextcloud-ingress
  namespace: nextcloud
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    traefik.ingress.kubernetes.io/router.middlewares: nextcloud-nextcloud-redirectregex@kubernetescrd
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - nextcloud.sector7.helloworlddao.com
    secretName: nextcloud-tls
  rules:
  - host: nextcloud.sector7.helloworlddao.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nextcloud
            port:
              number: 80
```

Apply:
```bash
kubectl apply -f nextcloud-deploy.yaml
```

### Step 6.4: NocoDB

Create `nocodb-deploy.yaml`:

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: nocodb
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nocodb-data
  namespace: nocodb
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 100Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nocodb
  namespace: nocodb
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nocodb
  template:
    metadata:
      labels:
        app: nocodb
    spec:
      containers:
      - name: nocodb
        image: nocodb/nocodb:latest
        ports:
        - containerPort: 8080
        env:
        - name: NC_DB
          value: "pg://supabase-db.supabase.svc.cluster.local:5432?u=postgres&p=your-postgres-password&d=nocodb"
        volumeMounts:
        - name: nocodb-data
          mountPath: /usr/app/data
      volumes:
      - name: nocodb-data
        persistentVolumeClaim:
          claimName: nocodb-data
---
apiVersion: v1
kind: Service
metadata:
  name: nocodb
  namespace: nocodb
spec:
  selector:
    app: nocodb
  ports:
  - port: 8080
    targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nocodb-ingress
  namespace: nocodb
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - nocodb.sector7.helloworlddao.com
    secretName: nocodb-tls
  rules:
  - host: nocodb.sector7.helloworlddao.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nocodb
            port:
              number: 8080
```

Apply:
```bash
kubectl apply -f nocodb-deploy.yaml
```

### Step 6.5: AppFlowy

AppFlowy requires AppFlowy-Cloud for self-hosting. Create `appflowy-deploy.yaml`:

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: appflowy
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: appflowy-data
  namespace: appflowy
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 50Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: appflowy
  namespace: appflowy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: appflowy
  template:
    metadata:
      labels:
        app: appflowy
    spec:
      containers:
      - name: appflowy-cloud
        image: appflowyinc/appflowy_cloud:latest
        ports:
        - containerPort: 8000
        env:
        - name: RUST_LOG
          value: "info"
        - name: DATABASE_URL
          value: "postgresql://postgres:your-postgres-password@supabase-db.supabase.svc.cluster.local:5432/appflowy"
        volumeMounts:
        - name: appflowy-data
          mountPath: /app/data
      volumes:
      - name: appflowy-data
        persistentVolumeClaim:
          claimName: appflowy-data
---
apiVersion: v1
kind: Service
metadata:
  name: appflowy
  namespace: appflowy
spec:
  selector:
    app: appflowy
  ports:
  - port: 8000
    targetPort: 8000
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: appflowy-ingress
  namespace: appflowy
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - appflowy.sector7.helloworlddao.com
    secretName: appflowy-tls
  rules:
  - host: appflowy.sector7.helloworlddao.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: appflowy
            port:
              number: 8000
```

Apply:
```bash
kubectl apply -f appflowy-deploy.yaml
```

---

## Phase 7: DNS Configuration

Update your DNS records for `sector7.helloworlddao.com`:

```
Type    Name        Value                           TTL
A       sector7     <Aurora-Public-IP>              300
CNAME   n8n         sector7.helloworlddao.com       300
CNAME   nextcloud   sector7.helloworlddao.com       300
CNAME   nocodb      sector7.helloworlddao.com       300
CNAME   appflowy    sector7.helloworlddao.com       300
CNAME   supabase    sector7.helloworlddao.com       300
CNAME   longhorn    sector7.helloworlddao.com       300
```

**For remote access**, you'll need to:

1. **Option A - Port Forwarding**: Forward ports 80 and 443 on your router to Aurora's local IP
2. **Option B - Cloudflare Tunnel** (recommended):
   ```bash
   # Install cloudflared on Aurora
   kubectl apply -f https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   ```

---

## Phase 8: Monitoring (Optional but Recommended)

Install Prometheus + Grafana:

```bash
kubectl create namespace monitoring

# Install kube-prometheus-stack
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/setup/ -n monitoring
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/ -n monitoring
```

Create Grafana ingress - `grafana-ingress.yaml`:

```yaml
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana-ingress
  namespace: monitoring
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - grafana.sector7.helloworlddao.com
    secretName: grafana-tls
  rules:
  - host: grafana.sector7.helloworlddao.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: grafana
            port:
              number: 3000
```

---

## Quick Start Checklist

- [ ] Phase 1: Install k3s on Aurora (control plane)
- [ ] Phase 1: Join OptiPlex to cluster
- [ ] Phase 1: Configure kubectl on Mini PC
- [ ] Phase 2: Deploy MetalLB
- [ ] Phase 3: Install cert-manager
- [ ] Phase 4: Deploy Traefik ingress
- [ ] Phase 5: Install Longhorn storage
- [ ] Phase 6: Deploy services (Supabase → n8n → Nextcloud → NocoDB → AppFlowy)
- [ ] Phase 7: Configure DNS records
- [ ] Phase 8: Set up monitoring (optional)
- [ ] Test each service is accessible via HTTPS

---

## Useful Commands

```bash
# Check cluster status
kubectl get nodes
kubectl get pods --all-namespaces

# Check storage
kubectl get pvc --all-namespaces
kubectl get sc

# Check ingresses
kubectl get ingress --all-namespaces

# Check certificates
kubectl get certificates --all-namespaces

# View logs
kubectl logs -n <namespace> <pod-name>

# Restart a deployment
kubectl rollout restart deployment/<name> -n <namespace>
```

---

## Summary & Recommendations

This guide will set up a production-grade, self-hosted infrastructure with:

- **High availability** - Services distributed across 2 nodes
- **Automatic SSL** - Let's Encrypt certificates for all services
- **Persistent storage** - Longhorn replicated storage across nodes
- **Remote access** - HTTPS access via your domain
- **Scalability** - Easy to add more services or nodes

**Estimated setup time**: 4-6 hours for the complete stack

---

## Service Access URLs (After Setup)

Once everything is deployed, you'll access your services at:

- n8n: https://n8n.sector7.helloworlddao.com
- Nextcloud: https://nextcloud.sector7.helloworlddao.com
- NocoDB: https://nocodb.sector7.helloworlddao.com
- AppFlowy: https://appflowy.sector7.helloworlddao.com
- Supabase: https://supabase.sector7.helloworlddao.com
- Longhorn Dashboard: https://longhorn.sector7.helloworlddao.com
- Grafana (if installed): https://grafana.sector7.helloworlddao.com

---

## Troubleshooting

### Common Issues

**Pods stuck in Pending state:**
```bash
kubectl describe pod <pod-name> -n <namespace>
# Check events for issues with storage or scheduling
```

**Certificate not issuing:**
```bash
kubectl describe certificate <cert-name> -n <namespace>
kubectl describe certificaterequest -n <namespace>
# Check if DNS is properly configured and ports 80/443 are open
```

**Service not accessible:**
```bash
kubectl get ingress -n <namespace>
kubectl get svc -n <namespace>
# Verify ingress has an address and service endpoints exist
```

**Storage issues:**
```bash
kubectl get pvc -n <namespace>
kubectl get pv
# Check if Longhorn is running: kubectl get pods -n longhorn-system
```

---

## Security Recommendations

1. **Change all default passwords** in the YAML files before deploying
2. **Enable authentication** for Longhorn dashboard
3. **Set up regular backups** using Velero or Longhorn snapshots
4. **Configure firewall rules** on your router to only allow necessary traffic
5. **Use strong passwords** for all service admin accounts
6. **Enable 2FA** where available (Nextcloud, etc.)
7. **Regular updates**: Keep your cluster and services updated
   ```bash
   # Update k3s
   curl -sfL https://get.k3s.io | sh -

   # Update service images
   kubectl set image deployment/<name> <container>=<new-image> -n <namespace>
   ```

---

## Backup Strategy

**Automated daily backups:**

1. **Longhorn snapshots** - Automatic volume snapshots
2. **Database backups** - PostgreSQL dumps for Supabase
3. **Configuration backups** - Store all YAML files in git

Example backup script:
```bash
#!/bin/bash
# Save all Kubernetes resources
kubectl get all --all-namespaces -o yaml > cluster-backup-$(date +%Y%m%d).yaml

# Backup Supabase database
kubectl exec -n supabase supabase-db-0 -- pg_dumpall -U postgres > supabase-backup-$(date +%Y%m%d).sql
```

---

## Next Steps After Setup

1. **Configure each service** - Set up admin accounts, configure settings
2. **Create n8n workflows** - Start automating tasks between services
3. **Import data** - Migrate existing data to Nextcloud/NocoDB
4. **Set up monitoring alerts** - Configure Grafana dashboards and alerts
5. **Document your setup** - Keep notes on customizations and configurations
6. **Train your team** - Onboard team members to the new infrastructure

---

## Resources

- [k3s Documentation](https://docs.k3s.io/)
- [Longhorn Documentation](https://longhorn.io/docs/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [n8n Documentation](https://docs.n8n.io/)
- [Nextcloud Documentation](https://docs.nextcloud.com/)
- [NocoDB Documentation](https://docs.nocodb.com/)
- [Supabase Documentation](https://supabase.com/docs)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-03
**Author**: Claude Code Setup Guide
