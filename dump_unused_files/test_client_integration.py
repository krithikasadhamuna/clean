"""
Test Client Package AI Attack Integration
Tests that all new capabilities are properly integrated
"""

import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Test imports
def test_imports():
    """Test that all new modules can be imported"""
    print("\n=== Testing Module Imports ===\n")
    
    packages = [
        "CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-windows-unified",
        "CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-linux-unified",
        "CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-macos-unified"
    ]
    
    results = []
    
    for package_path in packages:
        print(f"\nTesting {package_path.split('/')[-1]}:")
        
        # Add to path
        sys.path.insert(0, package_path)
        
        try:
            # Test new module imports
            from self_replica_builder import SelfReplicaBuilder
            print("  ✅ SelfReplicaBuilder imported")
            
            from dynamic_container_builder import DynamicContainerBuilder
            print("  ✅ DynamicContainerBuilder imported")
            
            from attack_vector_executor import AttackVectorExecutor
            print("  ✅ AttackVectorExecutor imported")
            
            # Test updated modules
            from command_executor import CommandExecutionEngine
            print("  ✅ CommandExecutionEngine imported")
            
            # Check for new methods
            if hasattr(CommandExecutionEngine, '_create_self_replica'):
                print("  ✅ CommandExecutionEngine has _create_self_replica method")
            else:
                print("  ❌ CommandExecutionEngine missing _create_self_replica method")
                results.append(False)
            
            if hasattr(CommandExecutionEngine, '_deploy_infrastructure'):
                print("  ✅ CommandExecutionEngine has _deploy_infrastructure method")
            else:
                print("  ❌ CommandExecutionEngine missing _deploy_infrastructure method")
                results.append(False)
            
            if hasattr(CommandExecutionEngine, '_execute_attack_vector'):
                print("  ✅ CommandExecutionEngine has _execute_attack_vector method")
            else:
                print("  ❌ CommandExecutionEngine missing _execute_attack_vector method")
                results.append(False)
            
            results.append(True)
            
        except ImportError as e:
            print(f"  ❌ Import failed: {e}")
            results.append(False)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append(False)
        finally:
            # Remove from path
            sys.path.remove(package_path)
    
    return all(results)


def test_file_structure():
    """Test that all required files exist"""
    print("\n\n=== Testing File Structure ===\n")
    
    packages = {
        "Windows": "CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-windows-unified",
        "Linux": "CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-linux-unified",
        "macOS": "CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-macos-unified"
    }
    
    required_files = [
        "self_replica_builder.py",
        "dynamic_container_builder.py",
        "attack_vector_executor.py",
        "command_executor.py",
        "unified_client_agent.py"
    ]
    
    results = []
    
    for platform, package_path in packages.items():
        print(f"\n{platform} Package:")
        
        for filename in required_files:
            filepath = os.path.join(package_path, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  ✅ {filename} ({size:,} bytes)")
                results.append(True)
            else:
                print(f"  ❌ {filename} MISSING")
                results.append(False)
    
    return all(results)


def test_command_executor_source():
    """Test that command_executor.py contains new methods"""
    print("\n\n=== Testing Command Executor Source ===\n")
    
    packages = {
        "Windows": "CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-windows-unified",
        "Linux": "CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-linux-unified",
        "macOS": "CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-macos-unified"
    }
    
    required_methods = [
        "_initialize_ai_capabilities",
        "_create_self_replica",
        "_deploy_infrastructure",
        "_execute_attack_vector"
    ]
    
    required_techniques = [
        "create_self_replica",
        "deploy_smtp_container",
        "execute_phishing"
    ]
    
    results = []
    
    for platform, package_path in packages.items():
        print(f"\n{platform} Package:")
        
        filepath = os.path.join(package_path, "command_executor.py")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for new methods
            for method in required_methods:
                if f"def {method}" in content or f"async def {method}" in content:
                    print(f"  ✅ Method: {method}")
                    results.append(True)
                else:
                    print(f"  ❌ Method missing: {method}")
                    results.append(False)
            
            # Check for new command types
            for technique in required_techniques:
                if f"'{technique}'" in content or f'"{technique}"' in content:
                    print(f"  ✅ Technique: {technique}")
                    results.append(True)
                else:
                    print(f"  ❌ Technique missing: {technique}")
                    results.append(False)
            
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
            results.append(False)
    
    return all(results)


def main():
    """Run all tests"""
    print("=" * 80)
    print("CLIENT PACKAGE AI ATTACK INTEGRATION TEST")
    print("=" * 80)
    
    results = {
        "File Structure": test_file_structure(),
        "Source Code": test_command_executor_source(),
        "Module Imports": test_imports()
    }
    
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Integration is complete!")
    else:
        print("❌ SOME TESTS FAILED! Review the output above.")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

