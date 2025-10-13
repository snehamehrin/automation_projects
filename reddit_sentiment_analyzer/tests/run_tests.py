"""
Test runner script for all tests
"""

import sys
import subprocess
import os
from pathlib import Path


def run_tests():
    """Run all tests with pytest"""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Change to project root
    os.chdir(project_root)
    
    # Add project root to Python path
    sys.path.insert(0, str(project_root))
    
    print("🧪 Running Brand Reddit Analysis Tool Tests")
    print("=" * 50)
    
    # Run unit tests
    print("\n📋 Running Unit Tests...")
    unit_result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/unit/", 
        "-v", 
        "--tb=short",
        "--color=yes"
    ], capture_output=False)
    
    # Run integration tests
    print("\n🔗 Running Integration Tests...")
    integration_result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/integration/", 
        "-v", 
        "--tb=short",
        "--color=yes"
    ], capture_output=False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    if unit_result.returncode == 0:
        print("✅ Unit Tests: PASSED")
    else:
        print("❌ Unit Tests: FAILED")
    
    if integration_result.returncode == 0:
        print("✅ Integration Tests: PASSED")
    else:
        print("❌ Integration Tests: FAILED")
    
    if unit_result.returncode == 0 and integration_result.returncode == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1


def run_specific_test(test_path):
    """Run a specific test file"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    
    print(f"🧪 Running specific test: {test_path}")
    print("=" * 50)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        test_path, 
        "-v", 
        "--tb=short",
        "--color=yes"
    ], capture_output=False)
    
    return result.returncode


def run_coverage():
    """Run tests with coverage report"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    
    print("📊 Running tests with coverage...")
    print("=" * 50)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "--cov=modules",
        "--cov=database",
        "--cov=config",
        "--cov=utils",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ], capture_output=False)
    
    print("\n📈 Coverage report generated in htmlcov/index.html")
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "coverage":
            exit_code = run_coverage()
        elif command == "unit":
            exit_code = run_specific_test("tests/unit/")
        elif command == "integration":
            exit_code = run_specific_test("tests/integration/")
        elif command.startswith("test_"):
            exit_code = run_specific_test(f"tests/unit/{command}")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: coverage, unit, integration, or specific test file")
            exit_code = 1
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)

