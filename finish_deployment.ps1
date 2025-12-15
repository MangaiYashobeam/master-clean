Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Complete BioTrack Admin Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will open an SSH session to your VPS." -ForegroundColor Yellow
Write-Host "You'll need to enter sudo password for the restart commands." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Enter to continue or Ctrl+C to cancel..." -ForegroundColor White
$null = Read-Host

Write-Host ""
Write-Host "Connecting to biotrack.bo.click..." -ForegroundColor Green
Write-Host ""

# Open interactive SSH session with commands ready to paste
ssh biotrack@biotrack.bo.click
