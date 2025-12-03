#!/usr/bin/env python3
"""
Dependency check script for Docker build.
Verifies that critical Python packages are installed correctly.
Exit code 0 = all OK, exit code 1 = missing dependencies.
"""
import sys

errors = []

try:
    import psycopg2
    print(f"✓ psycopg2 {psycopg2.__version__}")
except ImportError as e:
    errors.append(f"psycopg2: {e}")

try:
    import argon2
    print(f"✓ argon2-cffi {argon2.__version__}")
except ImportError as e:
    errors.append(f"argon2-cffi: {e}")

try:
    from passlib.hash import argon2 as pa
    print("✓ passlib argon2 backend")
except Exception as e:
    errors.append(f"passlib argon2: {e}")

if errors:
    print("✗ Missing dependencies:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)

print("All required Python dependencies are available.")
