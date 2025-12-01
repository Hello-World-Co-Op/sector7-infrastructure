# Sector7 Infrastructure - Network Topology

## Network Diagram

```
Internet
   │
   ├─► Modem
   │
   ├─► Protectli Firewall (OPNsense)
   │      └─► WAN: DHCP from modem
   │      └─► LAN: 192.168.1.0/24
   │
   ├─► Router
   │      └─► Gateway: 192.168.1.1
   │      └─► DHCP Server for 192.168.1.0/24
   │
   ├─► 5-Port Switch
   │
   ├─► Aurora Tower (k3s control plane)
   │      └─► IP: 192.168.1.50
   │      └─► Role: k3s server + worker
   │      └─► Specs: AMD Ryzen 5000, 32GB RAM, 2TB
   │
   ├─► Dell OptiPlex (k3s worker)
   │      └─► IP: 192.168.1.51
   │      └─► Role: k3s agent
   │      └─► Specs: i7 vPro, 32GB RAM, 2TB
   │
   └─► Mini PC (management)
          └─► IP: 192.168.1.106
          └─► Role: kubectl management, development
          └─► Specs: Ryzen 7 PRO, 32GB RAM, 2TB
```

## IP Address Allocation

### Static/Reserved IPs

| IP Address | Device | Purpose | Status |
|------------|--------|---------|--------|
| 192.168.1.1 | Gateway | Router/OPNsense gateway | Active |
| 192.168.1.50 | aurora | k3s control plane + worker | Active |
| 192.168.1.51 | optiplex | k3s worker node | Active |
| 192.168.1.106 | mini-pc | kubectl management | Active |
| 192.168.1.200-220 | MetalLB Pool | LoadBalancer service IPs | Reserved |

### LoadBalancer IP Assignments

| IP Address | Service | Namespace | Purpose |
|------------|---------|-----------|---------|
| 192.168.1.200 | traefik | traefik | Ingress controller (HTTP/HTTPS) |
| 192.168.1.201-220 | - | - | Available for new LoadBalancer services |

## Network Services

### Kubernetes Cluster
- **k3s Version:** v1.33.5+k3s1
- **Nodes:** 2 (1 control plane + worker, 1 worker)
- **CNI:** Flannel (default k3s)
- **Service CIDR:** 10.43.0.0/16
- **Pod CIDR:** 10.42.0.0/16

### MetalLB Configuration
- **Mode:** Layer 2 (L2Advertisement)
- **IP Pool:** 192.168.1.200-192.168.1.220
- **Namespace:** metallb-system

### Traefik Ingress
- **LoadBalancer IP:** 192.168.1.200
- **HTTP Port:** 80 → 31436 (NodePort)
- **HTTPS Port:** 443 → 32251 (NodePort)
- **Dashboard Port:** 8080 (ClusterIP only)

## OPNsense Firewall Configuration Needed

### 1. Firewall Rules (LAN Interface)

Allow internal traffic to Kubernetes services:

```
Action: Pass
Interface: LAN
Protocol: TCP/UDP
Source: LAN net
Destination: 192.168.1.50-51 (k3s nodes)
Description: Allow LAN access to k3s cluster nodes
```

```
Action: Pass
Interface: LAN
Protocol: TCP/UDP
Source: LAN net
Destination: 192.168.1.200-220 (MetalLB pool)
Description: Allow LAN access to k8s LoadBalancer services
```

### 2. Port Forwarding (WAN Interface)

For external access to services:

```
Interface: WAN
Protocol: TCP
Source: any
Source Port: any
Destination: WAN address
Destination Port: 80
Redirect Target IP: 192.168.1.200
Redirect Target Port: 80
Description: HTTP to Traefik Ingress
```

```
Interface: WAN
Protocol: TCP
Source: any
Source Port: any
Destination: WAN address
Destination Port: 443
Redirect Target IP: 192.168.1.200
Redirect Target Port: 443
Description: HTTPS to Traefik Ingress
```

### 3. NAT Outbound

Ensure NAT is enabled for outbound traffic from:
- 192.168.1.50 (aurora)
- 192.168.1.51 (optiplex)
- 192.168.1.200-220 (MetalLB pool)

### 4. DNS Configuration

#### Option A: OPNsense Unbound DNS

Add local domain overrides for `*.sector7.helloworlddao.com`:

```
Domain: sector7.helloworlddao.com
IP Address: 192.168.1.200
Description: Wildcard for all sector7 services
```

