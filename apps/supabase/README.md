# Supabase

PostgreSQL database with built-in auth, storage, and realtime features.

## Configuration

Before deploying, create a secret with your credentials:

```bash
# Create from template
cp ../../secrets/supabase.env.example ../../secrets/supabase.env

# Edit and add your passwords
nano ../../secrets/supabase.env

# Create Kubernetes secret
kubectl create secret generic supabase-config \
  --from-env-file=../../secrets/supabase.env \
  -n supabase
```

## Deploy

```bash
kubectl apply -f pvc.yaml
kubectl apply -f statefulset.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

## Access

- URL: https://supabase.sector7.helloworlddao.com
- Database: supabase-db.supabase.svc.cluster.local:5432

## Notes

Other services (Nextcloud, NocoDB, AppFlowy) will use this PostgreSQL instance.
