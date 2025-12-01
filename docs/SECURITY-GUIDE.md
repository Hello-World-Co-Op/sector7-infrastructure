# Sector7 Security Guide

## 🔒 Security Hardening Completed

### ✅ Infrastructure Security (DONE)

**1. fail2ban Installed & Configured**
- **Aurora Tower**: Active, monitoring SSH
- **OptiPlex**: Active, monitoring SSH
- Configuration:
  - 3 failed SSH attempts = 2 hour ban
  - Aggressive mode: 2 attempts in 5 min = 24 hour ban
- Protection against: Brute force SSH attacks

**2. Traefik Dashboard Secured**
- ❌ Removed insecure public access on port 8080
- ✅ Now requires HTTPS + authentication
- Access: https://traefik.sector7.helloworlddao.com
  - Username: `admin`
  - Password: `Sector7Admin2025!`
- **IMPORTANT**: Change this password after first login!

**3. Network Firewall (UFW)**
- Active on all nodes
- Default: Deny incoming, allow outgoing
- Only essential ports open

---

## 🚀 Kubernetes Security Recommendations

### 1. Network Policies (Implement Before Going Live)

Network policies control pod-to-pod communication. Right now, any pod can talk to any other pod.

**Create basic network policies:**

```bash
# Save this as cluster/05-security/network-policies.yaml
---
# Default deny all ingress traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress

---
# Allow Traefik to reach application pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-traefik
  namespace: default
spec:
  podSelector:
    matchLabels:
      expose: "true"  # Add this label to pods that need external access
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: traefik
```

### 2. Pod Security Standards

Add to your namespace definitions:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production-namespace
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 3. Resource Limits

Prevent resource exhaustion:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
  namespace: production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
```

### 4. RBAC (Role-Based Access Control)

k3s already has RBAC enabled. For team access to Kubernetes (if needed):

```bash
# Create read-only user for monitoring
kubectl create serviceaccount monitoring-user -n monitoring
kubectl create clusterrolebinding monitoring-viewer \\
  --clusterrole=view --serviceaccount=monitoring:monitoring-user
```

**IMPORTANT**: Team members should NEVER need direct Kubernetes access. They access services via web interfaces.

---

## 🛡️ Application Security

### How Team Members Access Services

**They DON'T need:**
- SSH access to servers
- kubectl access
- Direct IP addresses
- VPN connections

**They DO need:**
- Domain URLs (e.g., https://n8n.sector7.helloworlddao.com)
- User accounts created in each service
- Strong passwords (use a password manager!)

### Service-Level Authentication

Each application has its own auth:

| Service | Admin Setup | User Management |
|---------|-------------|-----------------|
| **n8n** | Set owner email/password on first access | Settings → Users |
| **Nextcloud** | Create admin during setup | Users menu |
| **NocoDB** | Email signup for first user | Team & Auth tab |
| **Supabase** | Project dashboard | Auth → Users |
| **AppFlowy** | Team workspace creation | Workspace settings |

### Security Best Practices for Applications

1. **Enable 2FA** where supported (Nextcloud, Supabase)
2. **Use strong passwords**: min 16 chars, mix of types
3. **Separate user roles**: Admin vs. regular users
4. **Regular backups**: Longhorn provides snapshots
5. **Update regularly**: Check for security patches

---

## 🌐 Router & Firewall Setup

### Phase 1: Router Security (DO THIS FIRST)

1. **Access Router Admin Panel**
   - URL: http://192.168.1.1 (or check router label)
   - Login with current credentials

2. **Change Default Password**
   - Look for: Security / Administration / System
   - Use a strong unique password
   - Store in password manager

3. **Enable Security Features**
   - ✅ SPI Firewall (Stateful Packet Inspection)
   - ✅ DoS Protection
   - ✅ Disable WPS (WiFi Protected Setup)
   - ✅ Change WiFi password if it's default
   - ✅ Disable remote management (unless you need it)

4. **Update Firmware**
   - Check for latest firmware version
   - Apply updates if available

### Phase 2: Dedicated Firewall Device (RECOMMENDED)

**Why you need this:**
- Enterprise-grade security between internet and your cluster
- Deep packet inspection
- VPN server for secure remote access
- Traffic monitoring and logging
- IDS/IPS (Intrusion Detection/Prevention)

**Recommended Device: Protectli FW4B** (~$250 on Newegg)

**Specs:**
- Intel quad-core CPU
- 4x Intel NICs
- 8GB RAM, 64GB mSATA
- Fanless, low power (<10W)
- Runs pfSense or OPNsense

**Alternative Options:**
- Netgate 4100 (~$500) - Official pfSense appliance
- QOTOM Q330G4 (~$200) - Similar to Protectli
- DIY: Old mini PC + 2+ NICs + pfSense (Free)

### Phase 3: Firewall Configuration

**Network Topology:**
```
Internet → Router (192.168.1.1)
            ↓
          Firewall Device (WAN: 192.168.1.2, LAN: 10.0.0.1)
            ↓
          Internal Network (10.0.0.0/24)
            ↓
          Traefik LoadBalancer (10.0.0.200)
            ↓
          Services
