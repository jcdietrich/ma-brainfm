# MA Provider Watcher Add-on

This add-on automatically re-installs custom Music Assistant providers after Home Assistant restarts. Without it, provider files are lost when the HA container is recreated.

## Installation

### Automatic (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/jcd/ma-brainfm/main/scripts/install_watcher_addon.sh | sh
```

### Manual

1. Copy the `addon/` folder to your HA add-ons directory:
   - HAOS 18+: `/mnt/data/supervisor/apps/local/ma_provider_watcher`
   - Older HAOS: `/addons/local/ma_provider_watcher`
   - Supervised: `/addons/ma_provider_watcher`

2. In HA: **Settings → Add-ons → Store** → click **Refresh**

3. Find **"MA Provider Watcher"** → **Install** → **Start**

4. Enable **Protection Mode: OFF** (required for Docker access)

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `auto_update` | `false` | Periodically check for provider updates |
| `update_interval` | `3600` | Seconds between update checks |

## How It Works

1. On start, copies provider files from `/config/custom_components/mass/providers/` into the MA container
2. Monitors for container recreation (HA restarts)
3. Re-copies providers when detected
4. Optionally checks for updates if auto_update is enabled
