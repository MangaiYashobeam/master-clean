#!/bin/bash
# Fix BioTrack Service Configuration
# This script updates the systemd service to use the new admin panel location

echo "=========================================="
echo "Fixing BioTrack Service Configuration"
echo "=========================================="
echo ""

# Create updated service file
echo "Creating updated service file..."
sudo tee /etc/systemd/system/biotrack.service > /dev/null << 'EOF'
[Unit]
Description=BioTrack Admin Panel
After=network.target

[Service]
User=biotrack
Group=biotrack
WorkingDirectory=/home/biotrack/master-clean
Environment=PATH=/home/biotrack/master-clean/venv/bin
Environment=IS_REMOTE_SERVER=true
Environment=DEPLOYMENT_MODE=vps
Environment=MESA_GL_VERSION_OVERRIDE=3.3
Environment=MESA_GLSL_VERSION_OVERRIDE=330
Environment=LIBGL_ALWAYS_SOFTWARE=1
Environment=MEDIAPIPE_DISABLE_GPU=1
Environment=GLOG_minloglevel=2
Environment=FLASK_CONFIG=production
Environment=SECRET_KEY=AjsmdOOqgnufFJmnq0SRkp7xoK5i2mFlIFfQLHQQJd0
ExecStart=/home/biotrack/master-clean/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 wsgi:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file updated"
echo ""

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
echo "✅ Daemon reloaded"
echo ""

# Restart service
echo "Restarting biotrack service..."
sudo systemctl restart biotrack.service
echo "✅ Service restarted"
echo ""

# Check status
echo "Service status:"
sudo systemctl status biotrack.service --no-pager
echo ""

# Wait a moment
sleep 2

# Test the service
echo "=========================================="
echo "Testing the service..."
echo "=========================================="
curl -I http://localhost:5000 2>&1 | head -5
echo ""

echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Visit: https://biotrack.bo.click"
echo "Login: admin / test123"
echo ""