Specific overrides:
- `n8n.sector7.helloworlddao.com` → 192.168.1.200
- `nextcloud.sector7.helloworlddao.com` → 192.168.1.200
- `nocodb.sector7.helloworlddao.com` → 192.168.1.200
- `appflowy.sector7.helloworlddao.com` → 192.168.1.200
- `longhorn.sector7.helloworlddao.com` → 192.168.1.200
- `grafana.sector7.helloworlddao.com` → 192.168.1.200

#### Option B: External DNS

Point public DNS records to your WAN IP:
- Requires port forwarding (80/443)
- Requires cert-manager for Let's Encrypt SSL
- Already configured in cluster

### 5. DHCP Reservations

Set static DHCP leases for:
- 192.168.1.50 → aurora MAC address
- 192.168.1.51 → optiplex MAC address
- 192.168.1.106 → mini-pc MAC address

## Security Considerations

### Firewall Best Practices

1. **Deny by Default:** Block all traffic not explicitly allowed
2. **Segment Networks:** Consider VLANs for management vs. services
3. **Rate Limiting:** Enable for WAN interface (protect against DDoS)
4. **IPS/IDS:** Enable Suricata for intrusion detection
5. **Geo-blocking:** Block unnecessary countries
6. **Logging:** Enable firewall logging for monitoring

### Recommended OPNsense Features to Enable

- **Suricata IDS/IPS:** Monitor and block malicious traffic
- **Unbound DNS:** Local DNS resolution with DNS-over-TLS upstream
- **HAProxy (optional):** Additional layer 7 load balancing
- **Let's Encrypt (optional):** SSL for OPNsense web UI
- **WireGuard/OpenVPN:** Remote access VPN
- **ACME Client:** Automatic SSL certificate management

## Service Access Matrix

| Service | Internal URL | External URL | Port | Namespace |
|---------|-------------|--------------|------|-----------|
| Traefik | http://192.168.1.200 | https://sector7.helloworlddao.com | 443 | traefik |
| n8n | https://n8n.sector7.helloworlddao.com | ✓ | 443 | n8n |
| Nextcloud | https://nextcloud.sector7.helloworlddao.com | ✓ | 443 | nextcloud |
| NocoDB | https://nocodb.sector7.helloworlddao.com | ✓ | 443 | nocodb |
| AppFlowy | https://appflowy.sector7.helloworlddao.com | ✓ | 443 | appflowy |
| Longhorn UI | https://longhorn.sector7.helloworlddao.com | ✓ | 443 | longhorn-system |
| Grafana | https://grafana.sector7.helloworlddao.com | ✓ | 443 | monitoring |

## Troubleshooting

### Check Connectivity

```bash
# From any LAN device, test connectivity to:

# Aurora node
ping 192.168.1.50

# OptiPlex node
ping 192.168.1.51

# Traefik LoadBalancer
ping 192.168.1.200
curl -I http://192.168.1.200

# k3s API server
curl -k https://192.168.1.50:6443
```

### Check MetalLB

```bash
kubectl get svc -n traefik
kubectl get ipaddresspool -n metallb-system
kubectl logs -n metallb-system -l app=metallb -l component=controller
```

### Check OPNsense Firewall Logs

1. Navigate to **Firewall → Log Files → Live View**
2. Filter by source: 192.168.1.50, 192.168.1.51, 192.168.1.200
3. Look for blocked traffic

### Common Issues

**Issue:** Services not accessible from LAN
- **Solution:** Add firewall rule to allow LAN → MetalLB pool (192.168.1.200-220)

**Issue:** External access not working
- **Solution:** Configure WAN port forwarding for 80/443 → 192.168.1.200

**Issue:** DNS not resolving sector7.helloworlddao.com locally
- **Solution:** Add Unbound DNS overrides in OPNsense

## Next Steps

1. Access OPNsense web interface (likely http://192.168.1.1)
2. Configure firewall rules as outlined above
3. Set up port forwarding for external access
4. Configure local DNS for internal resolution
5. Enable IDS/IPS for security monitoring
6. Test connectivity to all services

## References

- [OPNsense Documentation](https://docs.opnsense.org/)
- [MetalLB L2 Configuration](https://metallb.universe.tf/configuration/l2/)
- [k3s Networking](https://docs.k3s.io/networking)
- [Traefik Documentation](https://doc.traefik.io/traefik/)

---

**Last Updated:** 2025-11-13
**Network Subnet:** 192.168.1.0/24
**Gateway:** 192.168.1.1 (OPNsense/Router)
