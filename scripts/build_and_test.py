#!/usr/bin/env python3
"""
Complete Build and Test Script for AI Input Method Tool
Handles executable building, installer creation, and installation testing
"""

import os
import sys
import subprocess
import tempfile
import shutil
import time
from pathlib import Path
from typing import Optional
import argparse

# Import our build modules
sys.path.insert(0, str(Path(__file__).parent))
from build_executable import BuildAutomation
from build_installer import InstallerBuilder

PROJECT_ROOT = Path(__file__).parent.parent

class CompleteBuildProcess:
    """Manages the complete build and test process"""
    
    def __init__(self, debug: bool = False, skip_tests: bool = False):
        self.debug = debug
        self.skip_tests = skip_tests
        self.build_artifacts = {}
        
    def log(self, message: str, level: str = "INFO") -> None:
        """Log messages with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = "🚀" if level == "INFO" else "⚠️" if level == "WARN" else "❌"
        print(f"[{timestamp}] {prefix} {message}")
    
    def build_executable(self) -> None:
        """Build the Windows executable"""
        self.log("Step 1: Building Windows executable...")
        
        builder = BuildAutomation(debug=self.debug, clean=True)
        builder.run_full_build()
        
        # Store build info
        exe_path = PROJECT_ROOT / "dist" / "ai-input-method" / "ai-input-method.exe"
        if exe_path.exists():
            self.build_artifacts["executable"] = exe_path
            self.log(f"Executable built: {exe_path}")
        else:
            raise Exception("Executable build failed - file not found")
    
    def build_installer(self) -> None:
        """Build the Windows installer"""
        self.log("Step 2: Building Windows installer...")
        
        installer_builder = InstallerBuilder()
        installer_path = installer_builder.run_full_build()
        
        self.build_artifacts["installer"] = installer_path
        self.log(f"Installer built: {installer_path}")
    
    def test_installation(self) -> None:
        """Test the installation and uninstallation process"""
        if self.skip_tests:
            self.log("Skipping installation tests")
            return
            
        self.log("Step 3: Testing installation process...")
        
        installer_path = self.build_artifacts.get("installer")
        if not installer_path:
            raise Exception("No installer found to test")
        
        # Create a test installation directory
        test_install_dir = Path(tempfile.mkdtemp(prefix="ai_input_test_"))
        
        try:
            # Test silent installation
            self.log(f"Testing silent installation to: {test_install_dir}")
            
            install_cmd = [
                str(installer_path),
                "/S",  # Silent install
                f"/D={test_install_dir}"
            ]
            
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                self.log(f"Installation test failed: {result.stderr}", "ERROR")
                return
            
            # Verify installation
            expected_exe = test_install_dir / "ai-input-method.exe"
            if expected_exe.exists():
                self.log("Installation test passed ✅")
                
                # Test uninstallation
                uninstaller = test_install_dir / "uninstall.exe"
                if uninstaller.exists():
                    self.log("Testing uninstallation...")
                    
                    uninstall_cmd = [str(uninstaller), "/S"]
                    result = subprocess.run(
                        uninstall_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        self.log("Uninstallation test passed ✅")
                    else:
                        self.log("Uninstallation test failed", "WARN")
                else:
                    self.log("Uninstaller not found", "WARN")
            else:
                self.log("Installation verification failed - executable not found", "ERROR")
                
        except subprocess.TimeoutExpired:
            self.log("Installation test timed out", "ERROR")
        except Exception as e:
            self.log(f"Installation test error: {e}", "ERROR")
        finally:
            # Cleanup test directory
            if test_install_dir.exists():
                try:
                    shutil.rmtree(test_install_dir)
                except:
                    self.log(f"Could not cleanup test directory: {test_install_dir}", "WARN")
    
    def generate_release_package(self) -> None:
        """Create a complete release package"""
        self.log("Step 4: Creating release package...")
        
        release_dir = PROJECT_ROOT / "dist" / "release"
        release_dir.mkdir(exist_ok=True)
        
        # Copy installer
        installer_path = self.build_artifacts.get("installer")
        if installer_path:
            release_installer = release_dir / installer_path.name
            shutil.copy2(installer_path, release_installer)
            self.log(f"Release installer: {release_installer}")
        
        # Copy portable executable
        exe_path = self.build_artifacts.get("executable")
        if exe_path and exe_path.parent.exists():
            portable_dir = release_dir / "portable"
            if portable_dir.exists():
                shutil.rmtree(portable_dir)
            shutil.copytree(exe_path.parent, portable_dir)
            self.log(f"Portable version: {portable_dir}")
        
        # Create release notes
        release_notes = release_dir / "RELEASE_NOTES.txt"
        with open(release_notes, "w") as f:
            f.write("AI Input Method Tool - Release Package\n")
            f.write("=" * 40 + "\n\n")
            f.write("Contents:\n")
            f.write("- ai-input-method-installer-*.exe: Windows installer\n")
            f.write("- portable/: Portable version (no installation required)\n\n")
            f.write("System Requirements:\n")
            f.write("- Windows 10 or later (64-bit)\n")
            f.write("- .NET Framework 4.7.2 or later\n\n")
            f.write("Installation:\n")
            f.write("1. Run the installer as administrator\n")
            f.write("2. Follow the installation wizard\n")
            f.write("3. Launch from Start Menu or Desktop shortcut\n\n")
            f.write("Portable Usage:\n")
            f.write("1. Extract the portable folder\n")
            f.write("2. Run ai-input-method.exe directly\n")
            f.write("3. No installation required\n")
        
        self.log(f"Release package created: {release_dir}")
    
    def run_complete_build(self) -> None:
        """Execute the complete build and test process"""
        try:
            start_time = time.time()
            
            self.log("Starting complete build process for AI Input Method Tool...")
            self.log("=" * 60)
            
            # Build steps
            self.build_executable()
            self.build_installer()
            self.test_installation()
            self.generate_release_package()
            
            # Summary
            build_time = time.time() - start_time
            self.log("=" * 60)
            self.log("COMPLETE BUILD PROCESS FINISHED! 🎉")
            self.log("=" * 60)
            self.log(f"Total build time: {build_time:.1f} seconds")
            
            if self.build_artifacts.get("executable"):
                self.log(f"Executable: {self.build_artifacts['executable']}")
            if self.build_artifacts.get("installer"):
                self.log(f"Installer: {self.build_artifacts['installer']}")
            
            self.log(f"Release package: {PROJECT_ROOT / 'dist' / 'release'}")
            self.log("=" * 60)
            
        except Exception as e:
            self.log(f"Build process failed: {e}", "ERROR")
            sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Complete build and test process")
    parser.add_argument("--debug", action="store_true", help="Enable debug build")
    parser.add_argument("--skip-tests", action="store_true", help="Skip installation tests")
    parser.add_argument("--executable-only", action="store_true", help="Build executable only")
    parser.add_argument("--installer-only", action="store_true", help="Build installer only (requires existing executable)")
    
    args = parser.parse_args()
    
    if args.executable_only:
        builder = BuildAutomation(debug=args.debug, clean=True)
        builder.run_full_build()
        return
    
    if args.installer_only:
        installer_builder = InstallerBuilder()
        installer_builder.run_full_build()
        return
    
    # Run complete process
    process = CompleteBuildProcess(
        debug=args.debug,
        skip_tests=args.skip_tests
    )
    process.run_complete_build()

if __name__ == "__main__":
    main()