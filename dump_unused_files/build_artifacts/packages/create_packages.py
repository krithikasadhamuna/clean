#!/usr/bin/env python3
"""
Create ZIP packages for CodeGrey AI SOC Platform client agents
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_zip_package(source_dir: str, output_file: str):
    """Create a ZIP package from source directory"""
    print(f"Creating {output_file}...")
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        source_path = Path(source_dir)
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                # Calculate relative path
                relative_path = file_path.relative_to(source_path)
                zipf.write(file_path, relative_path)
                print(f"  Added: {relative_path}")
    
    print(f"Created: {output_file}")
    print(f"   Size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
    print()

def main():
    """Create all client agent packages"""
    print("CodeGrey AI SOC Platform - Package Creator")
    print("=" * 50)
    print()
    
    # Create output directory
    output_dir = Path("client-agent-packages")
    output_dir.mkdir(exist_ok=True)
    
    # Package definitions
    packages = [
        {
            'name': 'Windows Client Agent',
            'source': 'windows/codegrey-agent-windows-v2',
            'output': output_dir / 'codegrey-agent-windows-v2.zip'
        },
        {
            'name': 'Linux Client Agent',
            'source': 'linux/codegrey-agent-linux',
            'output': output_dir / 'codegrey-agent-linux-v2.zip'
        },
        {
            'name': 'macOS Client Agent',
            'source': 'macos/codegrey-agent-macos',
            'output': output_dir / 'codegrey-agent-macos-v2.zip'
        }
    ]
    
    # Create packages
    for package in packages:
        if Path(package['source']).exists():
            create_zip_package(package['source'], package['output'])
        else:
            print(f"ERROR: Source directory not found: {package['source']}")
    
    print("Package creation complete!")
    print(f"Packages created in: {output_dir.absolute()}")
    print()
    print("Upload these ZIP files to your software download API:")
    print("- codegrey-agent-windows-v2.zip -> Windows client package")
    print("- codegrey-agent-linux-v2.zip -> Linux client package") 
    print("- codegrey-agent-macos-v2.zip -> macOS client package")

if __name__ == "__main__":
    main()
