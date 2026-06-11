#!/usr/bin/env bash
set -e
# Build app image
docker build -t hospital-dt-app -f infra/Dockerfile.app .
# For vLLM, you should build/run the ROCm-enabled container separately following vendor docs.
echo "To run the app:"
echo "docker run --gpus all -p 8501:8501 -v $(pwd):/app hospital-dt-app"
echo "Ensure your vLLM server is running at http://host.docker.internal:8000/generate or set VLLM_ENDPOINT."
