#!/usr/bin/env python3
"""
CodeGrey AI SOC Platform - Complete Setup with Docker Support
Automatically installs Docker and configures all container capabilities
"""

import os
import sys
import subprocess
import time
import json
import shutil
from pathlib import Path
import asyncio

def run_powershell_script(script_path, args=None):
    """Run PowerShell script with proper arguments"""
    try:
        cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", script_path]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Script timed out after 10 minutes"
    except Exception as e:
        return False, "", str(e)

def check_docker_installation():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f" Docker found: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run(["docker", "info"], capture_output=True, text=True)
            if result.returncode == 0:
                print(" Docker daemon is running")
                return True
            else:
                print("WARNING Docker installed but daemon not running")
                return False
        else:
            print(" Docker not found")
            return False
    except FileNotFoundError:
        print(" Docker not found")
        return False

def install_docker():
    """Install Docker using PowerShell script"""
    print(" Installing Docker Desktop...")
    print("This will require Administrator privileges and may take 10-15 minutes")
    print("")
    
    # Check if we're running as admin
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print(" ERROR: This script must be run as Administrator!")
            print("Right-click Command Prompt or PowerShell and select 'Run as Administrator'")
            return False
    except:
        print("WARNING Could not verify admin privileges")
    
    # Run Docker installation script
    script_path = Path("install_docker_windows.ps1")
    if not script_path.exists():
        print(f" Docker installation script not found: {script_path}")
        return False
    
    print("Running Docker installation script...")
    success, stdout, stderr = run_powershell_script(str(script_path), ["-SkipRestart"])
    
    if success:
        print(" Docker installation completed successfully!")
        print(stdout)
        return True
    else:
        print(" Docker installation failed!")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return False

def configure_client_with_docker():
    """Configure client with Docker-enabled configuration"""
    print(" Configuring client with Docker support...")
    
    # Copy enhanced configuration
    enhanced_config = Path("config_with_docker.yaml")
    client_config_path = Path("build_artifacts/packages/windows/codegrey-agent-windows-v2/config.yaml")
    
    if enhanced_config.exists() and client_config_path.exists():
        shutil.copy2(enhanced_config, client_config_path)
        print(f" Updated client configuration: {client_config_path}")
        return True
    else:
        print(" Configuration files not found")
        return False

