#!/bin/bash
# Setup Traefik to route to MCP Server with SSL

set -e

echo "🔧 Setting up Traefik routing for MCP Server"

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

# Backup original docker-compose.yml
echo "💾 Backing up docker-compose.yml..."
cp /root/docker-compose.yml /root/docker-compose.yml.backup

# Update docker-compose.yml to add file provider
echo "📝 Updating docker-compose.yml..."
cat > /root/docker-compose.yml <<'EOF'
version: "3.7"

services:
  traefik:
    image: "traefik"
    restart: always
    command:
      - "--api=true"
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.file.directory=/traefik-config"
      - "--providers.file.watch=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.mytlschallenge.acme.tlschallenge=true"
      - "--certificatesresolvers.mytlschallenge.acme.email=${SSL_EMAIL}"
      - "--certificatesresolvers.mytlschallenge.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - traefik_data:/letsencrypt
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /root/traefik-config:/traefik-config:ro

  n8n:
    image: docker.n8n.io/n8nio/n8n
    restart: always
    ports:
      - "127.0.0.1:5678:5678"
    labels:
      - traefik.enable=true
      - traefik.http.routers.n8n.rule=Host(`${SUBDOMAIN}.${DOMAIN_NAME}`)
      - traefik.http.routers.n8n.tls=true
      - traefik.http.routers.n8n.entrypoints=web,websecure
      - traefik.http.routers.n8n.tls.certresolver=mytlschallenge
      - traefik.http.middlewares.n8n.headers.SSLRedirect=true
      - traefik.http.middlewares.n8n.headers.STSSeconds=315360000
      - traefik.http.middlewares.n8n.headers.browserXSSFilter=true
      - traefik.http.middlewares.n8n.headers.contentTypeNosniff=true
      - traefik.http.middlewares.n8n.headers.forceSTSHeader=true
      - traefik.http.middlewares.n8n.headers.SSLHost=${DOMAIN_NAME}
      - traefik.http.middlewares.n8n.headers.STSIncludeSubdomains=true
      - traefik.http.middlewares.n8n.headers.STSPreload=true
      - traefik.http.routers.n8n.middlewares=n8n@docker
    environment:
      - N8N_HOST=${SUBDOMAIN}.${DOMAIN_NAME}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - NODE_ENV=production
      - WEBHOOK_URL=https://${SUBDOMAIN}.${DOMAIN_NAME}/
      - GENERIC_TIMEZONE=${GENERIC_TIMEZONE}
    volumes:
      - n8n_data:/home/node/.n8n
      - /local-files:/files

volumes:
  traefik_data:
    external: true
  n8n_data:
    external:
EOF

# Restart Traefik
echo "🔄 Restarting Traefik..."
cd /root
docker-compose restart traefik

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
