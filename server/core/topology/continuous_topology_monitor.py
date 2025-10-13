"""
Continuous Network Topology Monitor
Real-time network topology updates from streaming logs
"""

import asyncio
import logging
from typing import Dict, Any, Set, List
from datetime import datetime, timedelta
from collections import defaultdict

from .network_mapper import NetworkTopologyMapper, NetworkNode
from shared.models import LogEntry


logger = logging.getLogger(__name__)


class ContinuousTopologyMonitor:
    """Continuously monitors and updates network topology from real-time logs"""
    
    def __init__(self, database_manager, topology_mapper: NetworkTopologyMapper):
        self.db_manager = database_manager
        self.topology_mapper = topology_mapper
        
        # Real-time processing
        self.running = False
        self.update_queue = asyncio.Queue(maxsize=1000)
        self.batch_update_interval = 30  # seconds
        self.full_refresh_interval = 300  # 5 minutes
        
        # Change tracking
        self.pending_changes = defaultdict(set)
        self.last_full_refresh = None
        self.topology_version = 0
        
        # Statistics
        self.stats = {
            'real_time_updates': 0,
            'nodes_added': 0,
            'nodes_updated': 0,
            'services_discovered': 0,
            'relationships_found': 0,
            'start_time': None
        }
        
        # Subscribers for topology changes
        self.change_subscribers = []
    
    async def start(self) -> None:
        """Start continuous topology monitoring"""
        if self.running:
            return
        
        logger.info("Starting Continuous Network Topology Monitor")
        self.running = True
        self.stats['start_time'] = datetime.utcnow()
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._real_time_processor()),
            asyncio.create_task(self._batch_updater()),
            asyncio.create_task(self._periodic_full_refresh()),
            asyncio.create_task(self._change_notifier())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Continuous topology monitor error: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop continuous monitoring"""
        logger.info("Stopping Continuous Network Topology Monitor")
        self.running = False
    
    async def process_log_entry(self, log_entry: LogEntry) -> None:
        """Process individual log entry for topology updates"""
        try:
            if not self.running:
                return
            
            # Check if log entry contains network-relevant information
            if await self._is_topology_relevant(log_entry):
                await self.update_queue.put(log_entry)
        
        except Exception as e:
            logger.error(f"Failed to process log entry for topology: {e}")
    
    async def _is_topology_relevant(self, log_entry: LogEntry) -> bool:
        """Check if log entry is relevant for network topology"""
        try:
            # Network-relevant indicators
            network_indicators = [
                'network', 'connection', 'ip', 'port', 'service', 'login', 'logon',
                'authentication', 'ssh', 'rdp', 'smb', 'http', 'dns', 'dhcp'
            ]
            
            message_lower = log_entry.message.lower()
            
            # Check message content
            if any(indicator in message_lower for indicator in network_indicators):
                return True
            
            # Check if it's a security or system log
            if log_entry.source.value in ['windows_system', 'linux_system', 'security']:
                return True
            
            # Check for network information in structured data
            if log_entry.network_info:
                return True
            
            # Check for process information (new services starting)
            if log_entry.process_info and any(svc in str(log_entry.process_info).lower() 
                                            for svc in ['service', 'daemon', 'server']):
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Topology relevance check failed: {e}")
            return False
    
    async def _real_time_processor(self) -> None:
        """Process log entries in real-time for topology updates"""
        logger.info("Starting real-time topology processor")
        
        while self.running:
            try:
                # Get log entry from queue
                log_entry = await asyncio.wait_for(
                    self.update_queue.get(), timeout=1.0
                )
                
                # Process for topology changes
                changes = await self._extract_topology_changes(log_entry)
                
                if changes:
                    # Track changes for batch processing
                    agent_id = log_entry.agent_id
                    self.pending_changes[agent_id].update(changes)
                    self.stats['real_time_updates'] += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Real-time processor error: {e}")
                await asyncio.sleep(1)
    
    async def _extract_topology_changes(self, log_entry: LogEntry) -> Set[str]:
        """Extract topology changes from log entry"""
        changes = set()
        
        try:
            # New IP address discovered
            if log_entry.network_info:
                if log_entry.network_info.get('source_ip'):
                    changes.add('ip_address')
                if log_entry.network_info.get('destination_ip'):
                    changes.add('network_connection')
            
            # New service discovered
            if log_entry.process_info:
                process_name = log_entry.process_info.get('process_name', '').lower()
                service_indicators = ['httpd', 'nginx', 'sshd', 'smbd', 'mysqld', 'postgres']
                if any(svc in process_name for svc in service_indicators):
                    changes.add('service_discovery')
            
            # Authentication event (user discovery)
            if any(tag in log_entry.tags for tag in ['authentication', 'login', 'logon']):
                changes.add('user_activity')
            
            # System information update
            if log_entry.event_type in ['system_start', 'service_start', 'network_change']:
                changes.add('system_info')
            
            # Security zone changes
            if 'firewall' in log_entry.message.lower() or 'zone' in log_entry.message.lower():
                changes.add('security_zone')
            
            return changes
        
        except Exception as e:
            logger.error(f"Change extraction failed: {e}")
            return set()
    
    async def _batch_updater(self) -> None:
        """Process pending changes in batches"""
        logger.info("Starting batch topology updater")
        
        while self.running:
            try:
                await asyncio.sleep(self.batch_update_interval)
                
                if self.pending_changes:
                    await self._process_pending_changes()
            
            except Exception as e:
                logger.error(f"Batch updater error: {e}")
                await asyncio.sleep(self.batch_update_interval)
    
    async def _process_pending_changes(self) -> None:
        """Process all pending topology changes"""
        try:
            if not self.pending_changes:
                return
            
            logger.info(f"Processing topology changes for {len(self.pending_changes)} agents")
            
            # Get recent logs for changed agents
            changed_agents = list(self.pending_changes.keys())
            
            for agent_id in changed_agents:
                changes = self.pending_changes[agent_id]
                
                # Get recent logs for this agent
                recent_logs = await self.db_manager.get_recent_logs(
                    agent_id=agent_id, hours=1, limit=100
                )
                
                # Update topology for this agent
                await self._update_agent_topology(agent_id, recent_logs, changes)
            
            # Clear pending changes
            self.pending_changes.clear()
            
            # Increment topology version
            self.topology_version += 1
            
            # Notify subscribers of changes
            await self._notify_topology_changes(changed_agents)
            
            logger.info(f"Topology updated (version {self.topology_version})")
            
        except Exception as e:
            logger.error(f"Pending changes processing failed: {e}")
    
    async def _update_agent_topology(self, agent_id: str, recent_logs: List[Dict], 
                                   changes: Set[str]) -> None:
        """Update topology for specific agent"""
        try:
            # Get or create node
            if agent_id not in self.topology_mapper.topology.nodes:
                node = NetworkNode(
                    agent_id=agent_id,
                    hostname=f'agent-{agent_id}'
                )
                self.topology_mapper.topology.nodes[agent_id] = node
                self.stats['nodes_added'] += 1
            else:
                node = self.topology_mapper.topology.nodes[agent_id]
                self.stats['nodes_updated'] += 1
            
            # Process each relevant log
            for log_data in recent_logs:
                await self.topology_mapper._process_log_for_topology(log_data)
            
            # Re-analyze node if significant changes
            if any(change in changes for change in ['service_discovery', 'system_info']):
                await self.topology_mapper._classify_node_role(node)
                await self.topology_mapper._assess_node_importance(node)
                
                if 'service_discovery' in changes:
                    self.stats['services_discovered'] += 1
            
            # Update relationships if network changes
            if 'network_connection' in changes:
                await self.topology_mapper._discover_relationships()
                self.stats['relationships_found'] += 1
            
            # Update last activity
            node.last_activity = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Agent topology update failed: {e}")
    
    async def _periodic_full_refresh(self) -> None:
        """Periodically refresh complete topology"""
        logger.info("Starting periodic full topology refresh")
        
        while self.running:
            try:
                await asyncio.sleep(self.full_refresh_interval)
                
                logger.info("Performing full topology refresh...")
                
                # Build complete topology from logs
                fresh_topology = await self.topology_mapper.build_topology_from_logs(hours=24)
                
                # Update our cached topology
                self.topology_mapper.topology = fresh_topology
                self.topology_version += 1
                self.last_full_refresh = datetime.utcnow()
                
                # Notify all subscribers
                await self._notify_topology_changes(list(fresh_topology.nodes.keys()))
                
                logger.info(f"Full topology refresh completed (version {self.topology_version})")
                
            except Exception as e:
                logger.error(f"Periodic refresh failed: {e}")
                await asyncio.sleep(self.full_refresh_interval)
    
    async def _change_notifier(self) -> None:
        """Notify subscribers of topology changes"""
        while self.running:
            try:
                await asyncio.sleep(5)  # Check for notifications every 5 seconds
                
                # This would be implemented based on your notification requirements
                # For now, just log significant changes
                
            except Exception as e:
                logger.error(f"Change notifier error: {e}")
                await asyncio.sleep(5)
    
    async def _notify_topology_changes(self, changed_agents: List[str]) -> None:
        """Notify subscribers about topology changes"""
        try:
            notification = {
                'event': 'topology_changed',
                'timestamp': datetime.utcnow().isoformat(),
                'topology_version': self.topology_version,
                'changed_agents': changed_agents,
                'change_count': len(changed_agents)
            }
            
            # Notify attack agents about topology changes
            await self._notify_attack_agents(notification)
            
            # Log significant changes
            if len(changed_agents) > 5:
                logger.info(f"Significant topology change: {len(changed_agents)} agents updated")
        
        except Exception as e:
            logger.error(f"Change notification failed: {e}")
    
    async def _notify_attack_agents(self, notification: Dict) -> None:
        """Notify attack agents about topology changes"""
        try:
            # This would integrate with your existing attack agents
            # to update their network context automatically
            
            # Example integration points:
            # 1. Update adaptive_attack_orchestrator network cache
            # 2. Trigger ai_attacker_brain to refresh network view
            # 3. Update dynamic_attack_generator with new targets
            
            logger.debug(f"Notifying attack agents of topology changes: {notification}")
            
            # You could implement webhooks, message queues, or direct method calls here
            
        except Exception as e:
            logger.error(f"Attack agent notification failed: {e}")
    
    def subscribe_to_changes(self, callback) -> None:
        """Subscribe to topology changes"""
        self.change_subscribers.append(callback)
        logger.info("New subscriber added to topology changes")
    
    def get_topology_status(self) -> Dict[str, Any]:
        """Get current topology monitoring status"""
        runtime = (datetime.utcnow() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
        
        return {
            'monitoring_status': 'active' if self.running else 'stopped',
            'topology_version': self.topology_version,
            'last_full_refresh': self.last_full_refresh.isoformat() if self.last_full_refresh else None,
            'pending_changes': len(self.pending_changes),
            'queue_size': self.update_queue.qsize(),
            'runtime_seconds': runtime,
            'statistics': {
                **self.stats,
                'updates_per_second': self.stats['real_time_updates'] / runtime if runtime > 0 else 0
            },
            'current_topology': {
                'total_nodes': len(self.topology_mapper.topology.nodes),
                'active_nodes': self.topology_mapper.topology.active_nodes,
                'high_value_targets': len(self.topology_mapper.topology.high_value_targets),
                'attack_paths': len(self.topology_mapper.topology.attack_paths)
            }
        }


class StreamingTopologyBuilder:
    """Builds topology from streaming log data"""
    
    def __init__(self, topology_monitor: ContinuousTopologyMonitor):
        self.monitor = topology_monitor
        self.stream_buffer = []
        self.buffer_size = 100
    
    async def process_log_stream(self, log_stream) -> None:
        """Process streaming logs for topology updates"""
        try:
            async for log_entry in log_stream:
                # Add to monitor queue
                await self.monitor.process_log_entry(log_entry)
                
                # Buffer for batch processing
                self.stream_buffer.append(log_entry)
                
                if len(self.stream_buffer) >= self.buffer_size:
                    await self._process_buffer()
        
        except Exception as e:
            logger.error(f"Stream processing failed: {e}")
    
    async def _process_buffer(self) -> None:
        """Process buffered log entries"""
        try:
            if not self.stream_buffer:
                return
            
            # Group by agent for efficient processing
            agent_logs = defaultdict(list)
            for log_entry in self.stream_buffer:
                agent_logs[log_entry.agent_id].append(log_entry)
            
            # Process each agent's logs
            for agent_id, logs in agent_logs.items():
                await self._update_agent_from_logs(agent_id, logs)
            
            # Clear buffer
            self.stream_buffer.clear()
        
        except Exception as e:
            logger.error(f"Buffer processing failed: {e}")
    
    async def _update_agent_from_logs(self, agent_id: str, logs: List[LogEntry]) -> None:
        """Update agent topology from batch of logs"""
        try:
            changes = set()
            
            for log_entry in logs:
                entry_changes = await self.monitor._extract_topology_changes(log_entry)
                changes.update(entry_changes)
            
            if changes:
                # Convert LogEntry objects to dict format for processing
                log_dicts = [log.to_dict() for log in logs]
                await self.monitor._update_agent_topology(agent_id, log_dicts, changes)
        
        except Exception as e:
            logger.error(f"Agent update from logs failed: {e}")
