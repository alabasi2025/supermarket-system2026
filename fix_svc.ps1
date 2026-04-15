$sysPath = 'C:\Windows\System32\config\systemprofile\.cloudflared'
New-Item -Path $sysPath -ItemType Directory -Force
Copy-Item 'C:\Users\qbas\.cloudflared\*' "$sysPath\" -Force
Write-Host "Files copied"
Get-ChildItem $sysPath
Start-Service cloudflared
Start-Sleep 3
Get-Service cloudflared
