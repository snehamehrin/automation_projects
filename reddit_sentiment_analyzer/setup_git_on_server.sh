#!/bin/bash
# Setup Git on Hostinger server and clone repository

echo "🔧 Setting up Git on Hostinger Server"
echo "====================================="

# Navigate to workspace
cd ~/workspace/projects

# Install Git if not already installed
echo "📦 Installing Git..."
sudo apt update
sudo apt install -y git

# Configure Git (you'll need to set your name and email)
echo "⚙️  Configuring Git..."
echo "Please run these commands with your details:"
echo "git config --global user.name 'Your Name'"
echo "git config --global user.email 'your.email@example.com'"

# Create SSH key for GitHub (if you don't have one)
echo "🔑 Setting up SSH key for GitHub..."
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "Generating SSH key..."
    ssh-keygen -t rsa -b 4096 -C "your.email@example.com" -f ~/.ssh/id_rsa -N ""
    echo "✅ SSH key generated!"
    echo "📋 Add this public key to your GitHub account:"
    cat ~/.ssh/id_rsa.pub
    echo ""
    echo "🔗 Go to: https://github.com/settings/ssh/new"
else
    echo "✅ SSH key already exists"
    echo "📋 Your public key:"
    cat ~/.ssh/id_rsa.pub
fi

echo ""
echo "📋 Next steps:"
echo "1. Add the SSH key above to your GitHub account"
echo "2. Test connection: ssh -T git@github.com"
echo "3. Clone your repository: git clone git@github.com:yourusername/yourrepo.git"
echo "4. Navigate to project: cd yourrepo"
echo "5. Install dependencies: pip install -r requirements.txt"
