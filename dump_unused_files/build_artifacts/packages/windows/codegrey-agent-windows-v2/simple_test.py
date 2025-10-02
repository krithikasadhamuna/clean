#!/usr/bin/env python3
"""
Simple test executable
"""

import sys
import os
from pathlib import Path

def main():
    print("=== SIMPLE TEST EXECUTABLE ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {Path(__file__).parent}")
    print(f"Python executable: {sys.executable}")
    print("=== END TEST ===")

if __name__ == "__main__":
    main()
