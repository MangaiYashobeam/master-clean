# Complete the deployment - Run these commands on the VPS
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Complete Admin Panel Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Good news! The repository is cloned and dependencies are installed." -ForegroundColor Green
Write-Host ""
Write-Host "Now SSH into your VPS and run these final commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "ssh biotrack@biotrack.bo.click" -ForegroundColor White
Write-Host ""
Write-Host "Then run:" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Stop the old service" -ForegroundColor Green
Write-Host "sudo systemctl stop biotrack.service" -ForegroundColor White
Write-Host ""
Write-Host "# Start the new service" -ForegroundColor Green
Write-Host "sudo systemctl start biotrack.service" -ForegroundColor White
Write-Host ""
Write-Host "# Check service status" -ForegroundColor Green
Write-Host "sudo systemctl status biotrack.service" -ForegroundColor White
Write-Host ""
Write-Host "# View logs in real-time (Ctrl+C to exit)" -ForegroundColor Green
Write-Host "sudo journalctl -u biotrack.service -f" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Quick Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "After starting the service, test it:" -ForegroundColor Yellow
Write-Host ""
Write-Host "curl http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Or visit in your browser: https://biotrack.bo.click" -ForegroundColor White
Write-Host ""
