#!/usr/bin/env python3
"""
Build Windows Client Agent Executable and Run Comprehensive Tests
"""

import os
import sys
import subprocess
import shutil
import asyncio
from pathlib import Path

def build_windows_executable():
    """Build Windows executable using PyInstaller"""
    
    print("🔨 Building CodeGrey Agent Windows Executable")
    print("=" * 60)
    
    # Change to the Windows client directory
    client_dir = Path("build_artifacts/packages/windows/codegrey-agent-windows-v2")
    if not client_dir.exists():
        print(f" Client directory not found: {client_dir}")
        return False
    
    original_dir = Path.cwd()
    os.chdir(client_dir)
    
    try:
        # Install PyInstaller if not available
        print("1. Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        
        # Create spec file for advanced configuration
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        ('README.md', '.'),
        ('requirements.txt', '.'),
        ('core', 'core'),
        ('shared', 'shared')
    ],
    hiddenimports=[
        'win32evtlog',
        'win32evtlogutil', 
        'win32con',
        'win32service',
        'win32net',
        'winreg',
        'psutil',
        'requests',
        'aiohttp',
        'docker',
        'yaml',
        'asyncio',
        'logging',
        'json',
        'datetime',
        'pathlib',
        'typing',
        'network_discovery',
        'location_detector',
        'container_orchestrator',
        'config_manager',
        'core.client.client_agent',
        'core.client.command_executor',
        'core.client.container_attack_executor',
        'core.client.container_manager',
        'core.client.forwarders.windows_forwarder',
        'core.client.forwarders.application_forwarder',
        'core.client.forwarders.base_forwarder',
        'shared.config',
        'shared.models',
        'shared.utils'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='CodeGrey-Agent-Windows',
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
    version_file=None
)
'''
        
        # Write spec file
        with open('CodeGrey-Agent-Windows-Test.spec', 'w') as f:
            f.write(spec_content)
        
        print("2. Building executable...")
        print("   This may take several minutes...")
        
        # Build executable
        subprocess.run([
            'pyinstaller', 
            '--clean',
            '--noconfirm',
            'CodeGrey-Agent-Windows-Test.spec'
        ], check=True)
        
        # Check if executable was created
        exe_path = Path('dist/CodeGrey-Agent-Windows.exe')
        if exe_path.exists():
            print(f"3.  SUCCESS: Executable created!")
            print(f"   Location: {exe_path.absolute()}")
            print(f"   Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            
            # Create distribution folder
            dist_folder = Path('CodeGrey-Agent-Windows-Test-Package')
            if dist_folder.exists():
                shutil.rmtree(dist_folder)
            
            dist_folder.mkdir()
            
            # Copy executable and required files
            shutil.copy2(exe_path, dist_folder / 'CodeGrey-Agent-Windows.exe')
            shutil.copy2('config.yaml', dist_folder / 'config.yaml')
            shutil.copy2('README.md', dist_folder / 'README.md')
            
            # Create run script
            run_script = '''@echo off
echo CodeGrey AI SOC Platform - Windows Agent
echo ==========================================
echo.
echo Starting Windows endpoint agent...
echo Server: http://backend.codegrey.ai:8080
echo.
echo Press Ctrl+C to stop the agent
echo.

CodeGrey-Agent-Windows.exe

echo.
echo Agent stopped. Press any key to exit...
pause >nul
'''
            
            with open(dist_folder / 'Run-CodeGrey-Agent.bat', 'w') as f:
                f.write(run_script)
            
            # Create test script
            test_script = '''@echo off
echo CodeGrey AI SOC Platform - Capability Test
echo ==========================================
echo.
echo Testing all client agent capabilities...
echo.

CodeGrey-Agent-Windows.exe --test

echo.
echo Test completed. Press any key to exit...
pause >nul
'''
            
            with open(dist_folder / 'Test-CodeGrey-Agent.bat', 'w') as f:
                f.write(test_script)
            
            # Create configuration script
            config_script = '''@echo off
echo CodeGrey AI SOC Platform - Configuration
echo =========================================
echo.
echo Configure the agent with your server details...
echo.

