#!/usr/bin/env bash

set -euo pipefail
cd "$(dirname "$0")/grid_api"

podman build -t grid-api-matplotlib --build-arg WITH_VIZ=1 -f Containerfile .
podman run --rm -p 8000:8000 grid-api-matplotlib:latest 