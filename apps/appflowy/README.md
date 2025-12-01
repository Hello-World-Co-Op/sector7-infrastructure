# AppFlowy-Cloud Deployment

**Deployment Date**: 2025-11-25
**Status**: ✅ OPERATIONAL
**Version**: Latest (appflowyinc images)
**Namespace**: appflowy

## Overview

AppFlowy-Cloud is a fully self-hosted collaboration platform deployed on the Sector7 Kubernetes cluster. All 8 microservices are running successfully on the Aurora node.

## Architecture

### Services Deployed

| Service | Status | Purpose | Port | Resource Usage |
|---------|--------|---------|------|----------------|
| PostgreSQL | ✅ Running | Dedicated database (pgvector) | 5432 | 1-2GB RAM, 20GB storage |
| Redis | ✅ Running | Cache and message queue | 6379 | 256-512MB RAM |
| MinIO | ✅ Running | S3-compatible object storage | 9000/9001 | 512MB-1GB RAM, 50GB storage |
| GoTrue | ✅ Running | Authentication service | 9999 | 256-512MB RAM |
| AppFlowy Cloud | ✅ Running | Main backend API | 8000 | 1-2GB RAM |
| AppFlowy Worker | ✅ Running | Background job processor | - | 512MB-1GB RAM |
| AppFlowy Web | ✅ Running | Web frontend | 3000 | 512MB-1GB RAM |
| Admin Frontend | ✅ Running | Admin dashboard | 3000 | 256-512MB RAM |

### Total Resources

- **RAM**: ~4-8GB total
- **Storage**: 70GB (20GB PostgreSQL + 50GB MinIO)
- **CPU**: ~3-5 cores under load

## Access URLs

**Base URL**: http://appflowy.sector7.helloworlddao.com

### Endpoints

- **Web App**: http://appflowy.sector7.helloworlddao.com/
- **API**: http://appflowy.sector7.helloworlddao.com/api
- **WebSocket**: ws://appflowy.sector7.helloworlddao.com/ws/v2
- **Authentication**: http://appflowy.sector7.helloworlddao.com/gotrue
- **Admin Console**: http://appflowy.sector7.helloworlddao.com/console
- **MinIO Console**: http://appflowy.sector7.helloworlddao.com/minio

## Configuration

### Credentials

**Admin User**:
- Email: graydon@helloworlddao.com
- Password: G@G!1insight!

**Database**:
- User: degenotterdev
- Password: G@G!1insight!
- Database: appflowy
- Host: appflowy-postgres:5432

**S3/MinIO**:
- Access Key: degenotterdev
- Secret Key: G@G!1insight!
- Bucket: appflowy
- Endpoint: http://appflowy-minio:9000

### License Tier

- **Plan**: Free Self-Hosted
- **Max Users**: 1
- **Max Guest Editors**: 3
- **Workspaces**: Unlimited

## Deployment Files

```
apps/appflowy/
├── 00-namespace.yaml         # Namespace definition
├── 01-secrets.yaml           # Credentials and configuration
├── 02-postgres.yaml          # PostgreSQL database (StatefulSet)
├── 03-redis.yaml             # Redis cache (Deployment)
├── 04-minio.yaml             # MinIO storage (Deployment)
├── 05-gotrue.yaml            # Authentication service (Deployment)
├── 06-appflowy-cloud.yaml    # Main backend (Deployment)
├── 07-appflowy-worker.yaml   # Background worker (Deployment)
├── 08-appflowy-web.yaml      # Web frontend (Deployment)
├── 09-admin-frontend.yaml    # Admin panel (Deployment)
└── 10-ingress.yaml           # HTTP routing (Ingress)
```

## Features Enabled

- ✅ User authentication (GoTrue)
- ✅ Real-time collaboration
- ✅ File storage (MinIO)
- ✅ Database storage (PostgreSQL + pgvector)
- ✅ Background job processing
- ✅ Web interface
- ✅ Admin dashboard
- ⚠️ Email notifications (SMTP not configured)
- ⚠️ AI features (not configured)

## Known Limitations

1. **SMTP**: Email notifications disabled (no SMTP server configured)
2. **AI**: AI features disabled (no OpenAI API key configured)
3. **SSL**: Running on HTTP only (SSL pending external access configuration)
4. **Single User**: Free tier limited to 1 user + 3 guests

## Troubleshooting

### Check Service Health

```bash
# Check all pods
kubectl get pods -n appflowy

# Check specific service logs
kubectl logs -n appflowy -l app=appflowy-cloud
kubectl logs -n appflowy -l app=appflowy-gotrue

# Check database connection
kubectl exec -it -n appflowy appflowy-postgres-0 -- psql -U degenotterdev -d appflowy

# Check MinIO buckets
kubectl port-forward -n appflowy svc/appflowy-minio 9001:9001
# Open http://localhost:9001 (login: degenotterdev / G@G!1insight!)
```

### Common Issues

**Issue**: Pods crash with "Invalid TLS kind"
- **Solution**: Set `APPFLOWY_MAILER_SMTP_TLS_KIND: "none"` when SMTP is not configured

**Issue**: "cannot parse integer from empty string"
- **Solution**: Ensure all SMTP port fields have numeric values (e.g., "587") or valid defaults

**Issue**: GoTrue database migrations fail
- **Solution**: Ensure PostgreSQL is running and search_path=auth is set in DATABASE_URL

## Maintenance

### Backup

```bash
# Backup PostgreSQL database
kubectl exec -n appflowy appflowy-postgres-0 -- pg_dumpall -U degenotterdev > appflowy-backup-$(date +%Y%m%d).sql

# Backup MinIO data (optional - uses PVC)
kubectl get pvc -n appflowy appflowy-minio-data
```

### Update

```bash
# Update to latest images
kubectl set image deployment/appflowy-cloud appflowy-cloud=appflowyinc/appflowy_cloud:latest -n appflowy
kubectl set image deployment/appflowy-web appflowy-web=appflowyinc/appflowy_web:latest -n appflowy
kubectl set image deployment/appflowy-worker appflowy-worker=appflowyinc/appflowy_worker:latest -n appflowy
kubectl set image deployment/appflowy-admin-frontend admin-frontend=appflowyinc/admin_frontend:latest -n appflowy
kubectl set image deployment/appflowy-gotrue gotrue=appflowyinc/gotrue:latest -n appflowy
```

### Scale

```bash
# Scale web frontend (if needed)
kubectl scale deployment/appflowy-web --replicas=2 -n appflowy

# Scale worker (for heavy background jobs)
kubectl scale deployment/appflowy-worker --replicas=2 -n appflowy
```

## Desktop Client Setup

To connect the AppFlowy desktop client from the Mini PC:

1. Download AppFlowy desktop client
2. In settings, set server URL to: `http://appflowy.sector7.helloworlddao.com`
3. Login with: graydon@helloworlddao.com

## References

- [Official AppFlowy-Cloud Repository](https://github.com/AppFlowy-IO/AppFlowy-Cloud)
- [AppFlowy Documentation](https://appflowy.com/docs)
- [Self-Hosting Guide](https://appflowy.com/docs/Step-by-step-Self-Hosting-Guide---From-Zero-to-Production)

---

**Deployed by**: Claude Code
**Date**: 2025-11-25
**Cluster**: aurora / sector7-infrastructure
