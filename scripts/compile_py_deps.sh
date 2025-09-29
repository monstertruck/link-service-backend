#!/usr/bin/env bash

set -e
set -o nounset
set -o errexit
set -o pipefail

REQUIREMENTS_IN="requirements.in"
REQUIREMENTS_TEST_IN="requirements-test.in"

echo "- Compiling python package dependencies..."
pip-compile --quiet --strip-extras ${REQUIREMENTS_IN}
pip-compile --quiet --strip-extras ${REQUIREMENTS_TEST_IN}
