#!/bin/bash
# Simple Traefik setup for MCP Server

set -e

echo "🔧 Setting up Traefik routing for MCP Server"

# Restore backup if it exists
if [ -f /root/docker-compose.yml.backup ]; then
    echo "💾 Restoring original docker-compose.yml..."
    cp /root/docker-compose.yml.backup /root/docker-compose.yml
fi

# Create Traefik config directory
echo "📁 Creating Traefik config directory..."
mkdir -p /root/traefik-config

# Create Traefik file provider config for MCP
echo "📝 Creating Traefik configuration for MCP server..."
cat > /root/traefik-config/mcp.yml <<'EOF'
http:
  routers:
    mcp-server:
      rule: "Host(`productalchemy.net`)"
      service: mcp-server
      entryPoints:
        - websecure
      tls:
        certResolver: mytlschallenge

  services:
    mcp-server:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8000"
EOF

# Add file provider to traefik service in docker-compose.yml
echo "📝 Updating docker-compose.yml to add file provider..."
cd /root

# Check if already added
if grep -q "providers.file.directory" docker-compose.yml; then
    echo "✅ File provider already configured"
else
    # Add the file provider lines after the docker provider line
    sed -i '/providers.docker.exposedbydefault=false/a\      - "--providers.file.directory=/traefik-config"\n      - "--providers.file.watch=true"' docker-compose.yml
    echo "✅ Added file provider configuration"
fi

# Check if volume is already added
if grep -q "/root/traefik-config:/traefik-config:ro" docker-compose.yml; then
    echo "✅ Traefik config volume already mounted"
else
    # Add volume mount after docker.sock line
    sed -i '/\/var\/run\/docker.sock:\/var\/run\/docker.sock:ro/a\      - /root/traefik-config:/traefik-config:ro' docker-compose.yml
    echo "✅ Added traefik-config volume mount"
fi

# Restart Traefik
echo "🔄 Restarting Traefik..."
docker compose restart traefik

# Wait for Traefik to start
echo "⏳ Waiting for Traefik to initialize..."
sleep 5

# Check if MCP server is running
echo "🔍 Checking MCP server status..."
sudo systemctl status supabase-mcp --no-pager || true

echo ""
echo "✅ Traefik configuration complete!"
echo ""
echo "🌐 Your MCP server should now be available at:"
echo "   https://productalchemy.net/sse"
echo ""
echo "💓 Test with:"
echo "   curl https://productalchemy.net/health"
echo ""
echo "📋 If it doesn't work immediately, wait 30 seconds for SSL certificate generation"
echo ""
