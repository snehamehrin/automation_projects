#!/usr/bin/env python3
"""
Git setup script for business_projects directory
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)

def setup_git_repo():
    """Set up Git repository for business_projects"""
    project_root = Path("/Users/snehamehrin/Desktop/business_projects")
    
    print("🔧 Setting up Git repository for business_projects")
    print("=" * 50)
    
    # Check if already a git repo
    success, output = run_command("git status", cwd=project_root)
    if success:
        print("✅ Git repository already exists")
        print("Current status:")
        print(output)
        return True
    
    # Initialize git repository
    print("📦 Initializing Git repository...")
    success, output = run_command("git init", cwd=project_root)
    if not success:
        print(f"❌ Failed to initialize Git: {output}")
        return False
    print("✅ Git repository initialized")
    
    # Create .gitignore
    print("📝 Creating .gitignore...")
    gitignore_content = """
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
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Data files
data/raw/
data/processed/
data/external/

# API keys and credentials
google_credentials.json
token.json
*.pem
*.key

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Node.js (if any frontend projects)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.next/
out/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/
"""
    
    with open(project_root / ".gitignore", "w") as f:
        f.write(gitignore_content.strip())
    print("✅ .gitignore created")
    
    # Add all files
    print("📁 Adding files to Git...")
    success, output = run_command("git add .", cwd=project_root)
    if not success:
        print(f"❌ Failed to add files: {output}")
        return False
    print("✅ Files added to Git")
    
    # Initial commit
    print("💾 Creating initial commit...")
    success, output = run_command('git commit -m "Initial commit: Reddit Sentiment Brand Analysis project"', cwd=project_root)
    if not success:
        print(f"❌ Failed to create initial commit: {output}")
        return False
    print("✅ Initial commit created")
    
    return True

def connect_remote_repo():
    """Connect to a remote repository"""
    project_root = Path("/Users/snehamehrin/Desktop/business_projects")
    
    print("\n🌐 Setting up remote repository connection")
    print("=" * 50)
    
    # Get remote URL from user
    print("Please provide your remote repository URL:")
    print("Examples:")
    print("  - GitHub: https://github.com/username/repo-name.git")
    print("  - GitLab: https://gitlab.com/username/repo-name.git")
    print("  - Bitbucket: https://bitbucket.org/username/repo-name.git")
    print()
    
    remote_url = input("Remote repository URL: ").strip()
    
    if not remote_url:
        print("❌ No remote URL provided")
        return False
    
    # Add remote origin
    print(f"🔗 Adding remote origin: {remote_url}")
    success, output = run_command(f"git remote add origin {remote_url}", cwd=project_root)
    if not success:
        print(f"❌ Failed to add remote: {output}")
        return False
    print("✅ Remote origin added")
    
    # Push to remote
    print("📤 Pushing to remote repository...")
    success, output = run_command("git push -u origin main", cwd=project_root)
    if not success:
        # Try with master branch if main fails
        print("Trying with master branch...")
        success, output = run_command("git push -u origin master", cwd=project_root)
        if not success:
            print(f"❌ Failed to push to remote: {output}")
            print("\n🔧 Manual steps needed:")
            print("1. Make sure the remote repository exists")
            print("2. Check your authentication (SSH keys or personal access token)")
            print("3. Try pushing manually: git push -u origin main")
            return False
    
    print("✅ Successfully pushed to remote repository")
    return True

def show_git_info():
    """Show current Git information"""
    project_root = Path("/Users/snehamehrin/Desktop/business_projects")
    
    print("\n📊 Current Git Status")
    print("=" * 30)
    
    # Show status
    success, output = run_command("git status", cwd=project_root)
    if success:
        print("Status:")
        print(output)
    
    # Show remotes
    success, output = run_command("git remote -v", cwd=project_root)
    if success:
        print("\nRemotes:")
        print(output)
    
    # Show last commit
    success, output = run_command("git log --oneline -1", cwd=project_root)
    if success:
        print(f"\nLast commit: {output}")

def main():
    """Main function"""
    print("🚀 Git Setup for Business Projects")
    print("=" * 50)
    print("This will set up Git for your entire business_projects directory")
    print("=" * 50)
    
    # Check if we're in the right directory
    project_root = Path("/Users/snehamehrin/Desktop/business_projects")
    if not project_root.exists():
        print("❌ business_projects directory not found!")
        return False
    
    try:
        # Setup Git repository
        if not setup_git_repo():
            return False
        
        # Ask if user wants to connect to remote
        print("\n" + "=" * 50)
        connect_remote = input("Do you want to connect to a remote repository? (y/n): ").strip().lower()
        
        if connect_remote == 'y':
            if not connect_remote_repo():
                print("⚠️  Remote connection failed, but local Git is set up")
        
        # Show final status
        show_git_info()
        
        print("\n🎉 Git setup completed!")
        print("\n📚 Useful Git commands:")
        print("  git status          - Check current status")
        print("  git add .           - Stage all changes")
        print("  git commit -m \"msg\" - Commit changes")
        print("  git push            - Push to remote")
        print("  git pull            - Pull from remote")
        print("  git log --oneline   - View commit history")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  Setup interrupted by user.")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
