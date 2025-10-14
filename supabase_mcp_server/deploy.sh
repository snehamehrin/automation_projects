#!/bin/bash
# Deploy Supabase MCP Server to Hostinger VPS

set -e

# Configuration
VPS_USER="your_username"
VPS_HOST="your_vps_ip_or_domain"
VPS_PATH="/home/$VPS_USER/supabase_mcp_server"
REMOTE_PORT="8000"

echo "🚀 Deploying Supabase MCP Server to VPS..."

# Create directory on VPS
echo "📁 Creating directory on VPS..."
ssh $VPS_USER@$VPS_HOST "mkdir -p $VPS_PATH"

# Copy files
echo "📤 Uploading files..."
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.pytest_cache' \
    --exclude '.git' --exclude 'tests' \
    ./ $VPS_USER@$VPS_HOST:$VPS_PATH/

# Setup on VPS
echo "🔧 Setting up on VPS..."
ssh $VPS_USER@$VPS_HOST << 'ENDSSH'
cd ~/supabase_mcp_server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-server.txt

# Create systemd service
sudo tee /etc/systemd/system/supabase-mcp.service > /dev/null << 'EOF'
[Unit]
Description=Supabase MCP Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/supabase_mcp_server
Environment="PATH=$HOME/supabase_mcp_server/venv/bin"
ExecStart=$HOME/supabase_mcp_server/venv/bin/python server_remote.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable supabase-mcp
sudo systemctl restart supabase-mcp

echo "✅ Service started!"
echo "📊 Status:"
sudo systemctl status supabase-mcp --no-pager

ENDSSH

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. SSH to your VPS: ssh $VPS_USER@$VPS_HOST"
echo "2. Edit .env file: nano ~/supabase_mcp_server/.env"
echo "3. Add your SUPABASE_URL and SUPABASE_KEY"
echo "4. Restart service: sudo systemctl restart supabase-mcp"
echo "5. Check logs: sudo journalctl -u supabase-mcp -f"
echo ""
echo "🌐 Your MCP server will be available at:"
echo "   http://$VPS_HOST:$REMOTE_PORT/sse"
echo ""
echo "💓 Health check:"
echo "   curl http://$VPS_HOST:$REMOTE_PORT/health"
