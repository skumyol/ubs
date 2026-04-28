#!/usr/bin/env python3
"""Run all tests with coverage reporting.

Usage:
    python run_tests.py           # Run all tests with coverage
    python run_tests.py --html    # Generate HTML coverage report
    python run_tests.py --xml     # Generate XML coverage report
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run pytest with coverage."""
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Base pytest command
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback
        "--cov=src",  # Coverage for src module
        "--cov-report=term-missing",  # Terminal report with missing lines
        "--cov-report=term:skip-covered",  # Summary only, skip 100% files
    ]

    # Check for additional report types
    if "--html" in sys.argv:
        cmd.append("--cov-report=html:htmlcov")
        print("Will generate HTML report at htmlcov/index.html")

    if "--xml" in sys.argv:
        cmd.append("--cov-report=xml")
        print("Will generate XML report at coverage.xml")

    # Add coverage target
    if "--fail-under" not in sys.argv:
        cmd.append("--cov-fail-under=90")

    # Run tests
    print("=" * 70)
    print("Running UBS Research Pipeline Tests")
    print("=" * 70)
    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=project_root)

    print()
    print("=" * 70)
    if result.returncode == 0:
        print("All tests passed with >=90% coverage!")
    else:
        print("Tests failed or coverage below 90%")
    print("=" * 70)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
