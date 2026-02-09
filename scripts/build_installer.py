#!/usr/bin/env python3
"""
Installer Build Script for AI Input Method Tool
Creates Windows installer using NSIS after building the executable
"""

import os
import sys
import subprocess
import shutil
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        import toml as tomllib  # Final fallback
from pathlib import Path
from typing import Optional, Tuple

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
BUILD_PATH = PROJECT_ROOT / "build"
DIST_PATH = PROJECT_ROOT / "dist"
INSTALLER_PATH = PROJECT_ROOT / "installer"
NSIS_SCRIPT = INSTALLER_PATH / "ai-input-method-installer.nsi"

class InstallerBuildError(Exception):
    """Custom exception for installer build errors"""
    pass

class InstallerBuilder:
    """Handles Windows installer creation using NSIS"""
    
    def __init__(self):
        self.nsis_path = self.find_nsis_installation()
        
    def log(self, message: str, level: str = "INFO") -> None:
        """Log build messages"""
        prefix = "[INFO]" if level == "INFO" else "[WARN]" if level == "WARN" else "[ERROR]"
        print(f"{prefix} {message}")
        
    def find_nsis_installation(self) -> Optional[Path]:
        """Find NSIS installation on the system"""
        possible_paths = [
            Path("C:/Program Files (x86)/NSIS/makensis.exe"),
            Path("C:/Program Files/NSIS/makensis.exe"),
            Path("D:/Program Files (x86)/NSIS/makensis.exe"),
            Path("D:/Program Files/NSIS/makensis.exe"),
            Path("C:/NSIS/makensis.exe"),
            Path("D:/NSIS/makensis.exe"),
        ]
        
        # Check PATH
        try:
            result = subprocess.run(["where", "makensis"], capture_output=True, text=True)
            if result.returncode == 0:
                return Path(result.stdout.strip().split('\n')[0])
        except:
            pass
            
        # Check common installation paths
        for path in possible_paths:
            if path.exists():
                return path
                
        return None
    
    def validate_prerequisites(self) -> None:
        """Validate that all prerequisites are met"""
        self.log("Validating installer prerequisites...")
        
        # Check if executable exists
        exe_path = DIST_PATH / "reInput.exe"
        if not exe_path.exists():
            raise InstallerBuildError(
                f"Executable not found: {exe_path}\n"
                "Please run 'python scripts/build_executable.py' first"
            )
            
        # Check NSIS installation
        if not self.nsis_path:
            raise InstallerBuildError(
                "NSIS not found. Please install NSIS from https://nsis.sourceforge.io/\n"
                "Make sure makensis.exe is in your PATH or installed in a standard location"
            )
            
        self.log(f"Using NSIS: {self.nsis_path}")
        
        # Check NSIS script
        if not NSIS_SCRIPT.exists():
            raise InstallerBuildError(f"NSIS script not found: {NSIS_SCRIPT}")
            
        # Check required resources
        resources_to_check = [
            PROJECT_ROOT / "LICENSE",
            PROJECT_ROOT / "app.ico"
        ]
        
        missing_resources = []
        for resource in resources_to_check:
            if not resource.exists():
                missing_resources.append(str(resource))
                
        if missing_resources:
            self.log(f"Warning: Missing resources: {', '.join(missing_resources)}", "WARN")
            
        self.log("Prerequisites validation passed")
    
    def prepare_installer_build(self) -> None:
        """Prepare files for installer build"""
        self.log("Preparing installer build...")
        
        # Ensure LICENSE file exists (create minimal one if missing)
        license_file = PROJECT_ROOT / "LICENSE"
        if not license_file.exists():
            self.log("Creating minimal LICENSE file", "WARN")
            with open(license_file, "w") as f:
                f.write("MIT License\n\nCopyright (c) 2025 AI Input Method Team\n\n"
                       "Permission is hereby granted, free of charge, to any person obtaining a copy "
                       "of this software and associated documentation files (the \"Software\"), to deal "
                       "in the Software without restriction, including without limitation the rights "
                       "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
                       "copies of the Software, and to permit persons to whom the Software is "
                       "furnished to do so, subject to the following conditions:\n\n"
                       "The above copyright notice and this permission notice shall be included in all "
                       "copies or substantial portions of the Software.\n\n"
                       "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
                       "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
                       "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE "
                       "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER "
                       "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, "
                       "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE "
                       "SOFTWARE.")
        
        # Ensure app icon exists (create placeholder if missing)
        icon_file = PROJECT_ROOT / "app.ico"
        if not icon_file.exists():
            self.log("App icon missing - installer will use default icon", "WARN")
            # Note: In a real scenario, you'd want to create or copy an actual .ico file
            
        # Copy configuration files to dist directory
        self.copy_config_files_to_dist()
            
        self.log("Installer build preparation completed")
    
    def copy_config_files_to_dist(self) -> None:
        """Copy configuration files to dist directory for installer"""
        self.log("Copying configuration files to dist directory...")
        
        # Ensure dist directory exists
        DIST_PATH.mkdir(exist_ok=True)
        
        # Copy settings.toml.example to dist
        settings_example = PROJECT_ROOT / "settings.toml.example"
        if settings_example.exists():
            dest_example = DIST_PATH / "settings.toml.example"
            shutil.copy2(settings_example, dest_example)
            self.log(f"Copied {settings_example.name} to dist directory")
        else:
            self.log("Warning: settings.toml.example not found in project root", "WARN")
        
        # Create a default settings.toml in dist if it doesn't exist
        # This ensures the installer has a settings.toml file to include
        settings_toml = DIST_PATH / "settings.toml"
        if not settings_toml.exists():
            if settings_example.exists():
                # Copy example as default settings.toml
                shutil.copy2(settings_example, settings_toml)
                self.log("Created default settings.toml from example file")
            else:
                # Create minimal settings.toml
                self.log("Creating minimal settings.toml file", "WARN")
                with open(settings_toml, "w") as f:
                    f.write("# AI Input Method Configuration\n")
                    f.write("# This file will be created with default settings on first run\n")
                    f.write("\n[app]\n")
                    f.write("name = \"AI Input Method\"\n")
                    f.write("version = \"0.02\"\n")
        else:
            self.log("settings.toml already exists in dist directory")
    
    def get_project_version(self) -> str:
        """Get version from pyproject.toml"""
        try:
            pyproject_path = PROJECT_ROOT / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, 'rb') as f:
                    data = tomllib.load(f)
                    return data.get('project', {}).get('version', '0.0.1')
        except Exception as e:
            self.log(f"Warning: Could not read version from pyproject.toml: {e}", "WARN")
        return "0.0.1"
    
    def build_installer(self) -> Path:
        """Build the Windows installer using NSIS"""
        self.log("Building Windows installer...")
        
        # Get version from pyproject.toml
        version = self.get_project_version()
        self.log(f"Using version: {version}")
        
        # Run NSIS compiler with version parameter
        cmd = [str(self.nsis_path), f"/DAPP_VERSION={version}", str(NSIS_SCRIPT)]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                raise InstallerBuildError(
                    f"NSIS compilation failed:\n{result.stderr}\n{result.stdout}"
                )
                
            # Find the generated installer
            installer_pattern = DIST_PATH.glob("ai-input-method-installer-*.exe")
            installer_files = list(installer_pattern)
            
            if not installer_files:
                raise InstallerBuildError("Installer file not found after NSIS compilation")
                
            installer_file = installer_files[0]
            file_size = installer_file.stat().st_size / (1024 * 1024)
            
            self.log(f"Installer created: {installer_file}")
            self.log(f"Installer size: {file_size:.1f} MB")
            self.log("Windows installer build completed")
            
            return installer_file
            
        except subprocess.TimeoutExpired:
            raise InstallerBuildError("NSIS compilation timed out")
        except Exception as e:
            raise InstallerBuildError(f"Failed to build installer: {e}")
    
    def validate_installer(self, installer_path: Path) -> None:
        """Validate the built installer"""
        self.log("Validating installer...")
        
        if not installer_path.exists():
            raise InstallerBuildError(f"Installer file not found: {installer_path}")
            
        # Check file size
        file_size = installer_path.stat().st_size
        if file_size < 1024 * 1024:  # Less than 1MB
            raise InstallerBuildError("Installer file seems too small")
            
        # TODO: Add more validation (digital signature check, etc.)
        
        self.log("Installer validation passed")
    
    def run_full_build(self) -> Path:
        """Execute the complete installer build process"""
        try:
            self.validate_prerequisites()
            self.prepare_installer_build()
            installer_path = self.build_installer()
            self.validate_installer(installer_path)
            
            self.log("=" * 50)
            self.log("INSTALLER BUILD COMPLETED!")
            self.log("=" * 50)
            self.log(f"Installer: {installer_path}")
            self.log("=" * 50)
            
            return installer_path
            
        except InstallerBuildError as e:
            self.log(f"Installer build failed: {e}", "ERROR")
            sys.exit(1)
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
            sys.exit(1)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Windows installer for AI Input Method Tool")
    parser.add_argument("--validate-only", action="store_true", help="Only validate prerequisites")
    
    args = parser.parse_args()
    
    builder = InstallerBuilder()
    
    if args.validate_only:
        try:
            builder.validate_prerequisites()
            print("Installer prerequisites validation passed")
        except InstallerBuildError as e:
            print(f"Validation failed: {e}")
            sys.exit(1)
        return
    
    builder.run_full_build()

if __name__ == "__main__":
    main()