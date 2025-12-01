# Sector7 Infrastructure Audit

**Latest Update**: 2025-11-25
**Status**: ✅ OPERATIONAL

> **Note**: For the current authoritative state, see [CURRENT-STATE.md](./CURRENT-STATE.md)
> This document contains historical audit information and architecture decisions.

---

## Update 2025-11-25: Current Verified State

### Cluster Status: ✅ OPERATIONAL

**Infrastructure**:
- k3s v1.33.5+k3s1 running on 2 nodes (aurora + optiplex)
- Network: 192.168.2.0/24 (migration completed)
- Ingress: ingress-nginx (NodePort mode at 192.168.2.159)
- Storage: local-path-provisioner (default)
- Cert-manager: Installed and running

**Working Services** (5):
1. Heimdall - Dashboard (http://sector7.helloworlddao.com)
2. n8n - Workflow automation (http://n8n.sector7.helloworlddao.com)
3. Nextcloud - File storage (http://nextcloud.sector7.helloworlddao.com)
4. NocoDB - Database UI (http://nocodb.sector7.helloworlddao.com)
5. Supabase - PostgreSQL database (internal)

**Removed Services**:
- ❌ AppFlowy - Removed due to database conflicts (2025-11-25)

**Changes from Previous State**:
- Replaced Traefik with ingress-nginx
- Removed Longhorn, using local-path-provisioner
- Removed MetalLB, using NodePort
- AppFlowy removed from cluster

---

## Historical Audit - 2025-11-13

### Original State Analysis

### Physical Network Topology (ACTUAL)

```
Internet
   │
Modem (ISP)
   │
Protectli Firewall (OPNsense)
   ├─ WAN: 71.73.220.69 (public IP)
   └─ LAN: 192.168.2.1/24
          │
      Spectrum Router
          ├─ WAN side: 192.168.2.217 (gets IP from OPNsense)
          └─ LAN side: 192.168.1.1/24
                 │
              5-port Switch
                 ├─ Aurora Tower: 192.168.1.50 (k3s control-plane)
                 ├─ Dell OptiPlex: 192.168.1.51 (k3s worker)
                 └─ Mini PC: 192.168.1.106 (management)
```

### Current IP Allocation

| Device | Network Interface | IP Address | Gateway | Network | Role |
|--------|------------------|------------|---------|---------|------|
| OPNsense (Protectli) | WAN (igc1) | 71.73.220.69 | ISP | Public | Firewall WAN |
| OPNsense (Protectli) | LAN (igc0) | 192.168.2.1/24 | - | 192.168.2.0/24 | Firewall LAN |
| Spectrum Router | WAN | 192.168.2.217 | 192.168.2.1 | 192.168.2.0/24 | Router WAN |
| Spectrum Router | LAN | 192.168.1.1/24 | - | 192.168.1.0/24 | Router LAN |
| Aurora Tower | enp (?) | 192.168.1.50 | 192.168.1.1 | 192.168.1.0/24 | k3s control-plane |
| Dell OptiPlex | enp (?) | 192.168.1.51 | 192.168.1.1 | 192.168.1.0/24 | k3s worker |
| Mini PC | enp1s0 | 192.168.1.106 | 192.168.1.1 | 192.168.1.0/24 | kubectl management |
| Traefik LoadBalancer | Virtual (MetalLB) | 192.168.1.200 | - | 192.168.1.0/24 | k8s ingress |

### MAC Addresses

| Device | MAC Address | Visible in Spectrum Router |
|--------|-------------|---------------------------|
| Aurora Tower | a0:ad:9f:85:ce:72 | ❌ NO |
| Dell OptiPlex | 64:00:6a:8c:ea:e9 | ✅ YES (Dell 8c:ea:e9) |
| Mini PC | (unknown) | ✅ YES (knower-SER) |
| Traefik (Virtual) | N/A (MetalLB) | ❌ NO (virtual IP) |

### Kubernetes Cluster Configuration

**Cluster Info:**
- **Distribution:** k3s v1.33.5+k3s1
- **Nodes:** 2 (aurora control-plane + worker, optiplex worker)
- **CNI:** Flannel (default)
- **Service CIDR:** 10.43.0.0/16
- **Pod CIDR:** 10.42.0.0/16

**Infrastructure Components:**
- ✅ MetalLB: Configured for 192.168.1.200-220
- ✅ Traefik: LoadBalancer at 192.168.1.200
- ✅ cert-manager: Running
- ✅ Longhorn: Running (some pods flapping)

**Applications:**
- ❌ NOT deployed yet (no apps running)

---

## Problems Identified

### Problem 1: Double NAT
**Issue:** Traffic must traverse TWO NAT boundaries to reach k8s services.

```
Internet → OPNsense NAT → Spectrum Router NAT → k8s services
```

**Impact:**
- Requires port forwarding on BOTH devices
- Spectrum router app won't allow manual IP entry
- Can't forward to MetalLB virtual IP (192.168.1.200)
- Complex troubleshooting
- Performance overhead

### Problem 2: Spectrum Router Limitations
**Issue:** Spectrum router managed only via mobile app with restrictions.

**Limitations:**
- Cannot access web interface (shows static QR code page)
- Port forwarding ONLY to devices visible in DHCP table
- Cannot manually enter IP addresses
- Aurora Tower not visible (likely static IP)
- MetalLB virtual IPs not visible

**Impact:**
- Cannot forward directly to Traefik LoadBalancer (192.168.1.200)
- Cannot forward to Aurora Tower (192.168.1.50)
- Must forward to OptiPlex (192.168.1.51) as workaround

### Problem 3: Network Segmentation
**Issue:** OPNsense on 192.168.2.x, k8s cluster on 192.168.1.x

**Impact:**
- OPNsense cannot directly manage k8s network
- Cannot use OPNsense DNS for local resolution
- Double NAT required
- Complex firewall rule management

### Problem 4: Aurora Tower Invisibility
**Issue:** Aurora Tower (primary k3s control-plane) not visible to Spectrum router.

**Possible Causes:**
- Static IP configuration (not DHCP)
- Network interface not broadcasting hostname
- DHCP lease expired but static IP configured

**Impact:**
- Cannot create DHCP reservation
- Cannot forward ports directly to Aurora
- Must rely on OptiPlex as entry point

### Problem 5: OPNsense Port Forwarding Misconfiguration
**Current Config:** OPNsense forwards 80/443 → 192.168.2.217 (Spectrum router)

**Issue:** Spectrum router is NOT forwarding to k8s yet, so traffic stops there.

---

## Root Cause Analysis

**Primary Issue:** Using ISP-provided Spectrum router as a network gateway creates limitations.

**Secondary Issue:** Double NAT architecture prevents clean port forwarding.

**Tertiary Issue:** Kubernetes cluster on different subnet than firewall.

---

## Recommended Solutions

### Option A: Single Network with OPNsense as Primary Router (RECOMMENDED)

**Description:** Eliminate double NAT by moving everything to 192.168.2.x network.

**Physical Topology:**
```
Internet → Modem → OPNsense (192.168.2.1)
                      │
                   5-port Switch
                      ├─ Aurora: 192.168.2.50
                      ├─ OptiPlex: 192.168.2.51
                      ├─ Mini PC: 192.168.2.106
                      ├─ Spectrum Router (AP mode): 192.168.2.217 (WiFi only)
                      └─ Traefik LB: 192.168.2.200
```

**Changes Required:**
1. Connect 5-port switch directly to OPNsense LAN port
2. Configure Spectrum router as Access Point (bridge mode)
3. Reconfigure k8s nodes to 192.168.2.x IPs
4. Update MetalLB pool to 192.168.2.200-220
5. Configure OPNsense DHCP for 192.168.2.0/24
6. Update OPNsense port forwarding to 192.168.2.200

**Advantages:**
- ✅ Single NAT (only OPNsense)
- ✅ Direct port forwarding to MetalLB IPs
- ✅ OPNsense manages all DHCP/DNS
- ✅ Local DNS resolution via OPNsense Unbound
- ✅ Full firewall control
- ✅ Clean, simple architecture

**Disadvantages:**
- ⚠️ Spectrum router may not support AP/bridge mode via app
- ⚠️ Requires reconfiguring all k8s nodes
- ⚠️ Requires updating MetalLB IP pool
- ⚠️ Some downtime during migration

**Complexity:** Medium (4-6 hours work)

---

### Option B: Keep Current Setup, Use OptiPlex as Entry Point

**Description:** Work around Spectrum router limitations by forwarding to OptiPlex.

**No Physical Changes Required**

**Changes:**
1. Configure Spectrum app to forward 80/443 to OptiPlex (192.168.1.51)
2. Rely on MetalLB to route traffic internally to Traefik (192.168.1.200)

**Advantages:**
- ✅ No network reconfiguration needed
- ✅ No k8s changes needed
- ✅ Quick to implement (minutes)

**Disadvantages:**
- ❌ Double NAT remains
- ❌ OptiPlex becomes single point of failure
- ❌ More complex troubleshooting
- ❌ Cannot use OPNsense DNS features
- ❌ Relies on Spectrum router limitations

**Complexity:** Low (immediate)

---

### Option C: Bridge Mode on Spectrum Router (if possible)

**Description:** Put Spectrum router in bridge/passthrough mode.

**Physical Topology:**
```
Internet → Modem → OPNsense → Spectrum Router (bridge) → 5-port Switch
```

**Changes:**
1. Enable bridge mode on Spectrum router (if available in app)
2. OPNsense DHCP serves 192.168.2.x to all devices
3. Spectrum router just passes traffic, doesn't NAT

**Advantages:**
- ✅ Single NAT (OPNsense)
- ✅ Keeps existing IP scheme initially
- ✅ Can gradually migrate to 192.168.2.x

**Disadvantages:**
- ❓ Unknown if Spectrum app allows bridge mode
- ⚠️ WiFi may stop working (depends on bridge implementation)

**Complexity:** Low-Medium (if supported)

---

## Comparison Matrix

| Feature | Option A (Recommended) | Option B (Quick Fix) | Option C (Bridge) |
|---------|----------------------|---------------------|-------------------|
| Single NAT | ✅ Yes | ❌ No | ✅ Yes |
| Port Forwarding | ✅ Clean | ⚠️ Workaround | ✅ Clean |
| DNS Control | ✅ OPNsense | ❌ Spectrum | ✅ OPNsense |
| Firewall Control | ✅ Full | ⚠️ Limited | ✅ Full |
| Complexity | Medium | Low | Low-Med |
| Downtime | 4-6 hours | Minutes | 1-2 hours |
| Long-term Maintainability | ✅ Excellent | ❌ Poor | ✅ Good |
| Requires k8s Reconfig | ✅ Yes | ❌ No | ⚠️ Maybe |

---

## Recommended Action Plan

### Phase 1: Immediate (Option B - Get Working Now)
1. Configure Spectrum router port forwarding:
   - Port 80 → OptiPlex (192.168.1.51)
   - Port 443 → OptiPlex (192.168.1.51)
2. Test external connectivity
3. Deploy applications

**Timeline:** 30 minutes
**Risk:** Low
**Outcome:** Services accessible, but not optimal architecture

---

### Phase 2: Proper Infrastructure (Option A - Do It Right)

**When:** After services are working and tested

1. **Preparation (Week 1)**
   - Document all current configurations
   - Backup all data and configs
   - Test Spectrum router in AP mode (research required)
   - Plan maintenance window

2. **Migration (Weekend/Off-hours)**
   - Physically reconnect: OPNsense → Switch → Devices
   - Configure Spectrum router as AP only
   - Reconfigure k8s nodes with 192.168.2.x IPs
   - Update MetalLB IP pool to 192.168.2.200-220
   - Update OPNsense port forwarding to 192.168.2.200
   - Configure OPNsense DNS with host overrides
   - Test connectivity

3. **Validation**
   - Verify all nodes online
   - Verify MetalLB working
   - Verify external access
   - Verify internal DNS resolution
   - Deploy test application

**Timeline:** 4-6 hours
**Risk:** Medium (requires careful execution)
**Outcome:** Clean, maintainable architecture

---

## Decision Required

**Question for you and your developer:**

1. **Short term:** Should we proceed with Option B (forward to OptiPlex) to get services working TODAY?

2. **Long term:** Do you want to invest time in Option A (proper reconfiguration) for a cleaner setup?

3. **Spectrum router:** Can you check if the Spectrum app has a "bridge mode" or "passthrough mode" option?

---

## Next Steps (Your Choice)

### If choosing Option B (Quick Fix):
1. Configure port forwarding in Spectrum app to OptiPlex
2. Test connectivity: `curl http://71.73.220.69`
3. Deploy applications
4. Plan Option A migration later

### If choosing Option A (Proper Setup):
1. Back up all current configs
2. Research Spectrum router AP mode
3. Schedule maintenance window
4. Create detailed migration checklist
5. Execute migration
6. Test and validate

### If choosing Option C (Bridge Mode):
1. Check Spectrum app for bridge/passthrough mode
2. If available, enable it
3. Reconfigure OPNsense DHCP
4. Test and validate

---

**What would you like to do?**

---

**Document Version:** 1.1
**Created:** 2025-11-13
**Updated:** 2025-11-15
**Status:** Major Issues Resolved - Port Forwarding Pending

---

## UPDATE: 2025-11-15 - Issues Diagnosed and Resolved

### Critical Issues Fixed

#### 1. MetalLB Speakers Communication Failure **[RESOLVED]**

**Problem:** MetalLB speakers on both nodes couldn't communicate on port 7946 (TCP/UDP), preventing LoadBalancer IP assignment.

**Root Cause:** UFW firewall blocking port 7946 on both Aurora and OptiPlex.

**Fix Applied:**
```bash
# On both nodes:
sudo ufw allow 7946/tcp
sudo ufw allow 7946/udp
```

**Result:** ✅ MetalLB speakers successfully joined, LoadBalancer IP (192.168.1.200) now functional.

**Verification:**
```bash
# Traefik LoadBalancer is now responding:
curl -I http://192.168.1.200
# Returns: HTTP/1.1 308 Permanent Redirect (redirecting to HTTPS)

curl -I -k https://192.168.1.200
# Returns: HTTP/2 404 (working, no apps deployed yet)
```

---

#### 2. Longhorn CSI Plugin CrashLoopBackOff on OptiPlex **[PARTIALLY RESOLVED]**

**Problem:** `longhorn-csi-plugin` pod on OptiPlex in CrashLoopBackOff (7000+ restarts).

**Root Cause:** Docker containers running alongside Kubernetes on OptiPlex creating conflicting iptables rules.

**Discovery:** OptiPlex is running standalone Docker workloads:
- linkstack_app
- nginx_optiplex
- nocodb_persistence
- nextcloud_app
- plex_server
- postgres_persistence

These containers use Docker bridge networks (172.21.x.x, 172.19.x.x, 172.20.x.x) that interfere with Kubernetes pod-to-service communication (10.42.x.x → 10.43.x.x).

**Current Status:**
- Aurora's longhorn-csi-plugin: ✅ Running (3/3)
- OptiPlex's longhorn-csi-plugin: ❌ CrashLoopBackOff (2/3)
  - Error: Cannot connect to `longhorn-backend:9500` (timeout)

**Impact:** Minimal - Longhorn storage still functional via Aurora node. OptiPlex can't provision local storage volumes.

**Recommended Solutions (choose one):**
1. **Migrate Docker workloads to Kubernetes** (best long-term)
2. **Stop Docker containers** if not critical
3. **Configure Docker daemon** with `--iptables=false` (requires Docker restart)
4. **Accept current state** - OptiPlex CSI plugin not critical for basic operation

---

### Current Cluster Status

**Infrastructure:** ✅ ALL WORKING
- k3s cluster: ✅ Both nodes Ready
- MetalLB: ✅ Working (192.168.1.200 assigned)
- Traefik: ✅ Responding on HTTP/HTTPS
- cert-manager: ✅ Running
- Longhorn: ⚠️ Working (Aurora only)

**Resource Usage:** Very light
- Aurora: 1% CPU, 7% memory (2.6GB/30GB)
- OptiPlex: Metrics pending, estimated similar

**Ports Opened on Both Nodes:**
- 22/tcp (SSH)
- 80/tcp (HTTP)
- 443/tcp (HTTPS)
- 6443/tcp (Kubernetes API)
- 7946/tcp+udp (MetalLB)
- 8080/tcp (Dashboard)

---

### Network Architecture Summary

**Current (Double NAT):**
```
Internet (71.73.220.69)
   ↓
Modem
   ↓
OPNsense Firewall (192.168.2.1)
   ↓ [Port forward: 80/443 → 192.168.2.217]
Spectrum Router (192.168.1.1)
   ↓ [Need to configure: 80/443 → 192.168.1.200]
5-port Switch
   ↓
Traefik LoadBalancer (192.168.1.200) ✅ WORKING
   ↓
k8s Services (Traefik ingress)
```

---

### Next Steps - External Access Configuration

#### Step 1: Verify OPNsense Port Forwarding
Current config (per docs):
- WAN 80 → 192.168.2.217 (Spectrum Router)
- WAN 443 → 192.168.2.217 (Spectrum Router)

**Action:** Already configured ✅

#### Step 2: Configure Spectrum Router Port Forwarding
**PENDING - Required Action:**

Using Spectrum mobile app:
1. Open Spectrum app
2. Navigate to: Network → Port Forwarding
3. Create two rules:

**Rule 1: HTTP**
- External Port: 80
- Internal IP: 192.168.1.200 (Traefik LoadBalancer)
- Internal Port: 80
- Protocol: TCP

**Rule 2: HTTPS**
- External Port: 443
- Internal IP: 192.168.1.200 (Traefik LoadBalancer)
- Internal Port: 443
- Protocol: TCP

**Challenge:** Spectrum app may only show DHCP-visible devices. If 192.168.1.200 is not visible:
- **Workaround:** Forward to OptiPlex (192.168.1.51) instead
- MetalLB will still route to Traefik LoadBalancer

#### Step 3: Test External Access
```bash
# From outside the network:
curl -I http://71.73.220.69
# Should return Traefik response

curl -I -k https://71.73.220.69
# Should return Traefik HTTPS response
```

#### Step 4: Configure DNS (After Port Forwarding Works)
Point DNS records for `*.sector7.helloworlddao.com` → `71.73.220.69`

---

### Recommendations

#### Immediate (Do Now)
1. ✅ **DONE:** Fixed MetalLB port 7946 blocking
2. ⏳ **PENDING:** Configure Spectrum router port forwarding (80/443 → 192.168.1.200 or .51)
3. ⏳ **TEST:** Verify external access works

#### Short Term (Next Week)
1. **Deploy applications** to test full stack
2. **Configure DNS** for sector7.helloworlddao.com
3. **Decide on Docker containers** - migrate to k8s or isolate networking
4. **Enable OPNsense DNS** overrides for local resolution

#### Long Term (Next Month)
1. **Consider Option A migration** - eliminate double NAT
2. **Move all workloads to Kubernetes** for unified management
3. **Implement monitoring** - Prometheus/Grafana alerts
4. **Set up automated backups** via Longhorn snapshots

---

### Device Specifications - Verified 2025-11-15

**Aurora (192.168.1.50) - Control Plane + Worker:**
- CPU: AMD Ryzen 5 5500 (6 cores, 12 threads)
- RAM: 30GB total (28GB available)
- Storage: 98GB (67GB free)
- Network: enp10s0
- OS: Ubuntu 25.10 (kernel 6.17.0-6)
- Container Runtime: containerd 2.1.4

**OptiPlex (192.168.1.51) - Worker:**
- CPU: Intel i7-4790 @ 3.60GHz (4 cores, 8 threads)
- RAM: 30GB total (28GB available)
- Storage: 98GB (65GB free)
- Network: eno1
- OS: Ubuntu 25.10 (kernel 6.17.0-6)
- Container Runtime: containerd 2.1.4
- **Note:** Also running standalone Docker containers (needs cleanup)

**Cluster Sizing:** Both nodes are well-specced for homelab workloads. Current resource usage is minimal (< 10%).

---

### Files Updated
- `/home/knower/sector7-infrastructure/docs/INFRASTRUCTURE-AUDIT.md` (this file)

### SSH Access Verified
- ✅ `degenotterdev@192.168.1.50` - Key-based auth working
- ✅ `degenotterdev@192.168.1.51` - Key-based auth working

---

**Document Version:** 1.1
**Created:** 2025-11-13
**Updated:** 2025-11-15
**Status:** Major Issues Resolved - External Access Configuration Pending
