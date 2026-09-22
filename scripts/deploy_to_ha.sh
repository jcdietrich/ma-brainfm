#!/bin/bash
# Deploy Brain.fm Radio provider to Music Assistant on Home Assistant
# Run this after HA/MA updates to reinstall the provider

set -e

HA_HOST="${HA_HOST:-192.168.86.29}"
HA_USER="${HA_USER:-jcd}"
PROVIDER_NAME="brainfm_radio"

echo "Brain.fm Radio Provider Deployer"
echo "================================="

# 1. Find MA container
MA=$(ssh "$HA_USER@$HA_HOST" "sudo docker ps --filter 'name=music_assistant' --format '{{.Names}}' | head -1" 2>/dev/null)
if [ -z "$MA" ]; then
    echo "ERROR: MA container not found on $HA_HOST"
    exit 1
fi
echo "Found MA container: $MA"

# 2. Detect Python version
PYVER=$(ssh "$HA_USER@$HA_HOST" "sudo docker exec $MA sh -c 'ls /app/venv/lib' 2>/dev/null | grep -m1 '^python3'")
if [ -z "$PYVER" ]; then
    echo "ERROR: Could not detect Python version"
    exit 1
fi
echo "Python version: $PYVER"

# 3. Deploy provider files into container
TARGET="/app/venv/lib/$PYVER/site-packages/music_assistant/providers/$PROVIDER_NAME"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROVIDER_DIR="$SCRIPT_DIR/../$PROVIDER_NAME"

echo "Deploying $PROVIDER_NAME to $MA:$TARGET"
cd "$PROVIDER_DIR" && tar czf - . | ssh "$HA_USER@$HA_HOST" "sudo docker exec -i $MA sh -c 'rm -rf $TARGET && mkdir -p $TARGET && cd $TARGET && tar xzf -'"

# 4. Verify
echo "Verifying..."
ssh "$HA_USER@$HA_HOST" "sudo docker exec $MA python3 -c 'import music_assistant.providers.$PROVIDER_NAME; print(\"Import OK\")'"

# 5. Restart MA
echo "Restarting Music Assistant..."
ssh "$HA_USER@$HA_HOST" "sudo docker restart $MA"

echo ""
echo "Done! Brain.fm Radio provider is installed."
echo "In MA UI: Settings -> Music Providers -> Add Provider -> Brain.fm Radio"
