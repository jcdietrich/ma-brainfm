#!/bin/bash
# Install the MA Provider Watcher add-on for Home Assistant OS
# Usage: curl -fsSL https://raw.githubusercontent.com/jcd/ma-brainfm/main/scripts/install_watcher_addon.sh | sh

set -e

echo "MA Provider Watcher Installer"
echo "=============================="

# Find add-ons directory
ADDONS_DIR=""
for dir in \
    "/mnt/data/supervisor/apps/local" \
    "/mnt/data/supervisor/addons/local" \
    "/addons" \
    "/config/addons"; do
    if [ -d "$dir" ]; then
        ADDONS_DIR="$dir"
        break
    fi
done

if [ -z "$ADDONS_DIR" ]; then
    echo "ERROR: Could not find local add-ons directory"
    echo "Pass it explicitly: $0 --addons-dir /path/to/addons"
    exit 1
fi

# Handle --addons-dir flag
while [ $# -gt 0 ]; do
    case "$1" in
        --addons-dir)
            ADDONS_DIR="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

TARGET_DIR="$ADDONS_DIR/ma_provider_watcher"

echo "Installing to: $TARGET_DIR"

# Copy addon files
mkdir -p "$TARGET_DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/../addon/"* "$TARGET_DIR/"

echo ""
echo "Add-on installed!"
echo ""
echo "Next steps:"
echo "1. In HA: Settings → Add-ons → Store → Refresh"
echo "2. Find 'MA Provider Watcher' → Install → Start"
echo "3. Enable Protection Mode: OFF (three-dot menu → Protection mode)"
