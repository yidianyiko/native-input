#!/usr/bin/env python3
"""
Build Automation Script for AI Input Method Tool
Creates Windows executable using PyInstaller with comprehensive validation
"""

import os
import sys
import shutil
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
BUILD_PATH = PROJECT_ROOT / "build"
DIST_PATH = PROJECT_ROOT / "dist"
SPEC_FILE = PROJECT_ROOT / "reInput.spec"

class BuildError(Exception):
    """Custom exception for build errors"""
    pass

class BuildAutomation:
    """Handles the complete build process for the AI Input Method Tool"""
    
    def __init__(self, debug: bool = False, clean: bool = True):
        self.debug = debug
        self.clean = clean
        self.build_info = {}
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO") -> None:
        """Log build messages with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = "[INFO]" if level == "INFO" else "[WARN]" if level == "WARN" else "[ERROR]"
        print(f"[{timestamp}] {prefix} {message}")
        
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Execute command and return exit code, stdout, stderr"""
        self.log(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid characters instead of failing
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                self.log(f"Command failed with exit code {result.returncode}", "ERROR")
                if result.stderr:
                    self.log(f"Error output: {result.stderr}", "ERROR")
                    
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            raise BuildError("Command timed out after 5 minutes")
        except Exception as e:
            raise BuildError(f"Failed to execute command: {e}")
    
    def validate_environment(self) -> None:
        """Validate basic build environment"""
        self.log("Validating build environment...")
        
        # Check Python version
        if sys.version_info < (3, 10):
            raise BuildError("Python 3.10+ required")
            
        # Check main entry point exists
        if not (SRC_PATH / "main.py").exists():
            raise BuildError(f"Main entry point missing: {SRC_PATH / 'main.py'}")
                
        # Check PyInstaller installation
        try:
            import PyInstaller
        except ImportError:
            raise BuildError("PyInstaller not installed. Run: uv add --dev pyinstaller")
            
        self.log("Environment validation passed") 
   
    def clean_build_directories(self) -> None:
        """Clean previous build artifacts"""
        if not self.clean:
            return
            
        self.log("Cleaning build directories...")
        
        directories_to_clean = [
            DIST_PATH,
            BUILD_PATH / "pyinstaller" / "build",
            BUILD_PATH / "pyinstaller" / "dist"
        ]
        
        for dir_path in directories_to_clean:
            if dir_path.exists():
                self.log(f"Removing {dir_path}")
                shutil.rmtree(dir_path)
                
        self.log("Build directories cleaned")
    
    def generate_version_info(self) -> None:
        """Generate Windows version info file"""
        self.log("Generating version info...")
        
        # Read version from pyproject.toml
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            import tomli as tomllib  # Fallback for older Python versions
            
        with open(PROJECT_ROOT / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
            
        version = pyproject["project"]["version"]
        name = pyproject["project"]["name"]
        description = pyproject["project"]["description"]
        
        # Parse version (e.g., "0.1.0" -> (0, 1, 0, 0))
        version_parts = version.split(".")
        while len(version_parts) < 4:
            version_parts.append("0")
        version_tuple = tuple(map(int, version_parts))
        
        version_info_content = f'''# UTF-8
#
# Version information for AI Input Method Tool
#

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'AI Input Method Team'),
            StringStruct(u'FileDescription', u'{description}'),
            StringStruct(u'FileVersion', u'{version}'),
            StringStruct(u'InternalName', u'{name}'),
            StringStruct(u'LegalCopyright', u'Copyright © 2025 AI Input Method Team'),
            StringStruct(u'OriginalFilename', u'ai-input-method.exe'),
            StringStruct(u'ProductName', u'AI Input Method Tool'),
            StringStruct(u'ProductVersion', u'{version}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
        
        version_file = BUILD_PATH / "version_info.txt"
        version_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(version_file, "w", encoding="utf-8") as f:
            f.write(version_info_content)
            
        self.build_info["version"] = version
        self.log(f"Version info generated: {version}")
    
    def validate_dependencies(self) -> None:
        """Basic dependency check"""
        self.log("Checking core dependencies...")
        
        # Only check critical dependencies that would cause immediate build failure
        critical_modules = ["PyInstaller", "PySide6"]
        
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError:
                raise BuildError(f"Critical dependency missing: {module}")
                
        self.log("Core dependencies check passed")
    
    def build_executable(self) -> None:
        """Run PyInstaller to build the executable"""
        self.log("Building executable with PyInstaller...")
        
        # Ensure spec file exists
        if not SPEC_FILE.exists():
            raise BuildError(f"PyInstaller spec file not found: {SPEC_FILE}")
            
        # Build command
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(SPEC_FILE)
        ]
        
        if self.debug:
            cmd.extend(["--debug", "all"])
            
        # Run PyInstaller
        exit_code, stdout, stderr = self.run_command(cmd)
        
        if exit_code != 0:
            raise BuildError(f"PyInstaller failed: {stderr}")
            
        self.log("Executable build completed")
    
    def validate_executable(self) -> None:
        """Basic executable validation"""
        self.log("Validating built executable...")
        
        exe_path = DIST_PATH / "reInput.exe"
        
        if not exe_path.exists():
            raise BuildError(f"Executable not found: {exe_path}")
            
        # Basic file size check
        file_size = exe_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        self.log(f"Executable size: {size_mb:.1f} MB")
        
        self.build_info["executable_size_mb"] = round(size_mb, 1)
        self.build_info["executable_path"] = str(exe_path)
        
        self.log("Executable validation completed")
    
    def copy_config_files(self) -> None:
        """Copy configuration files to exe directory"""
        self.log("Copying configuration files to exe directory...")
        
        exe_dir = DIST_PATH
        config_files = [
            PROJECT_ROOT / "settings.toml",
            PROJECT_ROOT / "settings.toml.example",
            PROJECT_ROOT / ".env.example"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                dest_file = exe_dir / config_file.name
                try:
                    import shutil
                    shutil.copy2(config_file, dest_file)
                    self.log(f"Copied {config_file.name} to exe directory")
                except Exception as e:
                    self.log(f"Failed to copy {config_file.name}: {e}", "ERROR")
            else:
                self.log(f"Config file not found: {config_file}", "WARN")
        
        self.log("Configuration files copy completed")  
  
    def generate_build_report(self) -> None:
        """Generate comprehensive build report"""
        build_time = time.time() - self.start_time
        
        self.build_info.update({
            "build_time_seconds": round(build_time, 2),
            "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": sys.version,
            "platform": sys.platform,
            "debug_build": self.debug
        })
        
        # Save build report
        report_file = BUILD_PATH / "build_report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.build_info, f, indent=2, ensure_ascii=False)
            
        # Print summary
        self.log("=" * 50)
        self.log("BUILD COMPLETED SUCCESSFULLY!")
        self.log("=" * 50)
        self.log(f"Version: {self.build_info.get('version', 'Unknown')}")
        self.log(f"Executable: {self.build_info.get('executable_path', 'Unknown')}")
        self.log(f"Size: {self.build_info.get('executable_size_mb', 'Unknown')} MB")
        self.log(f"Build time: {build_time:.1f} seconds")
        self.log(f"Report saved: {report_file}")
        self.log("=" * 50)
    
    def run_full_build(self) -> None:
        """Execute the simplified build process"""
        try:
            self.log("Starting AI Input Method Tool build process...")
            
            # Simplified build steps
            self.validate_environment()
            self.clean_build_directories()
            self.generate_version_info()
            self.build_executable()
            self.validate_executable()
            self.generate_build_report()
            
        except BuildError as e:
            self.log(f"Build failed: {e}", "ERROR")
            sys.exit(1)
        except KeyboardInterrupt:
            self.log("Build cancelled by user", "WARN")
            sys.exit(1)
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
            sys.exit(1)

def main():
    """Main entry point for build script"""
    parser = argparse.ArgumentParser(description="Build AI Input Method Tool executable")
    parser.add_argument("--debug", action="store_true", help="Enable debug build")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning build directories")
    parser.add_argument("--validate-only", action="store_true", help="Only validate environment")
    
    args = parser.parse_args()
    
    if args.validate_only:
        builder = BuildAutomation()
        try:
            builder.validate_environment()
            print("Environment validation passed")
        except BuildError as e:
            print(f"Validation failed: {e}")
            sys.exit(1)
        return
    
    # Run full build
    builder = BuildAutomation(
        debug=args.debug,
        clean=not args.no_clean
    )
    builder.run_full_build()

if __name__ == "__main__":
    main()