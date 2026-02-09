#!/usr/bin/env python3
"""
Voice Service Test Runner
Quick automated testing for voice functionality without manual interaction
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run voice service tests"""
    print("Running Voice Service Tests")
    print("=" * 50)
    
    # Run the simple voice tests
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/test_voice_simple.py", 
        "-v", 
        "--tb=short"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("\nAll voice tests PASSED!")
        print("\nVoice service is working correctly!")
        print("\nNext time you want to test voice functionality:")
        print("  python scripts/run_voice_tests.py")
        return True
    else:
        print(f"\nSome tests FAILED (exit code: {result.returncode})")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)