# MetalLB Load Balancer

MetalLB provides LoadBalancer IPs for services in your cluster.

## Configuration Required

Before applying, edit `ip-pool.yaml` and set the IP address range for your network.

**Example:**
- If your network is `192.168.68.0/24` and your machines use `.54`, `.65`, `.75`
- Set the pool to: `192.168.68.200-192.168.68.220`

This avoids conflicts with existing devices.

## Installation

```bash
kubectl apply -f install.yaml
kubectl wait --namespace metallb-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=metallb \
  --timeout=90s
kubectl apply -f ip-pool.yaml
```

## Verify

```bash
kubectl get ipaddresspool -n metallb-system
kubectl get pods -n metallb-system
```
