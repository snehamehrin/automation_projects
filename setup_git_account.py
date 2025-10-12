#!/usr/bin/env python3
"""
Git setup script for multiple GitHub accounts
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

def check_current_git_config():
    """Check current Git configuration"""
    project_root = Path("/Users/snehamehrin/Desktop/business_projects")
    
    print("🔍 Checking current Git configuration...")
    
    # Check global config
    success, global_name = run_command("git config --global user.name")
    success, global_email = run_command("git config --global user.email")
    
    print(f"Global Git config:")
    print(f"  Name: {global_name if success else 'Not set'}")
    print(f"  Email: {global_email if success else 'Not set'}")
    
    # Check local config
    success, local_name = run_command("git config user.name", cwd=project_root)
    success, local_email = run_command("git config user.email", cwd=project_root)
    
    print(f"Local Git config:")
    print(f"  Name: {local_name if success else 'Not set'}")
    print(f"  Email: {local_email if success else 'Not set'}")
    
    return global_name, global_email, local_name, local_email

def setup_git_account():
    """Set up Git with the correct account"""
    project_root = Path("/Users/snehamehrin/Desktop/business_projects")
    
    print("\n🔧 Setting up Git account for this project")
    print("=" * 50)
    
    # Get account details
    print("Please provide your GitHub account details:")
    print()
    
    name = input("Your name (as it appears on GitHub): ").strip()
    email = input("Your GitHub email address: ").strip()
    
    if not name or not email:
        print("❌ Name and email are required")
        return False
    
    # Set local Git config for this project
    print(f"\n📝 Setting Git config for this project...")
    
    success, _ = run_command(f"git config user.name '{name}'", cwd=project_root)
    if not success:
        print("❌ Failed to set user name")
        return False
    
    success, _ = run_command(f"git config user.email '{email}'", cwd=project_root)
    if not success:
        print("❌ Failed to set user email")
        return False
    
    print("✅ Git account configured for this project")
    
    # Ask about SSH key setup
    print(f"\n🔑 SSH Key Setup")
    print("=" * 30)
    print("For multiple GitHub accounts, SSH keys are recommended.")
    print("This allows you to use different accounts for different projects.")
    print()
    
    setup_ssh = input("Do you want to set up SSH keys for this account? (y/n): ").strip().lower()
    
    if setup_ssh == 'y':
        setup_ssh_key(email)
    
    return True

def setup_ssh_key(email):
    """Set up SSH key for the account"""
    print(f"\n🔑 Setting up SSH key for {email}")
    print("=" * 40)
    
    # Generate SSH key
    ssh_key_name = f"id_ed25519_{email.split('@')[0]}"
    ssh_key_path = f"~/.ssh/{ssh_key_name}"
    
    print(f"Generating SSH key: {ssh_key_name}")
    
    success, output = run_command(f"ssh-keygen -t ed25519 -C '{email}' -f {ssh_key_path} -N ''")
    if not success:
        print(f"❌ Failed to generate SSH key: {output}")
        return False
    
    print("✅ SSH key generated")
    
    # Add to SSH agent
    print("Adding to SSH agent...")
    success, _ = run_command(f"ssh-add {ssh_key_path}")
    if success:
        print("✅ SSH key added to agent")
    else:
        print("⚠️  Could not add to SSH agent (this is okay)")
    
    # Display public key
    success, public_key = run_command(f"cat {ssh_key_path}.pub")
    if success:
        print(f"\n📋 Your public SSH key:")
        print("=" * 50)
        print(public_key)
        print("=" * 50)
        print("\n📝 Next steps:")
        print("1. Copy the public key above")
        print("2. Go to GitHub → Settings → SSH and GPG keys")
        print("3. Click 'New SSH key'")
        print(f"4. Paste the key and give it a title like 'Business Projects - {email}'")
        print("5. Click 'Add SSH key'")
        print()
        
        # Create SSH config
        create_ssh_config(email, ssh_key_name)
    
    return True

def create_ssh_config(email, ssh_key_name):
    """Create SSH config for multiple accounts"""
    ssh_config_path = Path.home() / ".ssh" / "config"
    
    print("🔧 Setting up SSH config for multiple accounts...")
    
    # Read existing config
    existing_config = ""
    if ssh_config_path.exists():
        with open(ssh_config_path, 'r') as f:
            existing_config = f.read()
    
    # Check if config already exists for this host
    host_name = f"github-{email.split('@')[0]}"
    if f"Host {host_name}" in existing_config:
        print(f"✅ SSH config already exists for {host_name}")
        return
    
    # Add new config
    new_config = f"""