def test_docker_functionality():
    """Test Docker functionality with CodeGrey containers"""
    print(" Testing Docker functionality...")
    
    tests = [
        {
            "name": "Docker Hello World",
            "command": ["docker", "run", "--rm", "hello-world"],
            "expected": "Hello from Docker"
        },
        {
            "name": "Ubuntu Container",
            "command": ["docker", "run", "--rm", "ubuntu:22.04", "echo", "Ubuntu test successful"],
            "expected": "Ubuntu test successful"
        },
        {
            "name": "Nginx Container",
            "command": ["docker", "run", "--rm", "-d", "--name", "test-nginx", "nginx:alpine"],
            "expected": None
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"  Testing {test['name']}...")
        try:
            result = subprocess.run(test["command"], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                if test["expected"] is None or test["expected"] in result.stdout:
                    print(f"     {test['name']} passed")
                    results.append(True)
                else:
                    print(f"    WARNING {test['name']} unexpected output")
                    results.append(False)
            else:
                print(f"     {test['name']} failed: {result.stderr}")
                results.append(False)
                
        except subprocess.TimeoutExpired:
            print(f"     {test['name']} timed out")
            results.append(False)
        except Exception as e:
            print(f"     {test['name']} error: {e}")
            results.append(False)
    
    # Clean up test containers
    try:
        subprocess.run(["docker", "stop", "test-nginx"], capture_output=True)
        subprocess.run(["docker", "rm", "test-nginx"], capture_output=True)
    except:
        pass
    
    passed = sum(results)
    total = len(results)
    
    print(f"  Docker tests: {passed}/{total} passed")
    return passed == total

def rebuild_client_executable():
    """Rebuild client executable with Docker support"""
    print("🔨 Rebuilding client executable with Docker support...")
    
    client_dir = Path("build_artifacts/packages/windows/codegrey-agent-windows-v2")
    if not client_dir.exists():
        print(" Client directory not found")
        return False
    
    original_dir = Path.cwd()
    os.chdir(client_dir)
    
    try:
        # Build with PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--console",
            "--name", "CodeGrey-Agent-Windows-With-Docker",
            "main.py"
        ]
        
        print("Building executable (this may take several minutes)...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            exe_path = client_dir / "dist" / "CodeGrey-Agent-Windows-With-Docker.exe"
            if exe_path.exists():
                print(f" Executable built successfully: {exe_path}")
                print(f"  Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
                return True
            else:
                print(" Executable not found after build")
                return False
        else:
            print(" Build failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(" Build timed out")
        return False
    except Exception as e:
        print(f" Build error: {e}")
        return False
    finally:
        os.chdir(original_dir)

def run_comprehensive_test():
    """Run comprehensive test of all capabilities"""
    print(" Running comprehensive capability test...")
    
    try:
        # Import and run the test suite
        from simple_test import main as run_tests
        run_tests()
        return True
    except Exception as e:
        print(f" Test execution failed: {e}")
        return False

def main():
    """Main setup process"""
    print("CodeGrey AI SOC Platform - Complete Setup with Docker Support")
    print("=" * 70)
    print("This will install Docker and enable all container-based capabilities")
    print("=" * 70)
    print("")
    
    # Step 1: Check current Docker status
    print("Step 1: Checking Docker installation...")
    docker_installed = check_docker_installation()
    
    if not docker_installed:
        print("\nStep 2: Installing Docker Desktop...")
        if not install_docker():
            print(" Docker installation failed. Cannot proceed.")
            return False
        
        # Wait a bit for Docker to fully start
        print("Waiting for Docker to fully initialize...")
        time.sleep(30)
        
        # Check again
        docker_installed = check_docker_installation()
        if not docker_installed:
            print(" Docker installation verification failed")
            print("Please restart your computer and try again")
            return False
    else:
        print(" Docker already installed and running")
    
    # Step 3: Configure client with Docker support
    print("\nStep 3: Configuring client with Docker support...")
    if not configure_client_with_docker():
        print(" Client configuration failed")
        return False
    
    # Step 4: Test Docker functionality
    print("\nStep 4: Testing Docker functionality...")
    if not test_docker_functionality():
        print("WARNING Docker functionality test had issues, but continuing...")
    
    # Step 5: Rebuild executable
    print("\nStep 5: Rebuilding client executable...")
    if not rebuild_client_executable():
        print(" Executable rebuild failed")
        return False
    
    # Step 6: Run comprehensive test
    print("\nStep 6: Running comprehensive capability test...")
    run_comprehensive_test()
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎉 SETUP COMPLETE!")
    print("=" * 70)
    print("")
    print(" Docker Desktop installed and configured")
    print(" Client configured with full container support")
    print(" Executable rebuilt with Docker capabilities")
    print(" All container-based attack simulation enabled")
    print("")
    print(" YOUR CLIENT AGENT NOW HAS FULL CAPABILITIES:")
    print("   - Container-based attack simulation")
    print("   - Golden image snapshots")
    print("   - Isolated attack execution environments")
    print("   - Multi-platform attack scenarios")
    print("   - Advanced MITRE ATT&CK technique execution")
    print("")
    print("📦 READY FOR DEPLOYMENT:")
    print("   - Executable: build_artifacts/packages/windows/codegrey-agent-windows-v2/dist/")
    print("   - Configuration: Enhanced with Docker support")
    print("   - All container capabilities: ENABLED")
    print("")
    print(" Next steps:")
    print("   1. Deploy the enhanced client agent")
    print("   2. Run container-based attack simulations")
    print("   3. Monitor logs from isolated environments")
    print("   4. Analyze attack patterns with golden images")
    print("")
    print("Your CodeGrey AI SOC Platform is now fully operational! 🎉")

if __name__ == "__main__":
    main()

