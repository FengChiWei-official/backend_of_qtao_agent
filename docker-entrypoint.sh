
#!/bin/bash
set -euo pipefail

export PYTHONPATH=/app
echo "entrypoint.sh executed"

# Do not print full config (may contain secrets)
if [ -f /app/config/config.yaml ]; then
	echo "Found config at /app/config/config.yaml"
fi

# Ensure cache directory exists and is writable. If we cannot create /app/cache
# (image may have been created without ownership set), fall back to /tmp.
CACHE_DIR="/app/cache"
if ! mkdir -p "$CACHE_DIR" 2>/dev/null; then
	echo "Warning: cannot create $CACHE_DIR, falling back to /tmp/app-cache"
	CACHE_DIR="/tmp/app-cache"
	mkdir -p "$CACHE_DIR"
fi
export CACHE_DIR

# Apply DB migrations (only upgrade). Generating migrations should be done
# in development/CI and committed to VCS, not at container startup.
echo "Running alembic upgrade head"
conda run -n app alembic -c /app/config/alembic.ini upgrade head

echo "Starting application"
exec conda run --no-capture-output -n app python ./main.py