#!/usr/bin/env bash

set -e
set -o nounset
set -o errexit
set -o pipefail


echo "Installing service's environment..."
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
