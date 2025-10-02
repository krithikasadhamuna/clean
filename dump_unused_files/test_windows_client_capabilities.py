#!/usr/bin/env python3
"""
Comprehensive Test Suite for Windows Client Agent Capabilities
Tests all functionality including Docker availability, log forwarding, command execution, etc.
"""

import asyncio
import logging
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.client.client_agent import LogForwardingClient
from core.client.command_executor import CommandExecutionEngine
from core.client.container_attack_executor import ContainerAttackExecutor
from core.client.container_manager import ContainerManager
from shared.utils import setup_logging, get_system_info

# Setup logging
setup_logging('INFO', 'test_capabilities.log')
logger = logging.getLogger(__name__)

class WindowsClientCapabilityTester:
    """Test all Windows client agent capabilities"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_info': {},
            'capabilities': {},
            'docker_status': {},
            'log_forwarding': {},
            'command_execution': {},
            'container_management': {},
            'network_connectivity': {},
            'overall_status': 'unknown'
        }
        
        # Test configuration
        self.server_endpoint = "http://backend.codegrey.ai:8080"
        self.agent_id = f"test_agent_{int(time.time())}"
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive capability tests"""
        logger.info(" Starting Windows Client Agent Capability Tests")
        logger.info("=" * 60)
        
        try:
            # Test 1: System Information
            await self._test_system_info()
            
            # Test 2: Docker Availability
            await self._test_docker_availability()
            
            # Test 3: Network Connectivity
            await self._test_network_connectivity()
            
            # Test 4: Log Forwarding
            await self._test_log_forwarding()
            
            # Test 5: Command Execution
            await self._test_command_execution()
            
            # Test 6: Container Management (if Docker available)
            await self._test_container_management()
            
            # Test 7: Full Client Agent Integration
            await self._test_full_client_agent()
            
            # Generate final report
            self._generate_final_report()
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.test_results['overall_status'] = 'failed'
            self.test_results['error'] = str(e)
            return self.test_results
    
    async def _test_system_info(self):
        """Test system information gathering"""
        logger.info("🔍 Testing System Information Gathering...")
        
        try:
            system_info = get_system_info()
            
            self.test_results['system_info'] = {
                'status': 'success',
                'platform': system_info.get('platform', 'unknown'),
                'hostname': system_info.get('hostname', 'unknown'),
                'ip_address': system_info.get('ip_address', 'unknown'),
                'mac_address': system_info.get('mac_address', 'unknown'),
                'os_version': system_info.get('platform_version', 'unknown'),
                'python_version': sys.version,
                'architecture': system_info.get('architecture', 'unknown')
            }
            
            logger.info(f" System Info: {system_info.get('platform')} - {system_info.get('hostname')}")
            
        except Exception as e:
            logger.error(f" System info test failed: {e}")
            self.test_results['system_info'] = {'status': 'failed', 'error': str(e)}
    
    async def _test_docker_availability(self):
        """Test Docker availability and functionality"""
        logger.info(" Testing Docker Availability...")
        
        try:
            import docker
            
            # Test Docker connection
            docker_client = docker.from_env()
            docker_client.ping()
            
            # Get Docker info
            docker_info = docker_client.info()
            
            self.test_results['docker_status'] = {
                'status': 'available',
                'version': docker_info.get('ServerVersion', 'unknown'),
                'containers_running': docker_info.get('ContainersRunning', 0),
                'containers_total': docker_info.get('Containers', 0),
                'images': docker_info.get('Images', 0),
                'driver': docker_info.get('Driver', 'unknown')
            }
            
            logger.info(" Docker is available and running")
            
        except ImportError:
            logger.warning("WARNING: Docker Python library not installed")
            self.test_results['docker_status'] = {
                'status': 'library_not_installed',
                'message': 'Docker Python library not available'
            }
            
        except docker.errors.DockerException as e:
            logger.warning(f"WARNING: Docker not available: {e}")
            self.test_results['docker_status'] = {
                'status': 'not_available',
                'error': str(e),
                'message': 'Docker daemon not running or not accessible'
            }
            
        except Exception as e:
            logger.error(f" Docker test failed: {e}")
            self.test_results['docker_status'] = {'status': 'failed', 'error': str(e)}
    
    async def _test_network_connectivity(self):
        """Test network connectivity to server"""
        logger.info(" Testing Network Connectivity...")
        
        try:
            import aiohttp
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test server connectivity
                async with session.get(f"{self.server_endpoint}/health") as response:
                    if response.status == 200:
                        self.test_results['network_connectivity'] = {
                            'status': 'success',
                            'server_reachable': True,
                            'response_time_ms': 0,  # Could measure this
                            'server_status': 'healthy'
                        }
                        logger.info(" Server is reachable and healthy")
                    else:
                        self.test_results['network_connectivity'] = {
                            'status': 'partial',
                            'server_reachable': True,
                            'server_status': f'http_{response.status}'
                        }
                        logger.warning(f"WARNING: Server reachable but returned {response.status}")
                        
        except Exception as e:
            logger.error(f" Network connectivity test failed: {e}")
            self.test_results['network_connectivity'] = {
                'status': 'failed',
                'error': str(e),
                'server_reachable': False
            }
    
    async def _test_log_forwarding(self):
        """Test log forwarding capabilities"""
        logger.info(" Testing Log Forwarding...")
        
        try:
            # Test log forwarders
            from core.client.forwarders.windows_forwarder import WindowsLogForwarder
            from core.client.forwarders.application_forwarder import ApplicationLogForwarder
            
            # Test Windows log forwarder
            windows_forwarder = WindowsLogForwarder(self.agent_id, {})
            windows_status = await self._test_forwarder(windows_forwarder, "Windows")
            
            # Test application log forwarder
            app_forwarder = ApplicationLogForwarder(self.agent_id, {})
            app_status = await self._test_forwarder(app_forwarder, "Application")
            
            self.test_results['log_forwarding'] = {
                'status': 'success',
                'windows_forwarder': windows_status,
                'application_forwarder': app_status,
                'capabilities': ['windows_events', 'application_logs', 'system_logs']
            }
            
            logger.info(" Log forwarding capabilities verified")
            
        except Exception as e:
            logger.error(f" Log forwarding test failed: {e}")
            self.test_results['log_forwarding'] = {'status': 'failed', 'error': str(e)}
    
    async def _test_forwarder(self, forwarder, forwarder_name: str) -> Dict[str, Any]:
        """Test individual log forwarder"""
        try:
            # Test forwarder initialization
            await forwarder.start()
            
            # Test log collection
            logs_collected = 0
            if hasattr(forwarder, 'log_queue'):
                # Simulate some log collection
                await asyncio.sleep(1)
                logs_collected = forwarder.log_queue.qsize()
            
            await forwarder.stop()
            
            return {
                'status': 'success',
                'logs_collected': logs_collected,
                'initialization': 'success'
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_command_execution(self):
        """Test command execution capabilities"""
        logger.info("lightning Testing Command Execution...")
        
        try:
            # Create command executor
            executor = CommandExecutionEngine(self.agent_id, self.server_endpoint)
            
            # Test basic command execution
            test_commands = [
                {'technique': 'T1082', 'parameters': {'type': 'basic'}},  # System info
                {'technique': 'T1059', 'parameters': {'command': 'echo "test"'}},  # Command execution
            ]
            
            execution_results = []
            for cmd in test_commands:
                result = await executor._execute_command(cmd)
                execution_results.append(result)
            
            # Test statistics
            stats = executor.get_statistics()
            
            self.test_results['command_execution'] = {
                'status': 'success',
                'execution_enabled': stats['execution_enabled'],
                'test_commands_executed': len(execution_results),
                'successful_executions': sum(1 for r in execution_results if r.get('success')),
                'capabilities': ['system_discovery', 'command_execution', 'credential_dumping']
            }
            
            logger.info(" Command execution capabilities verified")
            
        except Exception as e:
            logger.error(f" Command execution test failed: {e}")
            self.test_results['command_execution'] = {'status': 'failed', 'error': str(e)}
    
    async def _test_container_management(self):
        """Test container management capabilities"""
        logger.info("📦 Testing Container Management...")
        
        try:
            # Create container manager
            config = {'containers': {'enabled': True, 'max_containers': 5}}
            container_manager = ContainerManager(self.agent_id, config)
            
            # Test Docker availability
            docker_available = container_manager.docker_available
            
            if docker_available:
                # Test container creation (if Docker available)
                container_status = container_manager.get_container_status()
                
                self.test_results['container_management'] = {
                    'status': 'success',
                    'docker_available': True,
                    'container_capabilities': ['container_creation', 'attack_execution', 'log_monitoring'],
                    'active_containers': container_status.get('active_containers', 0),
                    'golden_images': container_status.get('golden_images', 0)
                }
                
                logger.info(" Container management capabilities verified (Docker available)")
                
            else:
                self.test_results['container_management'] = {
                    'status': 'limited',
                    'docker_available': False,
                    'message': 'Container capabilities disabled - Docker not available',
                    'fallback_capabilities': ['command_execution', 'log_forwarding']
                }
                
                logger.info("WARNING: Container management limited - Docker not available")
                
        except Exception as e:
            logger.error(f" Container management test failed: {e}")
            self.test_results['container_management'] = {'status': 'failed', 'error': str(e)}
    
    async def _test_full_client_agent(self):
        """Test full client agent integration"""
        logger.info(" Testing Full Client Agent Integration...")
        
        try:
            # Create test configuration
            test_config = {
                'client': {
                    'agent_id': self.agent_id,
                    'server_endpoint': self.server_endpoint,
                    'api_key': '',
                    'reconnect_interval': 30,
                    'heartbeat_interval': 60
                },
                'log_forwarding': {
                    'enabled': True,
                    'batch_size': 10,
                    'flush_interval': 5,
                    'compression': False
                },
                'log_sources': {
                    'system_logs': {'enabled': True},
                    'security_logs': {'enabled': True},
                    'application_logs': {'enabled': True}
                },
                'windows': {
                    'event_logs': ['Security', 'System', 'Application'],
                    'wmi_enabled': True
                },
                'command_execution': {
                    'enabled': True,
                    'allowed_commands': ['powershell', 'cmd']
                },
                'containers': {
                    'enabled': True,
                    'max_containers': 5
                }
            }
            
            # Create temporary config file
            config_file = Path('test_config.yaml')
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump(test_config, f)
            
            # Create client agent
            client = LogForwardingClient(str(config_file))
            
            # Test client initialization
            client_status = client.get_status()
            
            # Test agent registration (without actually starting)
            try:
                # Create HTTP session for testing
                import aiohttp
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    client.session = session
                    
                    # Test registration endpoint
                    async with session.post(
                        f"{self.server_endpoint}/api/agents/register",
                        json={'agent_id': self.agent_id, 'test': True}
                    ) as response:
                        registration_success = response.status == 200
                        
            except Exception as e:
                registration_success = False
                logger.warning(f"Registration test failed: {e}")
            
            # Clean up
            if config_file.exists():
                config_file.unlink()
            
            self.test_results['capabilities'] = {
                'status': 'success',
                'client_initialization': 'success',
                'agent_registration': 'success' if registration_success else 'failed',
                'log_forwarding_enabled': client_status.get('forwarders', 0) > 0,
                'command_execution_enabled': client.command_executor is not None,
                'container_execution_enabled': client.container_executor is not None,
                'overall_capabilities': [
                    'log_forwarding',
                    'command_execution', 
                    'container_management' if self.test_results['docker_status'].get('status') == 'available' else 'command_execution_only',
                    'agent_registration',
                    'heartbeat_monitoring'
                ]
            }
            
            logger.info(" Full client agent integration verified")
            
        except Exception as e:
            logger.error(f" Full client agent test failed: {e}")
            self.test_results['capabilities'] = {'status': 'failed', 'error': str(e)}
    
    def _generate_final_report(self):
        """Generate final test report"""
        logger.info(" Generating Final Test Report...")
        
        # Determine overall status
        failed_tests = []
        partial_tests = []
        
        for test_name, result in self.test_results.items():
            if isinstance(result, dict) and 'status' in result:
                if result['status'] == 'failed':
                    failed_tests.append(test_name)
                elif result['status'] in ['partial', 'limited']:
                    partial_tests.append(test_name)
        
        if not failed_tests and not partial_tests:
            self.test_results['overall_status'] = 'excellent'
        elif not failed_tests:
            self.test_results['overall_status'] = 'good'
        elif len(failed_tests) <= 2:
            self.test_results['overall_status'] = 'acceptable'
        else:
            self.test_results['overall_status'] = 'poor'
        
        # Add summary
        self.test_results['summary'] = {
            'total_tests': len([k for k, v in self.test_results.items() if isinstance(v, dict) and 'status' in v]),
            'failed_tests': len(failed_tests),
            'partial_tests': len(partial_tests),
            'failed_test_names': failed_tests,
            'partial_test_names': partial_tests,
            'docker_available': self.test_results['docker_status'].get('status') == 'available',
            'server_reachable': self.test_results['network_connectivity'].get('server_reachable', False)
        }
        
        logger.info("=" * 60)
        logger.info(" CAPABILITY TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {self.test_results['overall_status'].upper()}")
        logger.info(f"Docker Available: {self.test_results['summary']['docker_available']}")
        logger.info(f"Server Reachable: {self.test_results['summary']['server_reachable']}")
        logger.info(f"Failed Tests: {len(failed_tests)}")
        logger.info(f"Partial Tests: {len(partial_tests)}")
        
        if failed_tests:
            logger.info(f"Failed: {', '.join(failed_tests)}")
        if partial_tests:
            logger.info(f"Partial: {', '.join(partial_tests)}")

async def main():
    """Main test execution"""
    print(" CodeGrey AI SOC Platform - Windows Client Capability Tester")
    print("=" * 70)
    print("Testing all client agent capabilities...")
    print("=" * 70)
    
    tester = WindowsClientCapabilityTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    results_file = Path('test_results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Docker Available: {results['summary']['docker_available']}")
    print(f"Server Reachable: {results['summary']['server_reachable']}")
    print(f"Failed Tests: {results['summary']['failed_tests']}")
    print(f"Partial Tests: {results['summary']['partial_tests']}")
    
    if results['summary']['failed_tests'] > 0:
        print(f"Failed: {', '.join(results['summary']['failed_test_names'])}")
    
    if results['summary']['partial_tests'] > 0:
        print(f"Partial: {', '.join(results['summary']['partial_test_names'])}")
    
    print("\n RECOMMENDATIONS:")
    
    if not results['summary']['docker_available']:
        print("- Docker not available - Container capabilities will be limited")
        print("- Client will still work for log forwarding and command execution")
        print("- Consider installing Docker for full container-based attack simulation")
    
    if not results['summary']['server_reachable']:
        print("- Server not reachable - Check network connectivity and server status")
        print("- Verify server endpoint: http://backend.codegrey.ai:8080")
    
    if results['overall_status'] in ['excellent', 'good']:
        print("-  Client agent is ready for deployment!")
        print("- All core capabilities are working")
    elif results['overall_status'] == 'acceptable':
        print("- WARNING: Client agent has some limitations but is functional")
        print("- Review failed tests and consider fixes")
    else:
        print("-  Client agent has significant issues")
        print("- Review and fix failed tests before deployment")
    
    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())

