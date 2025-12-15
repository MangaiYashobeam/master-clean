# Fix BioTrack Service - Manual Commands
# =======================================
# Run these commands on the VPS to complete the deployment

# SSH into your VPS
Write-Host "SSH into your VPS:" -ForegroundColor Cyan
Write-Host "ssh biotrack@biotrack.bo.click" -ForegroundColor White
Write-Host ""
Write-Host "Then run these commands:" -ForegroundColor Yellow
Write-Host ""

Write-Host @"
# 1. Reload systemd daemon
sudo systemctl daemon-reload

# 2. Stop the service
sudo systemctl stop biotrack.service

# 3. Start the service
sudo systemctl start biotrack.service

# 4. Check the status
sudo systemctl status biotrack.service

# 5. If there are errors, check the logs
sudo journalctl -u biotrack.service -f

# 6. Test locally on the VPS
curl http://localhost:5000

# 7. Check if it's responding
curl -I http://localhost:5000
"@ -ForegroundColor Green

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "What we've done so far:" -ForegroundColor Yellow
Write-Host "  ✅ Cloned admin repository" -ForegroundColor Green
Write-Host "  ✅ Set up Python virtual environment" -ForegroundColor Green
Write-Host "  ✅ Installed all dependencies" -ForegroundColor Green
Write-Host "  ✅ Installed gunicorn" -ForegroundColor Green
Write-Host "  ✅ Created wsgi.py entry point" -ForegroundColor Green
Write-Host "  ✅ Initialized database with test data" -ForegroundColor Green
Write-Host "  ✅ Updated systemd service file" -ForegroundColor Green
Write-Host ""
Write-Host "What's left:" -ForegroundColor Yellow
Write-Host "  ⏳ Restart the service with sudo (requires password)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Login credentials after deployment:" -ForegroundColor Cyan
Write-Host "  Admin: admin / test123" -ForegroundColor White
Write-Host "  Student: carlos.mendez / test123" -ForegroundColor White
Write-Host ""
