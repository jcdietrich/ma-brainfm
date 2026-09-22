#!/bin/bash
# MA Provider Watcher - re-copies providers after HA restarts

CONFIG="/config/custom_components/mass/providers"
PROVIDERS=("brainfm_radio")

copy_providers() {
    # Find MA container
    MA=""
    for name in "app_d5369777_music_assistant" "addon_d5369777_music_assistant"; do
        if docker inspect "$name" >/dev/null 2>&1; then
            MA="$name"
            break
        fi
    done

    if [ -z "$MA" ]; then
        echo "MA container not found, retrying..."
        return 1
    fi

    PYVER=$(docker exec "$MA" sh -c 'ls /app/venv/lib' 2>/dev/null | grep -m1 '^python3')
    if [ -z "$PYVER" ]; then
        echo "Could not detect Python version"
        return 1
    fi

    for PROVIDER in "${PROVIDERS[@]}"; do
        SOURCE="$CONFIG/$PROVIDER"
        TARGET="/app/venv/lib/$PYVER/site-packages/music_assistant/providers/$PROVIDER"

        if [ -d "$SOURCE" ]; then
            docker exec "$MA" mkdir -p "$TARGET"
            docker cp "$SOURCE/." "$MA:$TARGET/"
            echo "Copied $PROVIDER"
        else
            echo "Source not found: $SOURCE"
        fi
    done

    docker restart "$MA"
    echo "MA restarted with providers"
    return 0
}

# Initial copy
echo "MA Provider Watcher starting..."
copy_providers

# Watch for HA restarts (container recreation)
while true; do
    sleep 60
    # Check if MA container is running
    MA=""
    for name in "app_d5369777_music_assistant" "addon_d5369777_music_assistant"; do
        if docker inspect "$name" >/dev/null 2>&1; then
            MA="$name"
            break
        fi
    done

    if [ -z "$MA" ]; then
        echo "MA container gone, waiting for recreation..."
        sleep 30
        copy_providers
    fi
done
