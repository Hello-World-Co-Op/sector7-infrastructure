# Sector7 Infrastructure - Network Topology

## Network Diagram

```
Internet
   │
   ├─► Modem
   │
   ├─► Protectli Firewall (OPNsense)
   │      └─► WAN: DHCP from modem
   │      └─► LAN: 192.168.2.0/24
   │      └─► Gateway: 192.168.2.1
   │
   ├─► 5-Port Switch
   │
   ├─► Aurora Tower (k3s control plane)
   │      └─► IP: 192.168.2.159
   │      └─► Role: k3s server + worker
   │      └─► Specs: AMD Ryzen 5000, 32GB RAM, 2TB
   │
   ├─► library-wa-shi-tan (k3s worker)
   │      └─► IP: 192.168.2.231
   │      └─► Role: k3s agent
   │      └─► Specs: i7 vPro, 32GB RAM, 2TB
   │
   └─► Mini PC (management)
          └─► IP: 192.168.2.93
          └─► Role: kubectl management, development
          └─► Specs: Ryzen 7 PRO, 32GB RAM, 2TB
```

## IP Address Allocation

### Static/Reserved IPs

| IP Address | Device | Purpose | Status |
|------------|--------|---------|--------|
| 192.168.2.1 | Gateway | OPNsense firewall/gateway | Active |
| 192.168.2.93 | mini-pc | kubectl management | Active |
| 192.168.2.159 | aurora | k3s control plane + worker | Active |
| 192.168.2.231 | library-wa-shi-tan | k3s worker node | Active |
| 192.168.2.200-220 | MetalLB Pool | LoadBalancer service IPs | Reserved |

### LoadBalancer IP Assignments

| IP Address | Service | Namespace | Purpose |
|------------|---------|-----------|---------|
| 192.168.2.200 | ingress-nginx | ingress-nginx | Ingress controller (HTTP/HTTPS) |
| 192.168.2.201-220 | - | - | Available for new LoadBalancer services |

## Network Services

### Kubernetes Cluster
- **k3s Version:** v1.33.5+k3s1
- **Nodes:** 2 (1 control plane + worker, 1 worker)
- **CNI:** Flannel (default k3s)
- **Service CIDR:** 10.43.0.0/16
- **Pod CIDR:** 10.42.0.0/16

### MetalLB Configuration
- **Mode:** Layer 2 (L2Advertisement)
- **IP Pool:** 192.168.2.200-192.168.2.220
- **Namespace:** metallb-system

### Ingress-NGINX Controller
- **LoadBalancer IP:** 192.168.2.200
- **HTTP Port:** 80 → 32751 (NodePort)
- **HTTPS Port:** 443 → 30248 (NodePort)

## External Access

### Public IP
- **WAN IP:** 71.73.220.69
- **Domain:** sector7.helloworlddao.com

### DNS Records (point to 71.73.220.69)
```
A     sector7.helloworlddao.com           → 71.73.220.69
CNAME appflowy.sector7.helloworlddao.com  → sector7.helloworlddao.com
CNAME n8n.sector7.helloworlddao.com       → sector7.helloworlddao.com
CNAME nextcloud.sector7.helloworlddao.com → sector7.helloworlddao.com
CNAME nocodb.sector7.helloworlddao.com    → sector7.helloworlddao.com
```

## OPNsense Firewall Configuration

### Access OPNsense Web UI
- **URL:** http://192.168.2.1
- **Default user:** root

### 1. Port Forwarding (WAN Interface)

Navigate to: **Firewall → NAT → Port Forward**

| Interface | Protocol | Dest Port | Redirect Target IP | Redirect Port | Description |
|-----------|----------|-----------|-------------------|---------------|-------------|
| WAN | TCP | 80 | 192.168.2.200 | 80 | HTTP to Ingress |
| WAN | TCP | 443 | 192.168.2.200 | 443 | HTTPS to Ingress |

### 2. Firewall Rules (LAN Interface)

Navigate to: **Firewall → Rules → LAN**

```
Action: Pass
Interface: LAN
Protocol: TCP/UDP
Source: LAN net
Destination: 192.168.2.159, 192.168.2.231 (k3s nodes)
Description: Allow LAN access to k3s cluster nodes
```

```
Action: Pass
Interface: LAN
Protocol: TCP/UDP
Source: LAN net
Destination: 192.168.2.200-220 (MetalLB pool)
Description: Allow LAN access to k8s LoadBalancer services
```

### 3. Local DNS Configuration

Navigate to: **Services → Unbound DNS → Overrides**

Add these host overrides:

| Host | Domain | IP Address | Description |
|------|--------|------------|-------------|
| appflowy | sector7.helloworlddao.com | 192.168.2.200 | AppFlowy workspace |
| n8n | sector7.helloworlddao.com | 192.168.2.200 | n8n workflow automation |
| nextcloud | sector7.helloworlddao.com | 192.168.2.200 | Nextcloud file sharing |
| nocodb | sector7.helloworlddao.com | 192.168.2.200 | NocoDB database interface |
| longhorn | sector7.helloworlddao.com | 192.168.2.200 | Longhorn storage UI |
| grafana | sector7.helloworlddao.com | 192.168.2.200 | Grafana monitoring |

## Service Access Matrix

| Service | Internal URL | External URL | Namespace |
|---------|-------------|--------------|-----------|
| Ingress | http://192.168.2.200 | https://sector7.helloworlddao.com | ingress-nginx |
| AppFlowy | http://appflowy.sector7.helloworlddao.com | https://appflowy.sector7.helloworlddao.com | appflowy |
| n8n | http://n8n.sector7.helloworlddao.com | https://n8n.sector7.helloworlddao.com | n8n |
| Nextcloud | http://nextcloud.sector7.helloworlddao.com | https://nextcloud.sector7.helloworlddao.com | nextcloud |
| NocoDB | http://nocodb.sector7.helloworlddao.com | https://nocodb.sector7.helloworlddao.com | nocodb |

## Troubleshooting

### Check Connectivity

```bash
# From Mini PC, test connectivity to:

# OPNsense gateway
ping 192.168.2.1

# Aurora node
ping 192.168.2.159

# library-wa-shi-tan node
ping 192.168.2.231

# Ingress LoadBalancer
ping 192.168.2.200
curl -I http://192.168.2.200

# k3s API server
curl -k https://192.168.2.159:6443
```

### Check MetalLB

```bash
kubectl get svc -n ingress-nginx
kubectl get ipaddresspool -n metallb-system
kubectl logs -n metallb-system -l app=metallb -l component=controller
```

### Common Issues

**Issue:** Services not accessible from LAN
- **Solution:** Add firewall rule to allow LAN → MetalLB pool (192.168.2.200-220)

**Issue:** External access not working
- **Solution:** Configure WAN port forwarding for 80/443 → 192.168.2.200

**Issue:** DNS not resolving sector7.helloworlddao.com locally
- **Solution:** Add Unbound DNS overrides in OPNsense

---

**Last Updated:** 2025-12-01
**Network Subnet:** 192.168.2.0/24
**Gateway:** 192.168.2.1 (OPNsense)
**External IP:** 71.73.220.69
