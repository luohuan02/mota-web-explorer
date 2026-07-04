# Launch the h5mota game in Chrome on CDP port 9222 using the project's
# browser-profile, then attach agent-browser. This is the canonical launch
# procedure -- see skills/mota-live-browser/SKILL.md "Launch & Connect".
#
# Usage (from project root, any shell):
#   powershell -ExecutionPolicy Bypass -File scripts/launch_h5mota_chrome.ps1
# Then read/load state with:
#   node scripts/live_read_state.js
#   node scripts/live_load_save.js --slot 1
#
# Why a custom launcher (not `agent-browser --cdp 9222 --profile ... open`):
# agent-browser ignores --profile / --args --user-data-dir and launches Chrome
# with a TEMP profile (agent-browser-chrome-<uuid>), so the h5mota saves stored
# in browser-profile's localForage are missing (getSave returns null). Launching
# chrome.exe directly with --user-data-dir is the only reliable way to use the
# browser-profile. `agent-browser connect 9222` then attaches to that chrome.

$ErrorActionPreference = 'SilentlyContinue'
$chrome  = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$profile = 'D:/claude/mota-web-explorer/browser-profile'
$url     = 'https://h5mota.com/games/51/'

# 1. If 9222 already listening, a usable chrome is already up -- just (re)connect.
$listening = Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
  # 2. Kill leftover agent-browser / browser-profile chrome zombies. These hold
  #    the profile lock, so a fresh launch would attach to the old instance (which
  #    has no debug port) instead of starting a new one on 9222. User's normal
  #    Chrome (different user-data-dir, no --remote-debugging-port) is untouched.
  Get-CimInstance Win32_Process -Filter "name='chrome.exe'" |
    Where-Object { $_.CommandLine -match 'browser-profile|agent-browser-chrome|remote-debugging-port' } |
    ForEach-Object { Write-Host "kill zombie PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force }
  Start-Sleep -Seconds 2

  # 3. Launch chrome directly on 9222 with the browser-profile.
  Start-Process $chrome -ArgumentList "--remote-debugging-port=9222","--user-data-dir=$profile",$url

  # 4. Wait for the CDP port to come up.
  for ($i = 0; $i -lt 30; $i++) {
    if (Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue) { break }
    Start-Sleep -Milliseconds 500
  }
}

if (Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue) {
  Write-Host "chrome on 9222 ready"
} else {
  Write-Host "ERROR: 9222 not listening after launch"; exit 1
}

# 5. Attach agent-browser to the external chrome.
& agent-browser connect 9222
