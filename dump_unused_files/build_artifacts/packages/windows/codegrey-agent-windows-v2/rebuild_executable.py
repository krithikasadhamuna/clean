#!/usr/bin/env python3
"""
Rebuild Windows executable with correct client agent code
"""

import os
import sys
import subprocess
from pathlib import Path

def rebuild_executable():
    """Rebuild the Windows executable"""
    print("CodeGrey AI SOC Platform - Rebuilding Windows Executable")
    print("=" * 60)
    
    # Get current directory
    current_dir = Path(__file__).parent
    
    # PyInstaller spec content
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[r'{current_dir}'],
    binaries=[],
    datas=[
        ('core', 'core'),
        ('shared', 'shared'),
        ('config.yaml', '.'),
        ('client_config.yaml', '.'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
        ('config_manager.py', '.'),
        ('network_discovery.py', '.'),
        ('location_detector.py', '.'),
        ('container_orchestrator.py', '.'),
    ],
    hiddenimports=[
        'aiohttp',
        'asyncio',
        'yaml',
        'json',
        'logging',
        'pathlib',
        'subprocess',
        'platform',
        'uuid',
        'datetime',
        'typing',
        'ctypes',
        'wmi',
        'win32evtlog',
        'win32api',
        'win32con',
        'win32security',
        'win32service',
        'win32serviceutil',
        'pywintypes',
        'psutil',
        'requests',
        'cryptography',
        'docker',
        'core.client.client_agent',
        'core.client.command_executor',
        'core.client.container_attack_executor',
        'core.client.container_manager',
        'core.client.forwarders.windows_forwarder',
        'core.client.forwarders.linux_forwarder',
        'core.client.forwarders.application_forwarder',
        'core.client.forwarders.ebpf_forwarder',
        'core.client.forwarders.base_forwarder',
        'shared.config',
        'shared.models',
        'shared.utils',
        'config_manager',
        'network_discovery',
        'location_detector',
        'container_orchestrator',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
        'jupyter',
        'notebook',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CodeGrey-Agent-Windows-Final-Fixed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    # Write spec file
    spec_file = current_dir / "CodeGrey-Agent-Windows-Final-Fixed.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"Created spec file: {spec_file}")
    
    # Clean previous build
    print("Cleaning previous build...")
    if (current_dir / "build").exists():
        import shutil
        shutil.rmtree(current_dir / "build")
    if (current_dir / "dist").exists():
        import shutil
        shutil.rmtree(current_dir / "dist")
    
    # Build executable
    print("Building executable with PyInstaller...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ], cwd=current_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("SUCCESS: Executable built successfully!")
            print(f"Location: {current_dir / 'dist' / 'CodeGrey-Agent-Windows-Final-Fixed.exe'}")
            
            # Check file size
            exe_path = current_dir / "dist" / "CodeGrey-Agent-Windows-Final-Fixed.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"Size: {size_mb:.1f} MB")
            
            return True
        else:
            print("ERROR: Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"ERROR: Build error: {e}")
        return False

if __name__ == "__main__":
    success = rebuild_executable()
    if success:
        print("\nSUCCESS: Executable rebuild completed successfully!")
        print("The new executable should now use the correct LogForwardingClient code.")
    else:
        print("\nERROR: Executable rebuild failed!")
        sys.exit(1)
