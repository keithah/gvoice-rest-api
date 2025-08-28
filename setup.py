#!/usr/bin/env python3
"""
Setup script for Google Voice REST API
"""

import os
import sys
import subprocess
import secrets
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)


def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if not os.path.exists('.env'):
        print("Creating .env file...")
        
        # Generate a secure secret key
        secret_key = secrets.token_urlsafe(32)
        
        # Read template
        with open('.env.example', 'r') as f:
            template = f.read()
        
        # Replace secret key
        env_content = template.replace('change-this-to-a-random-secret-key', secret_key)
        
        # Write .env file
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✓ Created .env file with secure secret key")
    else:
        print("✓ .env file already exists")


def create_config_directory():
    """Create ~/.config/gvoice directory structure"""
    config_dir = Path.home() / '.config' / 'gvoice'
    subdirs = ['sessions', 'users', 'gv_sessions']
    
    for subdir in subdirs:
        dir_path = config_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created config directory: {config_dir}")


def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling dependencies...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Not running in a virtual environment!")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Please activate a virtual environment first:")
            print("  python -m venv venv")
            print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
            sys.exit(1)
    
    # Install requirements
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    print("✓ Dependencies installed")


def main():
    """Run setup process"""
    print("Google Voice REST API Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Create config directory
    create_config_directory()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    install_dependencies()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Review and edit .env file if needed")
    print("2. Run the server: python run.py")
    print("3. Visit API docs: http://localhost:8000/docs")
    print("\nFor cookie extraction instructions, see README.md")


if __name__ == "__main__":
    main()