# OPNsense Configuration Guide for Sector7 Infrastructure

This guide walks you through configuring your Protectli OPNsense firewall to work with the sector7 Kubernetes infrastructure.

## Prerequisites

- OPNsense installed on Protectli device
- Access to OPNsense web interface (typically http://192.168.1.1)
- Default credentials (change these after initial setup!)
- Network topology: Modem → OPNsense → Router → Switch → k8s nodes

## Step 1: Initial Access and Setup

### 1.1 Access OPNsense Web Interface

1. Open browser and navigate to: `http://192.168.1.1`
2. Login with default credentials:
   - Username: `root`
   - Password: `opnsense` (or whatever you set during installation)

### 1.2 Change Default Password

1. Navigate to: **System → Access → Users**
2. Click edit icon for `root` user
3. Set a strong password
4. Save changes

### 1.3 Configure Interfaces

1. Navigate to: **Interfaces → Assignments**
2. Verify:
   - **WAN:** Connected to modem
   - **LAN:** Connected to router (192.168.1.0/24 network)

## Step 2: DHCP Static Mappings

Reserve IPs for your Kubernetes nodes to prevent IP changes.

### 2.1 Get MAC Addresses

First, get the MAC addresses of your nodes. From your Mini PC, run:

```bash
# Aurora
ssh aurora@192.168.1.50 "ip link show | grep -A 1 enp"

# OptiPlex
ssh aurora@192.168.1.51 "ip link show | grep -A 1 enp"
```

### 2.2 Create Static DHCP Leases

1. Navigate to: **Services → DHCPv4 → [LAN]**
2. Scroll to **DHCP Static Mappings**
3. Click **+** to add new mapping

**For Aurora (k3s control plane):**
- **MAC Address:** [Your aurora MAC]
- **IP Address:** 192.168.1.50
- **Hostname:** aurora
- **Description:** k3s control plane + worker
- Click **Save**

**For OptiPlex (k3s worker):**
- **MAC Address:** [Your optiplex MAC]
- **IP Address:** 192.168.1.51
- **Hostname:** optiplex
- **Description:** k3s worker node
- Click **Save**

**For Mini PC (management):**
- **MAC Address:** [Your mini-pc MAC]
- **IP Address:** 192.168.1.106
- **Hostname:** mini-pc
- **Description:** kubectl management
- Click **Save**

4. Click **Apply changes**

## Step 3: Firewall Rules for Kubernetes Access

Allow traffic from LAN to your Kubernetes cluster.

### 3.1 Allow Access to k8s Nodes

1. Navigate to: **Firewall → Rules → LAN**
2. Click **+** to add new rule

**Rule 1: Allow LAN → k8s Nodes**
- **Action:** Pass
- **Interface:** LAN
- **Direction:** in
- **TCP/IP Version:** IPv4
- **Protocol:** TCP/UDP
- **Source:** LAN net
- **Destination:** Type "Network or Alias"
  - Address: `192.168.1.50/31` (covers .50 and .51)
- **Description:** Allow LAN access to k8s cluster nodes
- **Log:** Check this to monitor access
- Click **Save**

**Rule 2: Allow LAN → MetalLB LoadBalancer IPs**
- **Action:** Pass
- **Interface:** LAN
- **Direction:** in
- **TCP/IP Version:** IPv4
- **Protocol:** TCP/UDP
- **Source:** LAN net
- **Destination:** Type "Network or Alias"
  - Address: `192.168.1.200/28` (covers .200-.215)
- **Description:** Allow LAN access to k8s LoadBalancer services
- **Log:** Check this
- Click **Save**

3. Click **Apply changes**

### 3.2 Allow k8s Nodes Internet Access

These rules allow your nodes to pull container images and updates.

1. Still in **Firewall → Rules → LAN**
2. Click **+** to add new rule

**Rule 3: Allow k8s Nodes → Internet**
- **Action:** Pass
- **Interface:** LAN
- **Direction:** in
- **TCP/IP Version:** IPv4
- **Protocol:** any
- **Source:** Type "Network or Alias"
  - Address: `192.168.1.50/31`
- **Destination:** any
- **Description:** Allow k8s nodes internet access
- Click **Save**

3. Click **Apply changes**

## Step 4: Port Forwarding for External Access

Forward external HTTP/HTTPS traffic to Traefik ingress controller.

### 4.1 Create Port Forward Rules

1. Navigate to: **Firewall → NAT → Port Forward**
2. Click **+** to add new rule

**Rule 1: HTTP (Port 80)**
- **Interface:** WAN
- **TCP/IP Version:** IPv4
- **Protocol:** TCP
- **Source:** any
- **Source port range:** any
- **Destination:** WAN address
- **Destination port range:** HTTP (80)
- **Redirect target IP:** 192.168.1.200 (Traefik LoadBalancer)
- **Redirect target port:** HTTP (80)
- **Description:** HTTP to Traefik Ingress
- **Filter rule association:** Add associated filter rule
- Click **Save**

**Rule 2: HTTPS (Port 443)**
- **Interface:** WAN
- **TCP/IP Version:** IPv4
- **Protocol:** TCP
- **Source:** any
- **Source port range:** any
- **Destination:** WAN address
- **Destination port range:** HTTPS (443)
- **Redirect target IP:** 192.168.1.200
- **Redirect target port:** HTTPS (443)
- **Description:** HTTPS to Traefik Ingress
- **Filter rule association:** Add associated filter rule
- Click **Save**

3. Click **Apply changes**

**Note:** The port forwards will automatically create corresponding WAN firewall rules.

## Step 5: Local DNS Configuration

Configure DNS so internal devices can resolve `*.sector7.helloworlddao.com` to your Traefik LoadBalancer.

### 5.1 Enable Unbound DNS

1. Navigate to: **Services → Unbound DNS → General**
2. Ensure **Enable** is checked
3. Scroll to **Network Interfaces:** Select LAN
4. Click **Save**
5. Click **Apply**

### 5.2 Add Host Overrides

1. Navigate to: **Services → Unbound DNS → Overrides**
2. Scroll to **Host Overrides**
3. Click **+** to add each service

**Add these overrides (one by one):**

| Host | Domain | IP Address | Description |
|------|--------|------------|-------------|
| n8n | sector7.helloworlddao.com | 192.168.1.200 | n8n workflow automation |
| nextcloud | sector7.helloworlddao.com | 192.168.1.200 | Nextcloud file sharing |
| nocodb | sector7.helloworlddao.com | 192.168.1.200 | NocoDB database interface |
| appflowy | sector7.helloworlddao.com | 192.168.1.200 | AppFlowy project management |
| longhorn | sector7.helloworlddao.com | 192.168.1.200 | Longhorn storage UI |
| grafana | sector7.helloworlddao.com | 192.168.1.200 | Grafana monitoring |
| traefik | sector7.helloworlddao.com | 192.168.1.200 | Traefik dashboard |

For each:
- **Host:** [service name]
- **Domain:** sector7.helloworlddao.com
- **IP:** 192.168.1.200
- **Description:** [service description]
- Click **Save**

4. Click **Apply**

### 5.3 Test DNS Resolution

From any device on your LAN:

```bash
nslookup n8n.sector7.helloworlddao.com
# Should resolve to 192.168.1.200

nslookup nextcloud.sector7.helloworlddao.com
# Should resolve to 192.168.1.200
```

## Step 6: Security Hardening (Recommended)

### 6.1 Enable Suricata IDS/IPS

1. Navigate to: **Services → Intrusion Detection → Administration**
2. Check **Enabled**
3. Check **IPS mode** (to block, not just detect)
4. Select **Interfaces:** WAN
5. Click **Download & Update Rules** (this may take a few minutes)
6. Click **Save**

### 6.2 Configure Firewall Logging

1. Navigate to: **Firewall → Log Files → Settings**
2. Set **Log firewall default blocks:** Checked
3. Set **Log packets matched from the default pass rules:** Checked
4. Click **Save**

### 6.3 Enable DNS-over-TLS (Optional but Recommended)

1. Navigate to: **Services → Unbound DNS → General**
2. Scroll to **DNS over TLS**
3. Check **Use SSL/TLS for outgoing queries**
4. Add upstream DNS servers:
   - Cloudflare: `1.1.1.1@853`
   - Quad9: `9.9.9.9@853`
5. Click **Save** and **Apply**

### 6.4 Set Up Automatic Updates

1. Navigate to: **System → Firmware → Settings**
2. Check **Automatic update check**
3. Set schedule for automatic checks
4. Click **Save**

## Step 7: Monitoring and Maintenance

### 7.1 Monitor Firewall Logs

1. Navigate to: **Firewall → Log Files → Live View**
2. Watch for blocked traffic to/from your k8s nodes
3. Filter by IP: 192.168.1.50, 192.168.1.51, 192.168.1.200

### 7.2 Check System Status

1. Navigate to: **Lobby** (Dashboard)
2. Monitor:
   - CPU usage
   - Memory usage
   - Interface traffic
   - Active states (connections)

### 7.3 Review IDS Alerts

1. Navigate to: **Services → Intrusion Detection → Alerts**
2. Review any alerts for suspicious activity
3. Whitelist false positives if needed

## Step 8: Backup Configuration

**Important:** Always backup your configuration after making changes!

1. Navigate to: **System → Configuration → Backups**
2. Scroll to **Download configuration**
3. Click **Download** to save XML backup
4. Store securely (encrypted location)

### Restore Configuration

If needed, restore from:
1. Navigate to: **System → Configuration → Backups**
2. Under **Restore configuration**, click **Choose File**
3. Select your backup XML
4. Click **Restore configuration**

## Testing Checklist

After configuration, verify everything works:

### Internal Access Tests (from LAN device)

```bash
# Test Traefik LoadBalancer
curl -I http://192.168.1.200
# Should return HTTP response

# Test DNS resolution
nslookup n8n.sector7.helloworlddao.com
# Should resolve to 192.168.1.200

# Test HTTPS (if cert-manager has issued certs)
curl -I https://n8n.sector7.helloworlddao.com
# Should return HTTPS response

# Test Kubernetes API
curl -k https://192.168.1.50:6443
# Should return k8s API response
```

### External Access Tests (from outside your network)

1. Find your public IP: `curl ifconfig.me`
2. From external device/network:

```bash
# Test HTTP redirect to HTTPS
curl -I http://YOUR_PUBLIC_IP
# Should redirect to HTTPS

# Test HTTPS
curl -I https://YOUR_PUBLIC_IP
# Should work (might show certificate warning if using IP)

# Test with domain (if DNS configured)
curl -I https://n8n.sector7.helloworlddao.com
```

## Troubleshooting

### Issue: Services not accessible from LAN

**Symptoms:** Can't reach http://192.168.1.200 from local devices

**Solutions:**
1. Check firewall rules: **Firewall → Rules → LAN**
2. Verify MetalLB is working: `kubectl get svc -n traefik`
3. Check firewall logs: **Firewall → Log Files → Live View**
4. Ping test: `ping 192.168.1.200`

### Issue: DNS not resolving locally

**Symptoms:** `nslookup n8n.sector7.helloworlddao.com` fails

**Solutions:**
1. Verify Unbound is running: **Services → Unbound DNS → General**
2. Check host overrides: **Services → Unbound DNS → Overrides**
3. Restart Unbound: **Services → Unbound DNS → General** → **Restart**
4. Check client DNS settings (should point to 192.168.1.1)

### Issue: External access not working

**Symptoms:** Can't access services from internet

**Solutions:**
1. Verify port forwards: **Firewall → NAT → Port Forward**
2. Check WAN firewall rules: **Firewall → Rules → WAN**
3. Verify public IP: `curl ifconfig.me`
4. Check ISP doesn't block ports 80/443
5. Test with direct IP first, then domain

### Issue: Certificate errors

**Symptoms:** Browser shows SSL/TLS errors

**Solutions:**
1. Check cert-manager status: `kubectl get certificates -A`
2. Verify DNS is pointing to your public IP
3. Check Let's Encrypt rate limits
4. Review cert-manager logs: `kubectl logs -n cert-manager -l app=cert-manager`

## Advanced Configuration (Optional)

### VPN Access (WireGuard)

For secure remote access to your homelab:

1. Navigate to: **VPN → WireGuard → Instances**
2. Follow OPNsense WireGuard setup guide
3. Create peer for mobile/laptop devices
4. Access services via VPN without exposing ports

### HAProxy for Additional Load Balancing

1. Navigate to: **Services → HAProxy**
2. Configure backend servers (k8s nodes)
3. Set up health checks
4. Use as alternative to MetalLB for advanced routing

### Geo-blocking

Restrict access to specific countries:

1. Install plugin: **System → Firmware → Plugins** → search "geoip"
2. Navigate to: **Firewall → Aliases** → **GeoIP**
3. Create alias with allowed/blocked countries
4. Use in firewall rules

## Useful OPNsense Commands (SSH/Console)

```bash
# Restart network interfaces
/usr/local/etc/rc.d/netif restart

# Restart firewall
/usr/local/etc/rc.d/pf restart

# Restart Unbound DNS
/usr/local/etc/rc.d/unbound restart

# View firewall logs
clog /var/log/filter.log

# Check interface status
ifconfig

# Test connectivity
ping 192.168.1.200
```

## Regular Maintenance Schedule

### Daily
- Review firewall logs for anomalies
- Check system resource usage

### Weekly
- Review IDS/IPS alerts
- Check for firmware updates
- Backup configuration

### Monthly
- Update firmware (if available)
- Review firewall rules for optimization
- Test disaster recovery procedures

## Additional Resources

- [OPNsense Documentation](https://docs.opnsense.org/)
- [OPNsense Forum](https://forum.opnsense.org/)
- [Protectli Documentation](https://protectli.com/kb/)
- [Sector7 Network Topology](./NETWORK-TOPOLOGY.md)

## Support

For issues specific to this setup:
1. Check firewall logs first
2. Review k8s cluster status: `kubectl get pods -A`
3. Test connectivity step-by-step
4. Consult sector7 documentation in this repo

---

**Configuration Guide Version:** 1.0
**Last Updated:** 2025-11-13
**OPNsense Version:** 25.x compatible
**Tested On:** Protectli VP2420
