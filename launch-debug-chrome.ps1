# Launch Chrome with remote debugging enabled, using a fresh throwaway profile every run.

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profileRoot = "$env:TEMP"
$profileDir = Join-Path $profileRoot "chrome-debug-$(New-Guid)"

# Clean up leftover profiles from previous runs (in case Chrome was killed instead of closed normally).
Get-ChildItem -Path $profileRoot -Directory -Filter "chrome-debug-*" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

$proc = Start-Process -FilePath $chromePath -ArgumentList @(
    "--remote-debugging-address=0.0.0.0",
    "--remote-debugging-port=9222",
    "--user-data-dir=$profileDir",
    "http://localhost"
) -PassThru

Write-Host "Chrome launched (PID $($proc.Id)), profile: $profileDir"

# Block until Chrome closes, then delete its throwaway profile.
$proc.WaitForExit()
Remove-Item -Recurse -Force $profileDir -ErrorAction SilentlyContinue
Write-Host "Chrome closed, profile removed."