# GitHub account for {email}
Host {host_name}
    HostName github.com
    User git
    IdentityFile ~/.ssh/{ssh_key_name}
    IdentitiesOnly yes
"""
    
    with open(ssh_config_path, 'a') as f:
        f.write(new_config)
    
    print(f"✅ SSH config added for {host_name}")
    print(f"Use this URL for your repository: git@{host_name}:username/repo-name.git")

def setup_remote_repo():
    """Set up remote repository with correct account"""
    project_root = Path("/Users/snehamehrin/Desktop/business_projects")
    
    print(f"\n🌐 Setting up remote repository")
    print("=" * 40)
    
    # Check if remote already exists
    success, output = run_command("git remote -v", cwd=project_root)
    if success and output:
        print("Current remotes:")
        print(output)
        print()
        replace = input("Remote already exists. Replace it? (y/n): ").strip().lower()
        if replace == 'y':
            run_command("git remote remove origin", cwd=project_root)
        else:
            return True
    
    print("Please provide your repository details:")
    print()
    
    username = input("GitHub username: ").strip()
    repo_name = input("Repository name: ").strip()
    
    if not username or not repo_name:
        print("❌ Username and repository name are required")
        return False
    
    # Check if SSH config exists
    success, output = run_command("git config user.email", cwd=project_root)
    if success:
        email = output
        host_name = f"github-{email.split('@')[0]}"
        
        # Check if SSH config exists for this account
        ssh_config_path = Path.home() / ".ssh" / "config"
        if ssh_config_path.exists():
            with open(ssh_config_path, 'r') as f:
                ssh_config = f.read()
            if f"Host {host_name}" in ssh_config:
                remote_url = f"git@{host_name}:{username}/{repo_name}.git"
                print(f"Using SSH URL: {remote_url}")
            else:
                remote_url = f"https://github.com/{username}/{repo_name}.git"
                print(f"Using HTTPS URL: {remote_url}")
        else:
            remote_url = f"https://github.com/{username}/{repo_name}.git"
            print(f"Using HTTPS URL: {remote_url}")
    else:
        remote_url = f"https://github.com/{username}/{repo_name}.git"
        print(f"Using HTTPS URL: {remote_url}")
    
    # Add remote
    print(f"Adding remote origin...")
    success, output = run_command(f"git remote add origin {remote_url}", cwd=project_root)
    if not success:
        print(f"❌ Failed to add remote: {output}")
        return False
    
    print("✅ Remote origin added")
    
    # Push to remote
    print("Pushing to remote repository...")
    success, output = run_command("git push -u origin main", cwd=project_root)
    if not success:
        # Try with master branch
        print("Trying with master branch...")
        success, output = run_command("git push -u origin master", cwd=project_root)
        if not success:
            print(f"❌ Failed to push: {output}")
            print("\n🔧 Manual steps needed:")
            print("1. Make sure the repository exists on GitHub")
            print("2. Check your authentication")
            print("3. Try: git push -u origin main")
            return False
    
    print("✅ Successfully pushed to remote repository")
    return True

def main():
    """Main function"""
    print("🔧 Git Account Setup for Business Projects")
    print("=" * 50)
    print("This will help you set up Git with the correct GitHub account")
    print("=" * 50)
    
    project_root = Path("/Users/snehamehrin/Desktop/business_projects")
    if not project_root.exists():
        print("❌ business_projects directory not found!")
        return False
    
    try:
        # Check current config
        check_current_git_config()
        
        # Setup account
        if not setup_git_account():
            return False
        
        # Ask about remote repository
        print(f"\n" + "=" * 50)
        setup_remote = input("Do you want to set up a remote repository now? (y/n): ").strip().lower()
        
        if setup_remote == 'y':
            if not setup_remote_repo():
                print("⚠️  Remote setup failed, but local Git is configured")
        
        print(f"\n🎉 Git account setup completed!")
        print(f"\n📚 Your project is now configured with the correct GitHub account")
        print(f"\n💡 Useful commands:")
        print(f"  git status          - Check current status")
        print(f"  git add .           - Stage all changes")
        print(f"  git commit -m \"msg\" - Commit changes")
        print(f"  git push            - Push to remote")
        print(f"  git pull            - Pull from remote")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Setup interrupted by user.")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
