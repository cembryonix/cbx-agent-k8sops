#!/bin/bash
set -e

# K8SOps Agent Entrypoint
# Runs Reflex in production mode (frontend + backend)

FRONTEND_PORT="${K8SOPS_FRONTEND_PORT:-3000}"
BACKEND_PORT="${K8SOPS_BACKEND_PORT:-8000}"

echo "Starting K8SOps Agent..."
echo "  Frontend: http://0.0.0.0:${FRONTEND_PORT}"
echo "  Backend:  http://0.0.0.0:${BACKEND_PORT}"

exec reflex run --env prod \
    --frontend-port "${FRONTEND_PORT}" \
    --backend-port "${BACKEND_PORT}" \
    --backend-host "0.0.0.0"