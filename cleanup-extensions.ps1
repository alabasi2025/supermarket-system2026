# Close Windsurf before running this script!
# Run as Administrator: Right-click PowerShell > Run as Administrator

$keepPatterns = @(
    "esbenp.prettier*",
    "dbaeumer.vscode-eslint*", 
    "bradlc.vscode-tailwindcss*",
    "eamodio.gitlens*",
    "mhutchie.git-graph*",
    "christian-kohler.path-intellisense*",
    "usernamehw.errorlens*",
    "formulahendry.auto-close-tag*",
    "formulahendry.auto-rename-tag*",
    "humao.rest-client*",
    "pkief.material-icon-theme*",
    "streetsidesoftware.code-spell-checker*",
    "editorconfig.editorconfig*",
    "ms-vscode.live-server*",
    "naumovs.color-highlight*"
)

$extPath = "$env:USERPROFILE\.windsurf\extensions"
$deleted = 0

Get-ChildItem $extPath -Directory | ForEach-Object {
    $keep = $false
    foreach ($p in $keepPatterns) { 
        if ($_.Name -like $p) { $keep = $true; break } 
    }
    if (-not $keep) { 
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Deleted: $($_.Name)" -ForegroundColor Red
        $deleted++
    } else {
        Write-Host "Kept: $($_.Name)" -ForegroundColor Green
    }
}

Write-Host "`n=== DONE ===" -ForegroundColor Cyan
Write-Host "Deleted: $deleted extensions"
Write-Host "Remaining: $((Get-ChildItem $extPath -Directory).Count) extensions"
