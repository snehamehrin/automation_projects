# 🔧 Git Setup for Business Projects

## Quick Setup

Run the automated setup script:
```bash
cd /Users/snehamehrin/Desktop/business_projects
python setup_git.py
```

## Manual Setup

### 1. Initialize Git Repository
```bash
cd /Users/snehamehrin/Desktop/business_projects
git init
```

### 2. Create .gitignore
```bash
# Create .gitignore file with appropriate exclusions
touch .gitignore
```

### 3. Add Files and Commit
```bash
git add .
git commit -m "Initial commit: Business projects"
```

### 4. Connect to Remote Repository

#### Option A: GitHub
```bash
# Create a new repository on GitHub first, then:
git remote add origin https://github.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

#### Option B: GitLab
```bash
# Create a new repository on GitLab first, then:
git remote add origin https://gitlab.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

#### Option C: Bitbucket
```bash
# Create a new repository on Bitbucket first, then:
git remote add origin https://bitbucket.org/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

## 🔑 Authentication

### GitHub Personal Access Token
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token with repo permissions
3. Use token as password when prompted

### SSH Keys (Recommended)
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to SSH agent
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard
pbcopy < ~/.ssh/id_ed25519.pub

# Add to GitHub/GitLab/Bitbucket
```

## 📁 What Gets Tracked

The setup includes a comprehensive `.gitignore` that excludes:
- Python cache files (`__pycache__/`, `*.pyc`)
- Virtual environments (`venv/`, `env/`)
- Environment files (`.env`)
- IDE files (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`)
- Log files (`*.log`)
- Database files (`*.db`, `*.sqlite`)
- API keys and credentials
- Temporary files

## 🚀 Daily Git Workflow

```bash
# Check status
git status

# Add changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push to remote
git push

# Pull latest changes
git pull
```

## 🔄 Branching Strategy

```bash
# Create new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main
git checkout feature/new-feature

# Merge branch
git checkout main
git merge feature/new-feature

# Delete branch
git branch -d feature/new-feature
```

## 🆘 Troubleshooting

### Authentication Issues
```bash
# Check remote URL
git remote -v

# Update remote URL
git remote set-url origin https://github.com/username/repo.git
```

### Push Rejected
```bash
# Pull latest changes first
git pull origin main

# Then push
git push origin main
```

### Large Files
```bash
# Remove large files from history
git filter-branch --tree-filter 'rm -f path/to/large/file' HEAD
```

## 📚 Useful Commands

```bash
# View commit history
git log --oneline

# View changes
git diff

# View remote repositories
git remote -v

# Check branch status
git branch -a

# Stash changes
git stash
git stash pop

# Reset to last commit
git reset --hard HEAD
```

## 🎯 Best Practices

1. **Commit often** - Small, frequent commits
2. **Write clear messages** - "Fix bug" vs "Fix authentication error in login form"
3. **Use branches** - Don't work directly on main
4. **Pull before push** - Always sync with remote
5. **Review changes** - Use `git diff` before committing
6. **Keep .gitignore updated** - Add new file types as needed

## 🔐 Security Notes

- Never commit API keys or passwords
- Use environment variables for sensitive data
- Regularly rotate access tokens
- Use SSH keys instead of passwords when possible
- Review what you're committing with `git status` and `git diff`
