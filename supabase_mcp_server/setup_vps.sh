#!/bin/bash
# Setup script to run on VPS after git pull

set -e

echo "🔧 Setting up Supabase MCP Server on VPS..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-server.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Please create .env file with:"
    echo "   SUPABASE_URL=your_url"
    echo "   SUPABASE_KEY=your_key"
    echo "   HOST=0.0.0.0"
    echo "   PORT=8000"
    exit 1
fi

# Create systemd service
echo "🔧 Setting up systemd service..."
sudo tee /etc/systemd/system/supabase-mcp.service > /dev/null << EOF
[Unit]
Description=Supabase MCP Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python server_remote.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl enable supabase-mcp
sudo systemctl restart supabase-mcp

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Service status:"
sudo systemctl status supabase-mcp --no-pager
echo ""
echo "📋 Useful commands:"
echo "  Check logs: sudo journalctl -u supabase-mcp -f"
echo "  Restart: sudo systemctl restart supabase-mcp"
echo "  Stop: sudo systemctl stop supabase-mcp"
echo ""
echo "🌐 Server running at: http://$(hostname -I | awk '{print $1}'):8000/sse"
