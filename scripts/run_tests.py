#!/usr/bin/env python3
"""
Test runner script for AI Input Method
Runs basic functionality tests after cleanup
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run basic tests"""
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    
    print("Running AI Input Method Basic Tests")
    print("=" * 50)
    print("Note: Comprehensive tests have been cleaned up.")
    print("Only basic functionality tests remain.")
    print("=" * 50)
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/",
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=False)
        
        if result.returncode == 0:
            print("\nAll basic tests passed!")
            print("The core functionality is working correctly.")
        else:
            print("\nSome tests failed.")
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)