# Secrets Management

This directory contains sensitive configuration that should **NEVER** be committed to git.

## Setup

1. Copy example files and remove `.example` extension
2. Fill in your actual passwords and keys
3. Create Kubernetes secrets from these files

## Creating Secrets

### Supabase

```bash
cp supabase.env.example supabase.env
# Edit supabase.env with your passwords
kubectl create secret generic supabase-config --from-env-file=supabase.env -n supabase
```

### NocoDB

```bash
cp nocodb.env.example nocodb.env
# Edit nocodb.env
kubectl create secret generic nocodb-config --from-env-file=nocodb.env -n nocodb
```

### AppFlowy

```bash
cp appflowy.env.example appflowy.env
# Edit appflowy.env
kubectl create secret generic appflowy-config --from-env-file=appflowy.env -n appflowy
```

## Security Notes

- All `.env` files (except `.example`) are git-ignored
- Never commit actual passwords to version control
- Use strong, randomly generated passwords
- Consider using a password manager for team sharing
- For production, consider using Sealed Secrets or External Secrets Operator
