$svc = Get-WmiObject win32_service -Filter "Name='cloudflared'"
Write-Host "Path: $($svc.PathName)"
Write-Host "State: $($svc.State)"
Write-Host "StartMode: $($svc.StartMode)"

# Try start and capture error
try {
    Start-Service cloudflared -ErrorAction Stop
    Write-Host "Started OK"
} catch {
    Write-Host "Error: $_"
}