```

**pfSense Setup Guide:**
1. Install pfSense on firewall device
2. Configure WAN (connect to router)
3. Configure LAN (internal network)
4. Move cluster to LAN network
5. Configure NAT/Port Forwarding:
   - Port 80 → Traefik (10.0.0.200:80)
   - Port 443 → Traefik (10.0.0.200:443)
6. Enable Snort/Suricata (IDS/IPS)
7. Set up OpenVPN for remote admin access

---

## 🔐 SSH Hardening (Remaining Tasks)

### Current SSH Status
- ✅ Root login requires SSH keys
- ✅ Empty passwords disabled
- ✅ fail2ban protecting against brute force
- ⚠️ Password authentication still enabled

### Optional: Disable Password Auth (Key-only)

**ONLY do this if you:**
1. Have your SSH key working
2. Have saved a backup of your private key
3. Understand you can't login without the key

```bash
# On each node (Aurora, OptiPlex):
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### Disable X11 Forwarding

```bash
# On each node:
sudo sed -i 's/^X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

---

## 🔍 Security Monitoring

### Check fail2ban Status

```bash
# On Aurora or OptiPlex:
sudo fail2ban-client status sshd

# View banned IPs:
sudo fail2ban-client get sshd banned

# Unban an IP if needed:
sudo fail2ban-client set sshd unbanip 1.2.3.4
```

### Monitor Kubernetes Security

```bash
# Check for pods with security issues:
kubectl get pods --all-namespaces -o json | \\
  jq '.items[] | select(.spec.securityContext.runAsRoot == true)'

# Review RBAC permissions:
kubectl get clusterrolebindings

# Check for privileged containers:
kubectl get pods --all-namespaces -o json | \\
  jq '.items[] | select(.spec.containers[].securityContext.privileged == true)'
```

---

## 📋 Pre-Launch Security Checklist

### Before Exposing to Internet:

- [ ] Router admin password changed
- [ ] Router firmware updated
- [ ] Router firewall enabled
- [ ] Firewall device installed and configured (if using)
- [ ] All application admin passwords set
- [ ] Traefik dashboard password changed
- [ ] fail2ban active on all nodes
- [ ] SSH hardened (password auth disabled)
- [ ] Network policies implemented
- [ ] DNS A records configured
- [ ] SSL certificates working (Let's Encrypt)
- [ ] Team members have proper user accounts (not admin)
- [ ] Backup system tested

### After Going Live:

- [ ] Monitor fail2ban logs for attacks
- [ ] Check Traefik dashboard for unusual traffic
- [ ] Review Kubernetes pod logs regularly
- [ ] Test backups monthly
- [ ] Update services quarterly
- [ ] Review and rotate passwords every 90 days

---

## 🚨 Incident Response

### If You Detect a Breach:

1. **Immediate Actions:**
   ```bash
   # Disable port forwarding at router
   # Or disconnect firewall WAN interface

   # Check for unauthorized access:
   sudo lastlog
   sudo last -a

   # Check fail2ban logs:
   sudo tail -100 /var/log/fail2ban.log
   ```

2. **Investigation:**
   - Check Traefik access logs
   - Review Kubernetes audit logs
   - Examine application logs

3. **Recovery:**
   - Rotate all passwords
   - Review and revoke API keys
   - Restore from known-good backup if needed

---

## 📞 Support Resources

- **k3s Security**: https://docs.k3s.io/security
- **Traefik Security**: https://doc.traefik.io/traefik/
- **pfSense Docs**: https://docs.netgate.com/pfsense/
- **fail2ban Wiki**: https://github.com/fail2ban/fail2ban/wiki

---

## 📝 Credentials Summary

**Save these in a password manager!**

| Service | URL | Username | Password | Notes |
|---------|-----|----------|----------|-------|
| Router | http://192.168.1.1 | [your router user] | [CHANGE ME] | Admin access |
| Traefik Dashboard | https://traefik.sector7.helloworlddao.com | admin | Sector7Admin2025! | CHANGE AFTER FIRST LOGIN |
| Aurora SSH | 192.168.1.50 | degenotterdev | [SSH key] | Server admin |
| OptiPlex SSH | 192.168.1.51 | degenotterdev | [SSH key] | Server admin |

---

**Generated**: 2025-11-07
**Status**: Phase 1 Complete (fail2ban + Traefik secured)
**Next**: Router setup → Firewall device → Network policies
