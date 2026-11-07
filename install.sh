#!/bin/zsh
# Reel Inbox installer. Safe to re-run. Free tools only.
#   1. checks brew tools (yt-dlp, ffmpeg, whisper-cpp)
#   2. downloads the local Whisper model once (~550 MB)
#   3. compiles the Vision OCR helper
#   4. installs + starts the launchd agent that watches the iCloud inbox
#   5. registers the MCP server for every Claude Code session (user scope)
set -euo pipefail
REPO="${0:A:h}"
SUPPORT="$HOME/Library/Application Support/ReelInbox"
INBOX="$HOME/Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/ReelInbox"
MODEL="$SUPPORT/models/ggml-large-v3-turbo-q5_0.bin"
PLIST="$HOME/Library/LaunchAgents/com.silas.reelinbox.plist"
PY=/opt/homebrew/bin/python3

for t in yt-dlp ffmpeg whisper-cli; do
  command -v $t >/dev/null || { echo "missing $t: brew install ${t/whisper-cli/whisper-cpp}"; exit 1; }
done

mkdir -p "$SUPPORT/models" "$INBOX" "$HOME/ReelInbox"
[[ -s "$MODEL" ]] || curl -L --fail -o "$MODEL" \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin

mkdir -p "$REPO/bin"
swiftc -O "$REPO/vision/reelvision.swift" -o "$REPO/bin/reelvision"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.silas.reelinbox</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$REPO/worker/reel_worker.py</string></array>
  <key>WatchPaths</key><array><string>$INBOX</string></array>
  <key>StartInterval</key><integer>120</integer>
  <key>RunAtLoad</key><true/>
  <key>ThrottleInterval</key><integer>5</integer>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
  <key>StandardOutPath</key><string>$SUPPORT/launchd.out.log</string>
  <key>StandardErrorPath</key><string>$SUPPORT/launchd.err.log</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)/com.silas.reelinbox" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "launchd agent running: com.silas.reelinbox"

if command -v claude >/dev/null; then
  claude mcp remove --scope user reel-inbox >/dev/null 2>&1 || true
  claude mcp add --scope user reel-inbox -- "$PY" "$REPO/mcp/reel_mcp.py"
fi
echo "done"
