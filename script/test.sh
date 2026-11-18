#!/bin/sh
# Run the integration tests in a clean Python container, against the Home
# Assistant release that pytest-homeassistant-custom-component supports.
# usage: sh script/test.sh [pytest arguments]   (from the repository root)
set -e
MSYS_NO_PATHCONV=1 podman run --rm -v "$(pwd -W 2>/dev/null || pwd):/work:ro" --entrypoint sh docker.io/library/python:3.14-slim -c "
  pip install -q --root-user-action=ignore --disable-pip-version-check -r /work/requirements_test.txt &&
  cp -r /work /tmp/work && cd /tmp/work && python -m pytest -q -p no:cacheprovider \"\$@\"
" -- "$@"
