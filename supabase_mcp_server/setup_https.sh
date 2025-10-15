#!/bin/bash
# Setup HTTPS for productalchemy.net MCP Server

set -e

DOMAIN="productalchemy.net"
EMAIL="your-email@example.com"  # Change this to your email

echo "🔧 Setting up HTTPS for $DOMAIN"

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install Nginx and Certbot
echo "📦 Installing Nginx and Certbot..."
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx configuration
echo "📝 Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/mcp > /dev/null <<'EOF'
server {
    listen 80;
    server_name productalchemy.net;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
echo "✅ Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/mcp /etc/nginx/sites-enabled/

# Remove default site if exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx

# Get SSL certificate
echo "🔒 Getting SSL certificate from Let's Encrypt..."
echo "NOTE: Make sure your domain DNS is pointing to this server!"
echo "Waiting 10 seconds for you to verify..."
sleep 10

sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL || {
    echo "⚠️  SSL certificate setup failed. This usually means:"
    echo "   1. DNS hasn't propagated yet (wait a few minutes and try again)"
    echo "   2. Port 80 is blocked by firewall"
    echo "   3. Domain doesn't point to this server"
    echo ""
    echo "You can retry with: sudo certbot --nginx -d $DOMAIN"
    exit 1
}

# Setup auto-renewal
echo "🔄 Setting up SSL auto-renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

echo ""
echo "✅ HTTPS setup complete!"
echo ""
echo "🌐 Your MCP server is now available at:"
echo "   https://productalchemy.net/sse"
echo ""
echo "💓 Health check:"
echo "   curl https://productalchemy.net/health"
echo ""
echo "📋 Next steps:"
echo "1. Update your Claude Desktop config to use: https://productalchemy.net/sse"
echo "2. Restart Claude Desktop"
echo ""
