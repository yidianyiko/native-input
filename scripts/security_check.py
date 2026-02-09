#!/usr/bin/env python3
"""
Security check script to validate no sensitive data is included in builds
Run this before any build or deployment process
"""

import re
from pathlib import Path
from typing import List, Tuple

def scan_for_secrets(file_path: Path) -> List[Tuple[int, str]]:
    """Scan a file for potential secrets and return line numbers and content"""
    secrets_found = []
    
    # Common secret patterns
    patterns = [
        (r'sk-[a-zA-Z0-9]{48,}', 'OpenAI API Key'),
        (r'password\s*=\s*["\'][^"\']["\']', 'Hardcoded Password'),
        (r'secret\s*=\s*["\'][^"\']["\']', 'Hardcoded Secret'),
        (r'token\s*=\s*["\'][^"\']["\']', 'Hardcoded Token'),
        (r'-----BEGIN.*PRIVATE KEY-----', 'Private Key'),
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                for pattern, description in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        secrets_found.append((line_num, f"{description}: {line.strip()}"))
    except (UnicodeDecodeError, PermissionError):
        pass  # Skip binary or inaccessible files
    
    return secrets_found

def check_build_security():
    """Check for security issues before building"""
    print("Running security scan before build...")
    
    # Files to scan
    scan_paths = [
        Path("src"),
        Path("build_config.py"),
        Path(".env") if Path(".env").exists() else None,
        Path("config.json") if Path("config.json").exists() else None,
    ]
    
    issues_found = False
    
    for path in scan_paths:
        if path is None:
            continue
            
        if path.is_file():
            secrets = scan_for_secrets(path)
            if secrets:
                print(f"WARNING: Secrets found in {path}:")
                for line_num, content in secrets:
                    print(f"   Line {line_num}: {content}")
                issues_found = True
        elif path.is_dir():
            for file_path in path.rglob("*.py"):
                secrets = scan_for_secrets(file_path)
                if secrets:
                    print(f"WARNING: Secrets found in {file_path}:")
                    for line_num, content in secrets:
                        print(f"   Line {line_num}: {content}")
                    issues_found = True
    
    if issues_found:
        print("\nSecurity issues detected! Please remove hardcoded secrets before building.")
        print("Use environment variables or secure configuration files instead.")
        return False
    else:
        print("No security issues detected.")
        return True

if __name__ == "__main__":
    import sys
    success = check_build_security()
    sys.exit(0 if success else 1)