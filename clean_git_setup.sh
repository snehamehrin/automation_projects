#!/bin/bash
# Clean Git setup for automation_projects folder

echo "🧹 Cleaning Git Configuration for Automation Projects"
echo "====================================================="

# Navigate to automation_projects folder
cd /Users/snehamehrin/Desktop/automation_projects

echo "📁 Current directory: $(pwd)"
echo "📋 Contents:"
ls -la

echo ""
echo "🗑️  Removing existing Git configuration..."

# Remove existing .git folder if it exists
if [ -d ".git" ]; then
    echo "Removing existing .git folder..."
    rm -rf .git
    echo "✅ Removed existing Git repository"
else
    echo "No existing .git folder found"
fi

echo ""
echo "🔧 Setting up fresh Git repository..."

# Initialize new Git repository
git init

# Create .gitignore file
echo "📝 Creating .gitignore file..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
.venv/
env/
.env/

# Environment variables
.env
*.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Data files
*.csv
*.json
*.xlsx
*.pdf

# API Keys and sensitive files
google_console_key.json
token.pickle
EOF

echo "✅ Created .gitignore file"

# Add all files
echo "📦 Adding files to Git..."
git add .

# Make initial commit
echo "💾 Making initial commit..."
git commit -m "Initial commit: Automation projects collection"

echo ""
echo "✅ Fresh Git repository created!"
echo ""
echo "📋 Next steps:"
echo "1. Create a GitHub repository called 'automation_projects'"
echo "2. Add remote origin:"
echo "   git remote add origin git@github.com:yourusername/automation_projects.git"
echo "3. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "🔗 GitHub repository URL: https://github.com/new"
