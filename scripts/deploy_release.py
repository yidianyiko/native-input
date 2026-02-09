#!/usr/bin/env python3
"""
Deploy Release - Automated release deployment script
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.release_manager import ReleaseManager


def deploy_release(version: str = None, github_token: str = None, 
                  release_notes: str = "", is_prerelease: bool = False):
    """Deploy a complete release"""
    
    print("Starting automated release deployment...")
    
    # Initialize release manager
    manager = ReleaseManager(project_root)
    
    # Use current version if not specified
    if not version:
        version = manager.current_version
        print(f"Using current version: {version}")
    
    # Step 1: Create release
    print(f"\nStep 1: Creating release {version}...")
    success = manager.create_release(version, release_notes, is_prerelease)
    
    if not success:
        print("Release creation failed!")
        return False
    
    # Step 2: Create update manifest
    print(f"\nStep 2: Creating update manifest...")
    success = manager.create_update_manifest(version)
    
    if not success:
        print("Update manifest creation failed, continuing...")
    
    # Step 3: Publish to GitHub (if token provided)
    if github_token:
        print(f"\nStep 3: Publishing to GitHub...")
        success = manager.publish_to_github(version, github_token)
        
        if not success:
            print("GitHub publishing failed!")
            return False
    else:
        print("\n⏭️ Step 3: Skipping GitHub publishing (no token provided)")
    
    # Step 4: Update version in project files
    print(f"\nStep 4: Updating project version...")
    success = update_project_version(version)
    
    if not success:
        print("Version update failed, continuing...")
    
    print(f"\nRelease {version} deployed successfully!")
    
    # Print summary
    print("\nRelease Summary:")
    print(f"   Version: {version}")
    print(f"   Prerelease: {is_prerelease}")
    print(f"   GitHub: {'Published' if github_token else 'Not published'}")
    
    release_info = manager.get_release_info(version)
    if release_info:
        print(f"   Files: {len(release_info.get('files', {}))}")
        total_size = sum(f.get('size_bytes', 0) for f in release_info.get('files', {}).values())
        print(f"   Total size: {total_size / (1024*1024):.1f} MB")
    
    return True


def update_project_version(new_version: str) -> bool:
    """Update version in project files"""
    try:
        # Update pyproject.toml
        pyproject_path = project_root / "pyproject.toml"
        
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            
            # Replace version line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('version = '):
                    lines[i] = f'version = "{new_version}"'
                    break
            
            pyproject_path.write_text('\n'.join(lines))
            print(f"   Updated pyproject.toml version to {new_version}")
        
        # Update main.py version
        main_py_path = project_root / "src" / "main.py"
        
        if main_py_path.exists():
            content = main_py_path.read_text()
            
            # Replace current_version line in UpdateManager initialization
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'self.current_version = ' in line:
                    lines[i] = f'        self.current_version = "{new_version}"'
                    break
            
            main_py_path.write_text('\n'.join(lines))
            print(f"   Updated main.py version to {new_version}")
        
        return True
        
    except Exception as e:
        print(f"   Failed to update project version: {e}")
        return False


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy AI Input Method Release")
    parser.add_argument("--version", help="Version to deploy (default: current)")
    parser.add_argument("--notes", help="Release notes file or text")
    parser.add_argument("--prerelease", action="store_true", help="Mark as prerelease")
    parser.add_argument("--github-token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--repo", default="ai-input-method/ai-input-method", help="GitHub repository")
    
    args = parser.parse_args()
    
    # Get GitHub token from args or environment
    github_token = args.github_token or os.getenv("GITHUB_TOKEN")
    
    # Load release notes
    release_notes = ""
    if args.notes:
        notes_path = Path(args.notes)
        if notes_path.exists():
            release_notes = notes_path.read_text()
        else:
            release_notes = args.notes
    
    # Deploy release
    success = deploy_release(
        version=args.version,
        github_token=github_token,
        release_notes=release_notes,
        is_prerelease=args.prerelease
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())