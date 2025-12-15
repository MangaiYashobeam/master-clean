# Restart BioTrack Service
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Restart BioTrack Admin Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Connecting to VPS and restarting service..." -ForegroundColor Yellow
Write-Host ""

# Run the restart commands
ssh biotrack@biotrack.bo.click @"
echo '1. Reloading systemd daemon...'
sudo systemctl daemon-reload

echo '2. Stopping biotrack service...'
sudo systemctl stop biotrack.service

echo '3. Starting biotrack service...'
sudo systemctl start biotrack.service

echo '4. Service status:'
sudo systemctl status biotrack.service --no-pager -l

echo ''
echo '5. Recent logs:'
sudo journalctl -u biotrack.service --no-pager -n 30
"@

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Service restarted!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test the deployment at: https://biotrack.bo.click" -ForegroundColor White
Write-Host ""
