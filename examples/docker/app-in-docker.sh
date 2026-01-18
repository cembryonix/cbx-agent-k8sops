#!/usr/bin/env bash
set -e

# K8SOps Agent - Docker Control Script
# Usage: ./app-in-docker.sh start|stop

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
env_file="${script_dir}/.env"

# Source .env if exists (to get port settings)
if [ -f "$env_file" ]; then
    set -a
    source "$env_file"
    set +a
fi

# Container settings
CONTAINER_NAME="${CONTAINER_NAME:-k8sops-agent}"
IMAGE_NAME="${IMAGE_NAME:-cbx-agent-k8sops:dev}"
FRONTEND_PORT="${K8SOPS_FRONTEND_PORT:-3000}"
BACKEND_PORT="${K8SOPS_BACKEND_PORT:-8000}"

start_container() {
    # Check for .env file
    if [ ! -f "$env_file" ]; then
        echo "Error: .env file not found at $env_file"
        echo "Copy .env.example to .env and configure your settings"
        exit 1
    fi

    # Stop existing container if running
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo "Stopping existing container..."
        docker stop "$CONTAINER_NAME" >/dev/null
    fi

    # Remove existing container if exists
    if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
        echo "Removing existing container..."
        docker rm "$CONTAINER_NAME" >/dev/null
    fi

    echo "Starting K8SOps Agent..."
    echo "  Image: $IMAGE_NAME"
    echo "  Container: $CONTAINER_NAME"
    echo "  Frontend port: $FRONTEND_PORT"
    echo "  Backend port: $BACKEND_PORT"

    docker run -d \
        --name "$CONTAINER_NAME" \
        --env-file "$env_file" \
        -p "${FRONTEND_PORT}:3000" \
        -p "${BACKEND_PORT}:8000" \
        --restart unless-stopped \
        "$IMAGE_NAME"

    echo ""
    echo "Container started successfully!"
    echo "App UI: http://localhost:${FRONTEND_PORT}"
    echo ""
    echo "View logs:  docker logs -f $CONTAINER_NAME"
    echo "Stop:       $0 stop"
}

stop_container() {
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo "Stopping $CONTAINER_NAME..."
        docker stop "$CONTAINER_NAME" >/dev/null
        echo "Container stopped."
    else
        echo "Container $CONTAINER_NAME is not running."
    fi

    if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
        echo "Removing $CONTAINER_NAME..."
        docker rm "$CONTAINER_NAME" >/dev/null
        echo "Container removed."
    fi
}

case "${1:-}" in
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    *)
        echo "Usage: $0 start|stop"
        exit 1
        ;;
esac