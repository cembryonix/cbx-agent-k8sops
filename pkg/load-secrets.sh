#!/usr/bin/env bash
#
# Load secrets into Kubernetes from an env file.
#
# Usage:
#   ./pkg/load-secrets.sh -f secrets.env [-n namespace]
#
# The env file should contain KEY=VALUE pairs (one per line).
# Lines starting with # or 'export ' prefix are handled automatically.
#
# Example secrets.env:
#   ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
#   REDIS_URL=redis://default:pass@valkey.valkey.svc.cluster.local:6379
#
# This creates two Kubernetes secrets:
#   cbx-agent-k8sops-api-keys  (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
#   cbx-agent-redis-url        (REDIS_URL)

set -euo pipefail

NAMESPACE="cbx-agents"
ENV_FILE=""

usage() {
    echo "Usage: $0 -f <secrets-file> [-n <namespace>]"
    echo ""
    echo "Options:"
    echo "  -f  Path to env file with KEY=VALUE pairs"
    echo "  -n  Kubernetes namespace (default: cbx-agents)"
    exit 1
}

while getopts "f:n:h" opt; do
    case $opt in
        f) ENV_FILE="$OPTARG" ;;
        n) NAMESPACE="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

if [ -z "$ENV_FILE" ]; then
    echo "Error: -f <secrets-file> is required"
    usage
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: file not found: $ENV_FILE"
    exit 1
fi

# Parse env file into separate lists for API keys and Redis
API_ARGS=""
REDIS_URL=""
KEY_NAMES=""
COUNT=0

while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    case "$line" in
        ""|\#*|" "*\#*) continue ;;
    esac

    # Strip 'export ' prefix
    line="${line#export }"

    # Strip leading/trailing whitespace
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

    # Skip if not KEY=VALUE
    case "$line" in
        *=*) ;;
        *) continue ;;
    esac

    key="${line%%=*}"
    value="${line#*=}"

    # Strip surrounding quotes from value
    value="${value#\"}"
    value="${value%\"}"
    value="${value#\'}"
    value="${value%\'}"

    COUNT=$((COUNT + 1))

    if [ "$key" = "REDIS_URL" ]; then
        REDIS_URL="$value"
    else
        API_ARGS="${API_ARGS} --from-literal=${key}=${value}"
        KEY_NAMES="${KEY_NAMES} ${key}"
    fi
done < "$ENV_FILE"

if [ "$COUNT" -eq 0 ]; then
    echo "Error: no secrets found in $ENV_FILE"
    exit 1
fi

echo "Namespace: $NAMESPACE"
echo "Found ${COUNT} key(s)"
echo ""

# Create/update API keys secret
if [ -n "$API_ARGS" ]; then
    echo "Creating secret: cbx-agent-k8sops-api-keys"
    echo "  Keys:${KEY_NAMES}"
    kubectl create secret generic cbx-agent-k8sops-api-keys \
        -n "$NAMESPACE" \
        ${API_ARGS} \
        --dry-run=client -o yaml | kubectl apply -f -
fi

# Create/update Redis secret
if [ -n "$REDIS_URL" ]; then
    echo "Creating secret: cbx-agent-redis-url"
    echo "  Keys: REDIS_URL"
    kubectl create secret generic cbx-agent-redis-url \
        -n "$NAMESPACE" \
        --from-literal=REDIS_URL="${REDIS_URL}" \
        --dry-run=client -o yaml | kubectl apply -f -
fi

echo ""
echo "Done. Verify with:"
echo "  kubectl get secrets -n $NAMESPACE"