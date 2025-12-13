# Deploy biotrack-pro to VPS
Write-Host "Deploy to VPS - biotrack.bo.click" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run these commands manually:" -ForegroundColor Yellow
Write-Host ""
Write-Host "ssh biotrack@biotrack.bo.click" -ForegroundColor White
Write-Host ""
Write-Host "Then on the VPS run:" -ForegroundColor Yellow
Write-Host ""
Write-Host "cd ~/master-clean" -ForegroundColor Green
Write-Host "git fetch --all" -ForegroundColor Green
Write-Host "git reset --hard origin/master" -ForegroundColor Green
Write-Host "sudo systemctl restart biotrack.service" -ForegroundColor Green
Write-Host "sudo systemctl status biotrack.service" -ForegroundColor Green
Write-Host ""
Write-Host "Login credentials:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
