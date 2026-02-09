"""
Build configuration for creating reInput.exe
Uses PyInstaller to package the Python application into a standalone executable

SECURITY NOTES:
- Only .env.example is included (template file)
- Actual .env, config.json, and other sensitive files are EXCLUDED
- Users must configure their own .env and config.json after installation
- No API keys or secrets should ever be embedded in the executable
"""

import PyInstaller.__main__
import sys
from pathlib import Path

def validate_security():
    """Validate that no sensitive files will be included in the build"""
    sensitive_files = ['.env', 'config.json', 'secrets.enc']
    found_sensitive = []
    
    for file in sensitive_files:
        if Path(file).exists():
            found_sensitive.append(file)
    
    if found_sensitive:
        print("WARNING: Sensitive files detected:")
        for file in found_sensitive:
            print(f"   - {file}")
        print("   These files will be EXCLUDED from the build for security.")
        print("   Only .env.example will be included as a template.")
    
    return True

def build_executable():
    """Build the executable using PyInstaller"""
    
    # Security validation first
    if not validate_security():
        return False
    
    # Run comprehensive security check
    print("Running security scan...")
    import subprocess
    try:
        result = subprocess.run([sys.executable, "scripts/security_check.py"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("Security check failed!")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
        else:
            print("Security check passed!")
    except Exception as e:
        print(f"Could not run security check: {e}")
        print("Proceeding with build, but manual security review recommended.")
    
    # Get the main script path
    main_script = Path("src/main.py").resolve()
    
    # PyInstaller arguments
    args = [
        str(main_script),
        '--name=reInput',  # Output executable name
        '--onefile',       # Create a single executable file
        '--console',       # Show console window for debugging
        # '--icon=assets/icon.ico',  # App icon (if exists)
        
        # Hidden imports (modules that PyInstaller might miss)
        '--hidden-import=win32event',
        '--hidden-import=win32api', 
        '--hidden-import=win32pipe',
        '--hidden-import=win32file',
        '--hidden-import=win32gui',
        '--hidden-import=win32con',
        '--hidden-import=pywintypes',
        '--hidden-import=winreg',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtGui',
        
        # Add ONLY safe template files (never actual config/secrets)
        '--add-data=.env.example;.',
        
        # Security: Explicitly exclude sensitive files
        '--exclude=.env',              # Exclude actual environment file
        '--exclude=config.json',       # Exclude user configuration
        '--exclude=*.key',             # Exclude private keys
        '--exclude=*.pem',             # Exclude certificates
        '--exclude=secrets.enc',       # Exclude encrypted secrets
        '--exclude=*.token',           # Exclude token files
        
        # Exclude unnecessary modules to reduce size
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=PIL',
        
        # Output directory
        '--distpath=dist',
        '--workpath=build',
        '--specpath=build',
        
        # Clean build
        '--clean',
        
        # Optimization
        '--optimize=2',
        
        # Version info (Windows)
        # '--version-file=version_info.txt',
    ]
    
    print("Building reInput.exe...")
    print(f"Main script: {main_script}")
    
    try:
        PyInstaller.__main__.run(args)
        print("Build completed successfully!")
        print("Executable location: dist/reInput.exe")
        
    except Exception as e:
        print(f"Build failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)