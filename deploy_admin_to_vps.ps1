# Deploy master-clean-admin to VPS - biotrack.bo.click
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy Admin Panel to biotrack.bo.click" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "WARNING: This will DELETE all existing content and deploy the admin panel!" -ForegroundColor Red
Write-Host ""
Write-Host "Follow these steps:" -ForegroundColor Yellow
Write-Host ""

Write-Host "1. SSH into the VPS:" -ForegroundColor Cyan
Write-Host "   ssh biotrack@biotrack.bo.click" -ForegroundColor White
Write-Host ""

Write-Host "2. Stop the current service:" -ForegroundColor Cyan
Write-Host "   sudo systemctl stop biotrack.service" -ForegroundColor Green
Write-Host ""

Write-Host "3. Backup current directory (optional but recommended):" -ForegroundColor Cyan
Write-Host "   cd ~" -ForegroundColor Green
Write-Host "   sudo tar -czf master-clean-backup-`$(date +%Y%m%d-%H%M%S).tar.gz master-clean/" -ForegroundColor Green
Write-Host ""

Write-Host "4. Delete existing content:" -ForegroundColor Cyan
Write-Host "   cd ~/master-clean" -ForegroundColor Green
Write-Host "   rm -rf *" -ForegroundColor Green
Write-Host "   rm -rf .git .gitignore" -ForegroundColor Green
Write-Host ""

Write-Host "5. Clone the admin repository:" -ForegroundColor Cyan
Write-Host "   cd ~" -ForegroundColor Green
Write-Host "   rm -rf master-clean" -ForegroundColor Green
Write-Host "   git clone https://github.com/MangaiYashobeam/master-clean-admin.git master-clean" -ForegroundColor Green
Write-Host "   cd master-clean" -ForegroundColor Green
Write-Host ""

Write-Host "6. Set up Python virtual environment:" -ForegroundColor Cyan
Write-Host "   python3 -m venv venv" -ForegroundColor Green
Write-Host "   source venv/bin/activate" -ForegroundColor Green
Write-Host ""

Write-Host "7. Install dependencies:" -ForegroundColor Cyan
Write-Host "   pip install --upgrade pip" -ForegroundColor Green
Write-Host "   pip install -r requirements.txt" -ForegroundColor Green
Write-Host ""

Write-Host "8. Set up the database (if needed):" -ForegroundColor Cyan
Write-Host "   # Check if the repo has database setup scripts" -ForegroundColor Green
Write-Host "   # Run them if they exist, e.g.:" -ForegroundColor Green
Write-Host "   python scripts/init_db.py" -ForegroundColor Green
Write-Host ""

Write-Host "9. Update systemd service file (if needed):" -ForegroundColor Cyan
Write-Host "   sudo nano /etc/systemd/system/biotrack.service" -ForegroundColor Green
Write-Host "   # Verify paths point to /home/biotrack/master-clean" -ForegroundColor Green
Write-Host "   sudo systemctl daemon-reload" -ForegroundColor Green
Write-Host ""

Write-Host "10. Start the service:" -ForegroundColor Cyan
Write-Host "    sudo systemctl start biotrack.service" -ForegroundColor Green
Write-Host "    sudo systemctl status biotrack.service" -ForegroundColor Green
Write-Host ""

Write-Host "11. Check logs for any errors:" -ForegroundColor Cyan
Write-Host "    sudo journalctl -u biotrack.service -f --lines=50" -ForegroundColor Green
Write-Host ""

Write-Host "12. Test the deployment:" -ForegroundColor Cyan
Write-Host "    curl http://localhost:5000" -ForegroundColor Green
Write-Host "    # Or visit https://biotrack.bo.click in your browser" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Quick deployment command (all at once):" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host @"
ssh biotrack@biotrack.bo.click << 'ENDSSH'
sudo systemctl stop biotrack.service
cd ~
sudo tar -czf master-clean-backup-`$(date +%Y%m%d-%H%M%S).tar.gz master-clean/ 2>/dev/null || true
rm -rf master-clean
git clone https://github.com/MangaiYashobeam/master-clean-admin.git master-clean
cd master-clean
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# Run any initialization scripts if they exist
[ -f scripts/init_db.py ] && python scripts/init_db.py || true
sudo systemctl start biotrack.service
sudo systemctl status biotrack.service
ENDSSH
"@ -ForegroundColor Green
Write-Host ""
Write-Host "Note: Review the admin repository structure first to ensure" -ForegroundColor Yellow
Write-Host "it has all necessary files (requirements.txt, run.py, etc.)" -ForegroundColor Yellow
