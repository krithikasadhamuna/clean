"""
Container-Based Attack Execution Engine
Executes PhantomStrike AI attacks in isolated Docker containers
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .container_manager import ContainerManager
from shared.utils import safe_json_loads


logger = logging.getLogger(__name__)


class ContainerAttackExecutor:
    """Executes attacks in Docker containers"""
    
    def __init__(self, agent_id: str, server_endpoint: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.server_endpoint = server_endpoint
        self.config = config
        
        # Container management
        self.container_manager = ContainerManager(agent_id, config)
        
        # Execution state
        self.running = False
        self.active_executions = {}
        
        # Container templates for different attack scenarios
        self.container_templates = {
            'windows_endpoint': {
                'image': 'mcr.microsoft.com/windows/servercore:ltsc2019',
                'platform': 'windows',
                'tools': ['powershell', 'cmd', 'net', 'reg'],
                'logs': ['windows_events', 'powershell_logs']
            },
            'linux_server': {
                'image': 'ubuntu:22.04',
                'platform': 'linux', 
                'tools': ['bash', 'python3', 'curl', 'wget'],
                'logs': ['syslog', 'auth_log', 'audit_log']
            },
            'web_application': {
                'image': 'nginx:alpine',
                'platform': 'linux',
                'tools': ['curl', 'sqlmap', 'nikto'],
                'logs': ['access_log', 'error_log']
            },
            'database_server': {
                'image': 'mysql:8.0',
                'platform': 'linux',
                'tools': ['mysql', 'mysqldump'],
                'logs': ['mysql_logs', 'audit_logs']
            }
        }
    
    async def start(self) -> None:
        """Start container attack executor"""
        if self.running:
            return
        
        logger.info("Starting Container Attack Executor")
        self.running = True
        
        try:
            # Start container manager
            await self.container_manager._initialize_docker()
            
            if not self.container_manager.docker_available:
                logger.warning("Docker not available - container execution disabled")
                self.running = False
                return
            
            # Start execution monitoring
            asyncio.create_task(self._execution_monitor())
            
            logger.info("Container Attack Executor started")
            
        except Exception as e:
            logger.error(f"Failed to start container executor: {e}")
            self.running = False
    
    async def stop(self) -> None:
        """Stop container attack executor"""
        logger.info("Stopping Container Attack Executor")
        self.running = False
        
        # Clean up active containers
        await self._cleanup_all_containers()
    
    async def execute_attack_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete attack scenario in containers"""
        try:
            scenario_id = scenario.get('id', f"scenario_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            
            logger.info(f"Executing attack scenario: {scenario.get('name', scenario_id)}")
            
            # Step 1: Create golden image snapshots of target environments
            golden_images = await self._create_scenario_golden_images(scenario)
            
            # Step 2: Create attack execution containers
            containers = await self._create_scenario_containers(scenario)
            
            if not containers:
                return {'success': False, 'error': 'Failed to create execution containers'}
            
            # Step 3: Execute attack phases
            execution_results = []
            
            for phase in scenario.get('phases', []):
                phase_result = await self._execute_attack_phase(phase, containers)
                execution_results.append(phase_result)
                
                # Wait between phases
                await asyncio.sleep(2)
            
            # Step 4: Collect all logs generated
            all_logs = await self._collect_scenario_logs(containers)
            
            # Step 5: Clean up or preserve containers based on configuration
            cleanup_result = await self._cleanup_scenario_containers(
                containers, 
                preserve=scenario.get('preserve_containers', False)
            )
            
            return {
                'success': True,
                'scenario_id': scenario_id,
                'execution_results': execution_results,
                'containers_used': len(containers),
                'logs_generated': len(all_logs),
                'golden_images_created': len(golden_images),
                'cleanup_result': cleanup_result,
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Attack scenario execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _create_scenario_golden_images(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create golden images for scenario targets"""
        golden_images = []
        
        try:
            target_platforms = scenario.get('target_platforms', ['linux'])
            
            for platform in target_platforms:
                # Create base container for platform
                container_config = {
                    'scenario_id': scenario.get('id'),
                    'target_platform': platform
                }
                
                container_result = await self.container_manager.create_attack_container(container_config)
                
                if container_result.get('success'):
                    container_id = container_result['container_id']
                    
                    # Let container initialize
                    await asyncio.sleep(5)
                    
                    # Create golden image snapshot
                    snapshot_name = f"golden-{platform}-{scenario.get('id', 'unknown')}"
                    snapshot_result = await self.container_manager.create_golden_image_snapshot(
                        container_id, snapshot_name
                    )
                    
                    if snapshot_result.get('success'):
                        golden_images.append(snapshot_result)
                        logger.info(f"Golden image created: {snapshot_name}")
                    
                    # Keep container for attack execution
                else:
                    logger.error(f"Failed to create container for {platform}")
            
            return golden_images
            
        except Exception as e:
            logger.error(f"Golden image creation failed: {e}")
            return golden_images
    
    async def _create_scenario_containers(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create containers for attack scenario execution"""
        containers = []
        
        try:
            # Determine required container types based on scenario
            required_containers = self._analyze_scenario_requirements(scenario)
            
            for container_type in required_containers:
                container_config = {
                    'scenario_id': scenario.get('id'),
                    'target_platform': container_type,
                    'container_type': container_type
                }
                
                result = await self.container_manager.create_attack_container(container_config)
                
                if result.get('success'):
                    containers.append({
                        'container_id': result['container_id'],
                        'container_name': result['container_name'],
                        'type': container_type,
                        'platform': container_type
                    })
                    logger.info(f"Created {container_type} container: {result['container_name']}")
            
            return containers
            
        except Exception as e:
            logger.error(f"Scenario container creation failed: {e}")
            return []
    
    def _analyze_scenario_requirements(self, scenario: Dict[str, Any]) -> List[str]:
        """Analyze scenario to determine required container types"""
        required_containers = []
        
        try:
            techniques = scenario.get('mitre_techniques', [])
            target_elements = scenario.get('target_elements', [])
            
            # Determine container types based on techniques and targets
            if any(tech.startswith('T1059') for tech in techniques):  # Command execution
                required_containers.append('linux_server')
            
            if any(element in target_elements for element in ['web_server', 'web_application']):
                required_containers.append('web_application')
            
            if any(element in target_elements for element in ['database', 'database_server']):
                required_containers.append('database_server')
            
            if any(element in target_elements for element in ['windows', 'endpoint']):
                required_containers.append('windows_endpoint')
            
            # Default to linux server if nothing specific
            if not required_containers:
                required_containers.append('linux_server')
            
            return list(set(required_containers))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Scenario analysis failed: {e}")
            return ['linux_server']  # Fallback
    
    async def _execute_attack_phase(self, phase: Dict[str, Any], 
                                  containers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute single attack phase across containers"""
        try:
            phase_name = phase.get('name', 'unknown')
            techniques = phase.get('techniques', [])
            
            logger.info(f"Executing attack phase: {phase_name}")
            
            phase_results = []
            
            # Execute each technique
            for technique in techniques:
                # Select appropriate container for technique
                container = self._select_container_for_technique(technique, containers)
                
                if container:
                    # Execute technique in container
                    result = await self.container_manager.execute_attack_technique(
                        container['container_id'],
                        technique,
                        phase.get('parameters', {})
                    )
                    
                    phase_results.append(result)
                    
                    # Small delay between techniques
                    await asyncio.sleep(1)
            
            return {
                'phase_name': phase_name,
                'techniques_executed': len(techniques),
                'results': phase_results,
                'success_count': sum(1 for r in phase_results if r.get('success')),
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Attack phase execution failed: {e}")
            return {'phase_name': phase.get('name'), 'error': str(e)}
    
    def _select_container_for_technique(self, technique: str, 
                                      containers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select appropriate container for MITRE technique"""
        
        # Technique to platform mapping
        windows_techniques = ['T1059.001', 'T1055', 'T1003.001', 'T1548.002']
        linux_techniques = ['T1059.004', 'T1068', 'T1548.001']
        web_techniques = ['T1190', 'T1566.002']
        
        # Select container based on technique
        if technique in windows_techniques:
            for container in containers:
                if 'windows' in container.get('type', ''):
                    return container
        
        elif technique in linux_techniques:
            for container in containers:
                if 'linux' in container.get('type', ''):
                    return container
        
        elif technique in web_techniques:
            for container in containers:
                if 'web' in container.get('type', ''):
                    return container
        
        # Fallback to first available container
        return containers[0] if containers else None
    
    async def _collect_scenario_logs(self, containers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect all logs generated during scenario execution"""
        all_logs = []
        
        try:
            for container in containers:
                container_id = container['container_id']
                
                if container_id in self.container_manager.container_logs:
                    container_logs = self.container_manager.container_logs[container_id]
                    
                    # Convert LogEntry objects to dicts
                    for log_entry in container_logs:
                        log_dict = log_entry.to_dict() if hasattr(log_entry, 'to_dict') else log_entry
                        all_logs.append(log_dict)
            
            logger.info(f"Collected {len(all_logs)} logs from scenario execution")
            return all_logs
            
        except Exception as e:
            logger.error(f"Log collection failed: {e}")
            return all_logs
    
    async def _cleanup_scenario_containers(self, containers: List[Dict[str, Any]], 
                                         preserve: bool = False) -> Dict[str, Any]:
        """Clean up containers after scenario execution"""
        try:
            if preserve:
                logger.info("Preserving containers for analysis")
                return {'containers_preserved': len(containers)}
            
            cleanup_results = []
            
            for container in containers:
                container_id = container['container_id']
                
                # Create final snapshot before cleanup
                result = await self.container_manager.destroy_container(
                    container_id, 
                    create_snapshot=True
                )
                
                cleanup_results.append(result)
            
            successful_cleanups = sum(1 for r in cleanup_results if r.get('success'))
            
            return {
                'containers_cleaned': successful_cleanups,
                'cleanup_results': cleanup_results,
                'cleaned_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Container cleanup failed: {e}")
            return {'error': str(e)}
    
    async def _execution_monitor(self) -> None:
        """Monitor container executions"""
        while self.running:
            try:
                # Monitor container health and log forwarding
                for execution_id, execution_info in list(self.active_executions.items()):
                    await self._check_execution_health(execution_id, execution_info)
                
                await asyncio.sleep(10)  # Check every 10 seconds
            
            except Exception as e:
                logger.error(f"Execution monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _check_execution_health(self, execution_id: str, execution_info: Dict[str, Any]) -> None:
        """Check health of running execution"""
        try:
            # Check if containers are still running
            containers = execution_info.get('containers', [])
            
            for container in containers:
                container_id = container['container_id']
                
                if container_id in self.container_manager.active_containers:
                    container_obj = self.container_manager.active_containers[container_id]['container']
                    
                    try:
                        container_obj.reload()
                        if container_obj.status != 'running':
                            logger.warning(f"Container {container_obj.name} is not running: {container_obj.status}")
                    except Exception as e:
                        logger.error(f"Container health check failed: {e}")
        
        except Exception as e:
            logger.error(f"Execution health check failed: {e}")
    
    async def _cleanup_all_containers(self) -> None:
        """Clean up all active containers"""
        try:
            logger.info("Cleaning up all containers")
            
            for container_id in list(self.container_manager.active_containers.keys()):
                await self.container_manager.destroy_container(container_id, create_snapshot=True)
            
            logger.info("All containers cleaned up")
            
        except Exception as e:
            logger.error(f"Container cleanup failed: {e}")
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get container execution status"""
        return {
            'executor_running': self.running,
            'docker_available': self.container_manager.docker_available,
            'active_executions': len(self.active_executions),
            'container_status': self.container_manager.get_container_status(),
            'container_templates': list(self.container_templates.keys())
        }
