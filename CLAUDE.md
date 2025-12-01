# CLAUDE.md

This file provides guidance to Claude Code when working with the Sector7 Infrastructure repository.

## Project Overview

Sector7 is the self-hosted Kubernetes infrastructure for HelloWorldDAO, serving as the **foundation for the DAO proposal pipeline**. It provides team collaboration tools, workflow automation, and database services hosted on a local k3s cluster.

## Architecture

### Cluster Topology
- **Aurora Tower** (AMD Ryzen 5000, 32GB RAM): k3s control plane + worker
- **OptiPlex** (i7 vPro, 32GB RAM): k3s worker node
- **Mini PC** (Ryzen 7 PRO, 32GB RAM): kubectl management workstation

### Infrastructure Stack
- **Orchestration**: k3s (lightweight Kubernetes)
- **Load Balancer**: MetalLB (L2 mode)
- **Ingress**: Traefik
- **SSL**: cert-manager with Let's Encrypt
- **Storage**: Longhorn distributed storage
- **Domain**: `*.sector7.helloworlddao.com`

### Core Services
| Service | Purpose | URL |
|---------|---------|-----|
| AppFlowy | Collaborative workspace + LLM integration | `appflowy.sector7.helloworlddao.com` |
| n8n | Workflow automation (proposal pipeline) | `n8n.sector7.helloworlddao.com` |
| Nextcloud | File storage and collaboration | `nextcloud.sector7.helloworlddao.com` |
| NocoDB | Low-code database interface | `nocodb.sector7.helloworlddao.com` |
| Supabase | PostgreSQL database backend | Internal cluster access |
| Ollama | Local LLM inference | Internal cluster access |
| Grafana | Monitoring dashboards | `grafana.sector7.helloworlddao.com` |

## Directory Structure

```
.
├── apps/              # Application deployments (AppFlowy, n8n, Nextcloud, etc.)
├── cluster/           # Cluster infrastructure (MetalLB, Traefik, cert-manager, Longhorn)
├── monitoring/        # Observability stack (Grafana, Prometheus)
├── scripts/           # Automation scripts (deploy, backup)
├── secrets/           # Secret templates (git-ignored actual secrets)
└── docs/              # Documentation
```

## Common Commands

### Cluster Management
```bash
# Check cluster status
kubectl get nodes
kubectl get pods --all-namespaces

# View all services and ingresses
kubectl get svc -A
kubectl get ingress -A
```

### Deploying Applications
```bash
# Deploy all apps
./scripts/deploy-all-apps.sh

# Deploy specific app
kubectl apply -f apps/<app-name>/

# Restart a deployment
kubectl rollout restart deployment/<name> -n <namespace>
```

### Storage and Certificates
```bash
# Check persistent volumes
kubectl get pvc --all-namespaces

# Check SSL certificates
kubectl get certificates --all-namespaces
```

### Logs and Debugging
```bash
# View pod logs
kubectl logs -f -n <namespace> <pod-name>

# Describe pod for events
kubectl describe pod <pod-name> -n <namespace>
```

### Backup
```bash
./scripts/backup.sh
```

## Integration with Hello World DAO

Sector7 serves as the **off-chain proposal authoring layer**:

```
Sector7 (Local)                    ICP Canisters (Mainnet)
┌─────────────────┐               ┌─────────────────────┐
│ AppFlowy + LLM  │──drafting────▶│ governance canister │
│ n8n workflows   │──automation──▶│ (on-chain proposals)│
│ Supabase/NocoDB │──data────────▶│ treasury, oracle    │
└─────────────────┘               └─────────────────────┘
```

- **AppFlowy**: Team drafts and refines proposals collaboratively with LLM assistance
- **n8n**: Automates notifications, status updates, and triggers to on-chain governance
- **Supabase/NocoDB**: Stores proposal drafts, metadata, and team collaboration data

## Security Notes

- All secrets are in `secrets/` directory (git-ignored)
- Change default passwords before deploying
- Services are exposed via HTTPS with Let's Encrypt certificates
- Access is direct exposure to the network (port forwarding 80/443)

## Key Documentation

- `docs/CURRENT-STATE.md` - Authoritative reference for deployed infrastructure
- `docs/QUICK-REFERENCE.md` - Common commands and operations
- `docs/setup-guide.md` - Full setup guide from scratch
- `docs/NETWORK-TOPOLOGY.md` - Network diagram

## AppFlowy LLM Integration

AppFlowy Cloud integrates with Ollama for local LLM inference:
- Ollama deployment in `apps/ollama/`
- Models are loaded on-demand
- Used for proposal drafting assistance, summarization, and review
