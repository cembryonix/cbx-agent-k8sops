#!/bin/bash
set -e

# K8SOps Agent Entrypoint
# Runs Reflex in production mode (frontend + backend)

FRONTEND_PORT="${K8SOPS_FRONTEND_PORT:-3000}"
BACKEND_PORT="${K8SOPS_BACKEND_PORT:-8000}"

# Override Reflex backend URL for reverse proxy / ingress deployments
if [ -n "$API_URL" ]; then
    sed -i "s|app_name=\"k8sops\",|app_name=\"k8sops\",\n    api_url=\"${API_URL}\",|" /app/rxconfig.py
fi

echo "Starting K8SOps Agent..."
echo "  Frontend: http://0.0.0.0:${FRONTEND_PORT}"
echo "  Backend:  http://0.0.0.0:${BACKEND_PORT}"
[ -n "$API_URL" ] && echo "  API URL:  ${API_URL}"

exec reflex run --env prod \
    --frontend-port "${FRONTEND_PORT}" \
    --backend-port "${BACKEND_PORT}" \
    --backend-host "0.0.0.0"