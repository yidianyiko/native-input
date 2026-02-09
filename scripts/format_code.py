#!/usr/bin/env python3
"""
Code formatting script using black and isort
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list, description: str) -> bool:
    """Run a command and return success status"""
    try:
        print(f"Running {description}...")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"  Command: {' '.join(command)}")
        print(f"  Error: {e.stderr}")
        return False


def main():
    """Format code using black and isort"""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    
    # Change to project root
    import os
    os.chdir(project_root)
    
    success = True
    
    # Run isort
    success &= run_command(
        ["python", "-m", "isort", str(src_path)],
        "import sorting (isort)"
    )
    
    # Run black
    success &= run_command(
        ["python", "-m", "black", str(src_path)],
        "code formatting (black)"
    )
    
    if success:
        print("\n✓ All formatting completed successfully!")
        return 0
    else:
        print("\n✗ Some formatting operations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())