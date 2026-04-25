#!/usr/bin/env bash
# Stop MISS CLOVER production processes and close labelled Terminal windows.

cd "$(dirname "$0")"

echo "Stopping MISS CLOVER..."

# Tunnel
pkill -9 -f "cloudflared.*missclover" 2>/dev/null && echo "  Cloudflare Tunnel stopped" || echo "  Tunnel was not running"

# Gunicorn + anything on port 5002
pkill -9 -f "gunicorn.*missclover" 2>/dev/null
lsof -ti:5002 | xargs kill -9 2>/dev/null
sleep 1
lsof -ti:5002 | xargs kill -9 2>/dev/null && echo "  Gunicorn stopped (forced)" || echo "  Gunicorn stopped"

# Close labelled Terminal windows
osascript -e '
tell application "Terminal"
    repeat with w in windows
        try
            if custom title of w is "MC-Gunicorn" or custom title of w is "MC-Tunnel" then
                close w saving no
            end if
        end try
    end repeat
end tell
' 2>/dev/null

rm -f logs/gunicorn.pid logs/cloudflared.pid 2>/dev/null
echo "Done."
