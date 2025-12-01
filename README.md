# Sector7 Infrastructure

Self-hosted Kubernetes infrastructure for HelloWorldDAO team collaboration and workflow automation.

## Architecture

- **Cluster**: k3s v1.33.5 on 2 nodes (Aurora Tower + OptiPlex)
- **Storage**: local-path-provisioner (default)
- **Ingress**: ingress-nginx (NodePort mode)
- **SSL**: cert-manager with Let's Encrypt
- **Domain**: sector7.helloworlddao.com
- **Network**: 192.168.2.0/24

## Services

- **Heimdall** - Application dashboard
- **n8n** - Workflow automation
- **Nextcloud** - File collaboration
- **NocoDB** - Low-code database interface
- **Supabase** - PostgreSQL database

## Quick Start

### Prerequisites

1. Two Ubuntu servers with k3s installed (see `docs/setup-guide.md`)
2. kubectl configured on your local machine
3. DNS configured for `*.sector7.helloworlddao.com`

### Deploy Infrastructure

**Note**: Core infrastructure (ingress-nginx, cert-manager, local-path-provisioner) is already deployed and running.

```bash
# 1. Verify cluster is running
kubectl get nodes
kubectl get pods --all-namespaces

# 2. Check services status
kubectl get svc -A
kubectl get ingress -A

# 3. Access services (from internal network)
# - Heimdall: http://sector7.helloworlddao.com
# - n8n: http://n8n.sector7.helloworlddao.com
# - Nextcloud: http://nextcloud.sector7.helloworlddao.com
# - NocoDB: http://nocodb.sector7.helloworlddao.com
```

## Directory Structure

```
.
├── cluster/           # Cluster-wide infrastructure
├── apps/              # Application deployments
├── monitoring/        # Observability stack
├── scripts/           # Automation scripts
├── secrets/           # Secrets (git-ignored)
└── docs/              # Documentation
```

## Access

Services are available at (HTTP only, SSL pending configuration):

- Heimdall: http://sector7.helloworlddao.com
- n8n: http://n8n.sector7.helloworlddao.com
- Nextcloud: http://nextcloud.sector7.helloworlddao.com
- NocoDB: http://nocodb.sector7.helloworlddao.com
- Supabase: Internal only (PostgreSQL database)

## Documentation

- **[Current State](docs/CURRENT-STATE.md)** - Authoritative reference for deployed infrastructure
- **[Quick Reference](docs/QUICK-REFERENCE.md)** - Common commands and operations
- **[Infrastructure Audit](docs/INFRASTRUCTURE-AUDIT.md)** - Historical audit and architecture decisions
- [Full Setup Guide](docs/setup-guide.md) - Original setup documentation
- [Network Topology](docs/NETWORK-TOPOLOGY.md) - Network diagram
- [Security Guide](docs/SECURITY-GUIDE.md) - Security best practices

## Maintenance

### Update a service

```bash
kubectl set image deployment/<name> <container>=<image>:<tag> -n <namespace>
```

### View logs

```bash
kubectl logs -f -n <namespace> <pod-name>
```

### Backup

```bash
./scripts/backup.sh
```

## Security Notes

- All secrets are stored in `secrets/` directory (git-ignored)
- Change default passwords before deploying
- Enable 2FA on all services that support it
- Regular backups are automated via Longhorn snapshots
