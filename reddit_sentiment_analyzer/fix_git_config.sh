#!/bin/bash
# Fix Git configuration for the correct account

echo "🔧 Fixing Git Configuration"
echo "============================"

# Check current Git configuration
echo "📋 Current Git configuration:"
echo "User name: $(git config --global user.name)"
echo "User email: $(git config --global user.email)"
echo ""

# Check if we're in a Git repository
if [ -d ".git" ]; then
    echo "✅ This is a Git repository"
    echo "Remote origin: $(git remote get-url origin 2>/dev/null || echo 'No remote set')"
else
    echo "❌ This is not a Git repository"
    echo "Initializing Git repository..."
    git init
fi

echo ""
echo "🔧 To fix your Git configuration, run these commands:"
echo ""
echo "# Set the correct user name and email"
echo "git config --global user.name 'Your Correct Name'"
echo "git config --global user.email 'your.correct.email@example.com'"
echo ""
echo "# Or set it only for this repository (recommended)"
echo "git config user.name 'Your Correct Name'"
echo "git config user.email 'your.correct.email@example.com'"
echo ""
echo "# Check your configuration"
echo "git config --list | grep user"
echo ""
echo "# If you need to change the remote repository"
echo "git remote set-url origin git@github.com:yourusername/yourrepo.git"
echo ""
echo "# Or add a new remote"
echo "git remote add origin git@github.com:yourusername/yourrepo.git"
