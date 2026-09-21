#!/bin/bash
# generate-kubeconfig.sh
# Run this ONCE on your teamX-primary k3s node to create a kubeconfig for GitHub Actions.
#
# Usage:
#   ./generate-kubeconfig.sh team1-primary
#
# The output is a base64-encoded kubeconfig. Paste it into your GitHub repo secret
# named KUBECONFIG (Settings -> Secrets and variables -> Actions -> New repository secret).

set -euo pipefail

NODE_HOSTNAME="${1:-$(hostname)}"
NAMESPACE="${NAMESPACE:-default}"

echo "Generating kubeconfig for node: ${NODE_HOSTNAME}, namespace: ${NAMESPACE}" >&2

# Extract the k3s CA certificate
CA_CERT=$(sudo cat /var/lib/rancher/k3s/server/tls/server-ca.crt | base64 -w 0)

# Get the ServiceAccount token from the dedicated Secret
TOKEN=$(sudo kubectl get secret github-deployer-token -n "${NAMESPACE}" -o jsonpath='{.data.token}' 2>/dev/null | base64 -d)
if [ -z "$TOKEN" ]; then
    echo "ERROR: Could not get token from secret 'github-deployer-token' in namespace '${NAMESPACE}'." >&2
    echo "Did you apply k8s/github-permissions.yaml?" >&2
    exit 1
fi

# Build the kubeconfig
KUBECONFIG=$(cat <<EOF | base64 -w 0
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: ${CA_CERT}
    server: https://${NODE_HOSTNAME}:6443
  name: k3s-cluster
contexts:
- context:
    cluster: k3s-cluster
    user: github-deployer
    namespace: ${NAMESPACE}
  name: k3s
current-context: k3s
users:
- name: github-deployer
  user:
    token: ${TOKEN}
EOF
)

echo ""
echo "===== BASE64-ENCODED KUBECONFIG ====="
echo ""
echo "${KUBECONFIG}"
echo ""
echo "===== INSTRUCTIONS ====="
echo "1. Copy the long string above (from 'YXBp...' to the end)."
echo "2. In your GitHub repo, go to Settings -> Secrets and variables -> Actions."
echo "3. Create a new repository secret named: KUBECONFIG"
echo "4. Paste the base64 string as the value."
echo ""
echo "NOTE: If https://${NODE_HOSTNAME}:6443 fails with TLS errors, k3s may not have"
echo "      that hostname in its API certificate. In that case, regenerate k3s with:"
echo "      sudo k3s server --tls-san=${NODE_HOSTNAME} ..."
