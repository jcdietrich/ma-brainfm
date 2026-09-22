#!/bin/bash
# Music Assistant Brain.fm Radio Provider Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/jcd/ma-brainfm/main/scripts/install_provider.sh | sh
# Or: bash install_provider.sh

set -e

PROVIDER_NAME="brainfm_radio"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROVIDER_DIR="$SCRIPT_DIR/../$PROVIDER_NAME"

# If run from a different location, look for provider dir
if [ ! -d "$PROVIDER_DIR" ]; then
    PROVIDER_DIR="./$PROVIDER_NAME"
fi

if [ ! -d "$PROVIDER_DIR" ]; then
    echo "ERROR: Could not find $PROVIDER_NAME directory"
    echo "Run this script from the project root, or ensure $PROVIDER_NAME/ is in the current directory"
    exit 1
fi

echo "Music Assistant Brain.fm Radio Provider Installer"
echo "=================================================="

# Find MA container
MA=""
for name in "app_d5369777_music_assistant" "addon_d5369777_music_assistant"; do
    if docker inspect "$name" >/dev/null 2>&1; then
        MA="$name"
        break
    fi
done

if [ -z "$MA" ]; then
    # Try to find by image
    MA=$(docker ps --filter "ancestor=ghcr.io/music-assistant/server" --format "{{.Names}}" | head -1)
    if [ -z "$MA" ]; then
        MA=$(docker ps --filter "name=music_assistant" --format "{{.Names}}" | head -1)
    fi
fi

if [ -z "$MA" ]; then
    echo "ERROR: Could not find Music Assistant container"
    echo "Make sure Music Assistant is installed and running"
    exit 1
fi

echo "Found MA container: $MA"

# Detect Python version
PYVER=$(docker exec "$MA" sh -c 'ls /app/venv/lib' 2>/dev/null | grep -m1 '^python3')
if [ -z "$PYVER" ]; then
    echo "ERROR: Could not detect Python version in container"
    exit 1
fi

echo "Python version: $PYVER"

# Copy provider into container
TARGET="/app/venv/lib/$PYVER/site-packages/music_assistant/providers/$PROVIDER_NAME"
echo "Copying provider to $MA:$TARGET"

docker exec "$MA" mkdir -p "/app/venv/lib/$PYVER/site-packages/music_assistant/providers/$PROVIDER_NAME"
docker cp "$PROVIDER_DIR/." "$MA:$TARGET/"

# Verify
echo "Verifying installation..."
docker exec "$MA" python -c "import music_assistant.providers.$PROVIDER_NAME; print('Import OK')" 2>/dev/null || echo "Note: Import check may fail until MA is restarted"

# Restart MA
echo "Restarting Music Assistant..."
docker restart "$MA"

echo ""
echo "Done! Brain.fm Radio provider installed."
echo "In MA UI: Settings → Music Providers → Add Provider → Brain.fm Radio"
echo ""
echo "NOTE: This installation will be lost if HA is restarted."
echo "Install the watcher add-on to survive restarts:"
echo "  See WATCHER_ADDON.md in the project root"
