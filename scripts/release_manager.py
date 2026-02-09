#!/usr/bin/env python3
"""
Release Manager - Handles creating and publishing releases
"""

import json
import hashlib
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import tomli


class ReleaseManager:
    """Manages application releases and distribution"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.releases_dir = self.project_root / "releases"
        
        # Load project configuration
        self.project_config = self._load_project_config()
        self.current_version = self.project_config.get("project", {}).get("version", "0.1.0")
        
        print(f"Release Manager initialized for version {self.current_version}")
    
    def _load_project_config(self) -> Dict:
        """Load project configuration from pyproject.toml"""
        try:
            pyproject_path = self.project_root / "pyproject.toml"
            with open(pyproject_path, "rb") as f:
                return tomli.load(f)
        except Exception as e:
            print(f"Failed to load project config: {e}")
            return {}
    
    def create_release(self, version: str = None, release_notes: str = "", is_prerelease: bool = False) -> bool:
        """Create a new release"""
        try:
            version = version or self.current_version
            print(f"Creating release {version}...")
            
            # Create release directory
            release_dir = self.releases_dir / version
            release_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if executable exists, build if needed
            exe_path = self.dist_dir / "reInput.exe"
            if not exe_path.exists():
                print("Building executable...")
                if not self._build_executable():
                    return False
            else:
                print("Using existing executable...")
            
            # Create installer (skip if NSIS not available)
            print("Creating installer...")
            installer_path = self._create_installer(version)
            if not installer_path:
                print("Installer creation skipped (NSIS not available or failed)")
                installer_path = None
            
            # Create ZIP package
            print("🗜️ Creating ZIP package...")
            zip_path = self._create_zip_package(version)
            if not zip_path:
                return False
            
            # Generate checksums
            print("Generating checksums...")
            files_to_checksum = [f for f in [installer_path, zip_path] if f is not None]
            checksums = self._generate_checksums(files_to_checksum)
            
            # Create release metadata
            print("Creating release metadata...")
            metadata = self._create_release_metadata(
                version, release_notes, is_prerelease, 
                installer_path, zip_path, checksums
            )
            
            # Save metadata
            metadata_path = release_dir / "release.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Release {version} created successfully!")
            print(f"Release directory: {release_dir}")
            
            return True
            
        except Exception as e:
            print(f"Failed to create release: {e}")
            return False
    
    def _build_executable(self) -> bool:
        """Build executable using existing build script"""
        try:
            build_script = self.project_root / "scripts" / "build_executable.py"
            if not build_script.exists():
                print("Build script not found")
                return False
            
            # Run build script using uv
            result = subprocess.run(
                ["uv", "run", "python", str(build_script)],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Build failed: {result.stderr}")
                return False
            
            print("Executable built successfully")
            return True
            
        except Exception as e:
            print(f"Failed to build executable: {e}")
            return False
    
    def _create_installer(self, version: str) -> Optional[Path]:
        """Create installer using existing installer script"""
        try:
            installer_script = self.project_root / "scripts" / "build_installer.py"
            if not installer_script.exists():
                print("Installer script not found")
                return None
            
            # Run installer script using uv
            result = subprocess.run(
                ["uv", "run", "python", str(installer_script)],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Installer creation failed:")
                print(f"Return code: {result.returncode}")
                print(f"STDERR: {result.stderr}")
                print(f"STDOUT: {result.stdout}")
                return None
            
            # Find created installer
            installer_pattern = f"ai-input-method-installer-*.exe"
            installer_files = list(self.dist_dir.glob(installer_pattern))
            
            if installer_files:
                installer_path = installer_files[0]  # Use the first match
            else:
                # Try alternative naming patterns
                installer_path = self.dist_dir / f"ai-input-method-{version}-setup.exe"
                if not installer_path.exists():
                    installer_path = self.dist_dir / "ai-input-method-setup.exe"
            
            if installer_path.exists():
                print(f"Installer created: {installer_path}")
                return installer_path
            else:
                print("Installer file not found")
                return None
                
        except Exception as e:
            print(f"Failed to create installer: {e}")
            return None
    
    def _create_zip_package(self, version: str) -> Optional[Path]:
        """Create ZIP package for portable distribution"""
        try:
            # Find executable
            exe_path = self.dist_dir / "reInput.exe"
            if not exe_path.exists():
                print("Executable not found for ZIP package")
                return None
            
            # Create ZIP package
            zip_path = self.dist_dir / f"reInput-{version}-portable.zip"
            added_files = set()  # Track added files to avoid duplicates
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add the main executable
                zipf.write(exe_path, "reInput.exe")
                added_files.add("reInput.exe")
                
                # Add configuration files if they exist
                config_files = [
                    self.dist_dir / "settings.toml.example",
                    self.project_root / "settings.toml.example"
                ]
                
                for config_file in config_files:
                    if config_file.exists():
                        zipf.write(config_file, config_file.name)
                        added_files.add(config_file.name)
                        break  # Only add one copy
                
                # Add additional configuration files
                additional_config_files = [
                    "config.json",
                    ".env.example",
                    "README.md",
                    "LICENSE"
                ]
                
                for config_file in additional_config_files:
                    config_path = self.project_root / config_file
                    if config_path.exists() and config_file not in added_files:
                        zipf.write(config_path, config_file)
                        added_files.add(config_file)
                
                # Add resources
                resources_dir = self.project_root / "resources"
                if resources_dir.exists():
                    for resource_file in resources_dir.rglob("*"):
                        if resource_file.is_file():
                            arcname = resource_file.relative_to(self.project_root)
                            arcname_str = str(arcname)
                            if arcname_str not in added_files:
                                zipf.write(resource_file, arcname_str)
                                added_files.add(arcname_str)
            
            print(f"ZIP package created: {zip_path}")
            return zip_path
            
        except Exception as e:
            print(f"Failed to create ZIP package: {e}")
            return None
    
    def _generate_checksums(self, file_paths: List[Path]) -> Dict[str, str]:
        """Generate SHA256 checksums for files"""
        checksums = {}
        
        for file_path in file_paths:
            if file_path and file_path.exists():
                try:
                    checksum = self._calculate_sha256(file_path)
                    checksums[file_path.name] = checksum
                    print(f"Checksum for {file_path.name}: {checksum[:16]}...")
                    
                except Exception as e:
                    print(f"Failed to generate checksum for {file_path}: {e}")
        
        return checksums
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _create_release_metadata(self, version: str, release_notes: str, is_prerelease: bool,
                               installer_path: Path, zip_path: Path, checksums: Dict[str, str]) -> Dict:
        """Create release metadata"""
        metadata = {
            "version": version,
            "release_date": datetime.now().isoformat(),
            "is_prerelease": is_prerelease,
            "release_notes": release_notes,
            "files": {},
            "checksums": checksums,
            "system_requirements": {
                "os": "Windows 10/11",
                "architecture": "x64",
                "python": "3.10+",
                "memory": "512MB",
                "disk_space": "100MB"
            }
        }
        
        # Add file information
        if installer_path and installer_path.exists():
            metadata["files"]["installer"] = {
                "filename": installer_path.name,
                "size_bytes": installer_path.stat().st_size,
                "type": "installer"
            }
        
        if zip_path and zip_path.exists():
            metadata["files"]["portable"] = {
                "filename": zip_path.name,
                "size_bytes": zip_path.stat().st_size,
                "type": "portable"
            }
        
        return metadata
    
    def publish_to_github(self, version: str, github_token: str, repo: str = "ai-input-method/ai-input-method") -> bool:
        """Publish release to GitHub"""
        try:
            print(f"Publishing release {version} to GitHub...")
            
            release_dir = self.releases_dir / version
            metadata_path = release_dir / "release.json"
            
            if not metadata_path.exists():
                print("Release metadata not found")
                return False
            
            # Load metadata
            with open(metadata_path) as f:
                metadata = json.load(f)
            
            # Create GitHub release
            release_data = {
                "tag_name": f"v{version}",
                "name": f"AI Input Method v{version}",
                "body": metadata["release_notes"],
                "draft": False,
                "prerelease": metadata["is_prerelease"]
            }
            
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Create release (HTTPClient not available, using requests)
            try:
                import requests
                response = requests.post(
                    f"https://api.github.com/repos/{repo}/releases",
                    json=release_data,
                    headers=headers,
                    timeout=60
                )
            except ImportError:
                print("requests library not available for GitHub publishing")
                return False
            
            if response.status_code != 201:
                print(f"Failed to create GitHub release: {response.text}")
                return False
            
            release_info = response.json()
            upload_url = release_info["upload_url"].replace("{?name,label}", "")
            
            # Upload assets
            for file_info in metadata["files"].values():
                file_path = self.dist_dir / file_info["filename"]
                if file_path.exists():
                    self._upload_github_asset(upload_url, file_path, github_token)
            
            print(f"Release published to GitHub: {release_info['html_url']}")
            return True
            
        except Exception as e:
            print(f"Failed to publish to GitHub: {e}")
            return False
    
    def _upload_github_asset(self, upload_url: str, file_path: Path, github_token: str) -> bool:
        """Upload asset to GitHub release"""
        try:
            headers = {
                "Authorization": f"token {github_token}",
                "Content-Type": "application/octet-stream"
            }
            
            with open(file_path, "rb") as f:
                try:
                    import requests
                    response = requests.post(
                        f"{upload_url}?name={file_path.name}",
                        data=f.read(),
                        headers=headers,
                        timeout=300
                    )
                except ImportError:
                    print("requests library not available for GitHub asset upload")
                    return False
            
            if response.status_code == 201:
                print(f"Uploaded asset: {file_path.name}")
                return True
            else:
                print(f"Failed to upload asset {file_path.name}: {response.text}")
                return False
                
        except Exception as e:
            print(f"Failed to upload asset {file_path.name}: {e}")
            return False
    
    def create_update_manifest(self, version: str) -> bool:
        """Create update manifest for automatic updates"""
        try:
            print(f"Creating update manifest for {version}...")
            
            release_dir = self.releases_dir / version
            metadata_path = release_dir / "release.json"
            
            if not metadata_path.exists():
                print("Release metadata not found")
                return False
            
            # Load metadata
            with open(metadata_path) as f:
                metadata = json.load(f)
            
            # Create update manifest
            manifest = {
                "version": version,
                "release_date": metadata["release_date"],
                "is_critical": metadata.get("is_critical", False),
                "min_version": metadata.get("min_version"),
                "release_notes": metadata["release_notes"],
                "downloads": {}
            }
            
            # Add download URLs (these would be actual URLs in production)
            base_url = f"https://github.com/ai-input-method/ai-input-method/releases/download/v{version}/"
            
            for file_type, file_info in metadata["files"].items():
                manifest["downloads"][file_type] = {
                    "url": base_url + file_info["filename"],
                    "checksum": metadata["checksums"].get(file_info["filename"], ""),
                    "size_bytes": file_info["size_bytes"]
                }
            
            # Save manifest
            manifest_path = release_dir / "update_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"Update manifest created: {manifest_path}")
            return True
            
        except Exception as e:
            print(f"Failed to create update manifest: {e}")
            return False
    
    def list_releases(self) -> List[str]:
        """List available releases"""
        if not self.releases_dir.exists():
            return []
        
        releases = []
        for release_dir in self.releases_dir.iterdir():
            if release_dir.is_dir() and (release_dir / "release.json").exists():
                releases.append(release_dir.name)
        
        return sorted(releases, reverse=True)
    
    def get_release_info(self, version: str) -> Optional[Dict]:
        """Get release information"""
        try:
            metadata_path = self.releases_dir / version / "release.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to get release info for {version}: {e}")
        
        return None


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Input Method Release Manager")
    parser.add_argument("command", choices=["create", "publish", "list", "info"])
    parser.add_argument("--version", help="Version to create/publish")
    parser.add_argument("--notes", help="Release notes")
    parser.add_argument("--prerelease", action="store_true", help="Mark as prerelease")
    parser.add_argument("--github-token", help="GitHub token for publishing")
    parser.add_argument("--repo", default="ai-input-method/ai-input-method", help="GitHub repository")
    
    args = parser.parse_args()
    
    manager = ReleaseManager()
    
    if args.command == "create":
        version = args.version or manager.current_version
        notes = args.notes or f"Release {version}"
        
        success = manager.create_release(version, notes, args.prerelease)
        if success:
            manager.create_update_manifest(version)
        
        return 0 if success else 1
    
    elif args.command == "publish":
        if not args.github_token:
            print("GitHub token required for publishing")
            return 1
        
        version = args.version or manager.current_version
        success = manager.publish_to_github(version, args.github_token, args.repo)
        return 0 if success else 1
    
    elif args.command == "list":
        releases = manager.list_releases()
        if releases:
            print("Available releases:")
            for release in releases:
                print(f"  - {release}")
        else:
            print("No releases found")
        return 0
    
    elif args.command == "info":
        if not args.version:
            print("Version required for info command")
            return 1
        
        info = manager.get_release_info(args.version)
        if info:
            print(f"Release {args.version} info:")
            print(json.dumps(info, indent=2))
        else:
            print(f"Release {args.version} not found")
        return 0
    
    return 1


if __name__ == "__main__":
    exit(main())