CodeGrey-Agent-Windows.exe --configure

echo.
echo Configuration complete. Press any key to exit...
pause >nul
'''
            
            with open(dist_folder / 'Configure-CodeGrey-Agent.bat', 'w') as f:
                f.write(config_script)
            
            print(f"4. 📦 Distribution package created:")
            print(f"   Folder: {dist_folder.absolute()}")
            print(f"   Files:")
            for file in dist_folder.iterdir():
                print(f"     - {file.name}")
            
            return True, dist_folder
            
        else:
            print(" ERROR: Executable not found after build")
            return False, None
            
    except subprocess.CalledProcessError as e:
        print(f" Build failed: {e}")
        return False, None
    except Exception as e:
        print(f" Error: {e}")
        return False, None
    finally:
        os.chdir(original_dir)

async def run_capability_tests():
    """Run comprehensive capability tests"""
    print("\n Running Capability Tests...")
    print("=" * 60)
    
    try:
        # Import and run the test suite
        from test_windows_client_capabilities import WindowsClientCapabilityTester
        
        tester = WindowsClientCapabilityTester()
        results = await tester.run_all_tests()
        
        return results
        
    except Exception as e:
        print(f" Test execution failed: {e}")
        return None

def main():
    """Main build and test execution"""
    print(" CodeGrey AI SOC Platform - Windows Client Build & Test")
    print("=" * 70)
    print("Building executable and testing all capabilities...")
    print("=" * 70)
    
    # Step 1: Build executable
    build_success, dist_folder = build_windows_executable()
    
    if not build_success:
        print("\n Build failed. Cannot proceed with tests.")
        return
    
    # Step 2: Run capability tests
    print("\n" + "=" * 70)
    test_results = asyncio.run(run_capability_tests())
    
    # Step 3: Generate final report
    print("\n" + "=" * 70)
    print(" FINAL BUILD & TEST REPORT")
    print("=" * 70)
    
    if test_results:
        print(f"Overall Status: {test_results['overall_status'].upper()}")
        print(f"Docker Available: {test_results['summary']['docker_available']}")
        print(f"Server Reachable: {test_results['summary']['server_reachable']}")
        print(f"Failed Tests: {test_results['summary']['failed_tests']}")
        print(f"Partial Tests: {test_results['summary']['partial_tests']}")
        
        # Save test results to distribution folder
        if dist_folder:
            import json
            results_file = dist_folder / 'test_results.json'
            with open(results_file, 'w') as f:
                json.dump(test_results, f, indent=2, default=str)
            print(f"\n📄 Test results saved to: {results_file}")
        
        # Recommendations
        print("\n RECOMMENDATIONS:")
        
        if not test_results['summary']['docker_available']:
            print("- WARNING: Docker not available - Container capabilities limited")
            print("-  Client will still work for log forwarding and command execution")
            print("- 💡 Consider installing Docker for full container-based attack simulation")
        
        if not test_results['summary']['server_reachable']:
            print("-  Server not reachable - Check network connectivity")
            print("-  Verify server endpoint: http://backend.codegrey.ai:8080")
        
        if test_results['overall_status'] in ['excellent', 'good']:
            print("-  Client agent is ready for deployment!")
            print("-  All core capabilities are working")
        elif test_results['overall_status'] == 'acceptable':
            print("- WARNING: Client agent has some limitations but is functional")
            print("- 🔍 Review failed tests and consider fixes")
        else:
            print("-  Client agent has significant issues")
            print("-  Review and fix failed tests before deployment")
    
    print(f"\n📦 Distribution Package: {dist_folder}")
    print("📁 Files included:")
    if dist_folder:
        for file in dist_folder.iterdir():
            print(f"   - {file.name}")
    
    print("\n" + "=" * 70)
    print("🎉 BUILD & TEST COMPLETE!")
    print("=" * 70)
    
    if test_results and test_results['overall_status'] in ['excellent', 'good', 'acceptable']:
        print(" Windows client agent is ready for deployment!")
        print(" You can now distribute the package to Windows endpoints")
    else:
        print("WARNING: Review the test results and fix any issues before deployment")

if __name__ == "__main__":
    main()

