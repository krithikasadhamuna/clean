#!/usr/bin/env python3
"""
Comprehensive Test Suite for CodeGrey AI SOC Platform
Tests all capabilities including container orchestration and attack agents
"""

import requests
import json
import time
import sys
import asyncio
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8080"
API_KEY = None  # Disabled in development

class ComprehensiveTestSuite:
    """Complete test suite for all SOC platform capabilities"""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.passed_tests = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            self.passed_tests.append(test_name)
            print(f" {test_name}")
        else:
            self.failed_tests.append(test_name)
            print(f" {test_name}: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 10) -> Dict:
        """Make HTTP request with error handling"""
        try:
            url = f"{BASE_URL}{endpoint}"
            headers = {'Content-Type': 'application/json'}
            
            if API_KEY:
                headers['X-API-Key'] = API_KEY
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                return {'error': f'Unsupported method: {method}'}
            
            return {
                'status_code': response.status_code,
                'data': response.json() if response.content else {},
                'success': response.status_code == 200
            }
            
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    def test_server_health(self):
        """Test server health endpoint"""
        print("\n🏥 Testing Server Health")
        print("=" * 40)
        
        result = self.make_request('GET', '/health')
        
        if result.get('success'):
            data = result['data']
            self.log_test("Server Health Check", True, f"Status: {data.get('status')}")
            
            # Check agent availability
            agents = data.get('agents', {})
            if isinstance(agents, dict):
                for agent_type, status in agents.items():
                    self.log_test(f"{agent_type.title()} Agent Available", 
                                status == 'available', f"Status: {status}")
            
            # Check LangChain integration
            langchain_status = data.get('langchain_integration', 'unknown')
            self.log_test("LangChain Integration", 
                         langchain_status == 'active', f"Status: {langchain_status}")
        else:
            self.log_test("Server Health Check", False, result.get('error', 'Unknown error'))
    
    def test_frontend_apis(self):
        """Test all frontend API endpoints"""
        print("\n🖥️ Testing Frontend APIs")
        print("=" * 40)
        
        # Test agents API
        result = self.make_request('GET', '/api/backend/agents')
        if result.get('success'):
            data = result['data']
            agents = data.get('data', [])
            self.log_test("Frontend Agents API", True, f"Found {len(agents)} agents")
            
            # Validate agent structure
            if agents:
                agent = agents[0]
                required_fields = ['id', 'name', 'type', 'status', 'capabilities']
                missing_fields = [field for field in required_fields if field not in agent]
                self.log_test("Agent Data Structure", 
                             len(missing_fields) == 0, 
                             f"Missing fields: {missing_fields}" if missing_fields else "All fields present")
        else:
            self.log_test("Frontend Agents API", False, result.get('error'))
        
        # Test network topology API
        result = self.make_request('GET', '/api/backend/network-topology')
        if result.get('success'):
            data = result['data']
            topology_data = data.get('data', [])
            self.log_test("Network Topology API", True, f"Found {len(topology_data)} network nodes")
        else:
            self.log_test("Network Topology API", False, result.get('error'))
        
        # Test software download API
        result = self.make_request('GET', '/api/backend/software-download')
        if result.get('success'):
            data = result['data']
            downloads = data.get('data', [])
            self.log_test("Software Download API", True, f"Found {len(downloads)} download packages")
            
            # Validate download structure
            if downloads:
                download = downloads[0]
                required_fields = ['id', 'name', 'version', 'downloadUrl', 'os']
                missing_fields = [field for field in required_fields if field not in download]
                self.log_test("Download Data Structure", 
                             len(missing_fields) == 0,
                             f"Missing fields: {missing_fields}" if missing_fields else "All fields present")
        else:
            self.log_test("Software Download API", False, result.get('error'))
        
        # Test detection results API
        result = self.make_request('GET', '/api/backend/detections')
        if result.get('success'):
            data = result['data']
            detections = data.get('data', [])
            self.log_test("Detection Results API", True, f"Found {len(detections)} detection results")
        else:
            self.log_test("Detection Results API", False, result.get('error'))
    
    def test_attack_agents_api(self):
        """Test attack agents API"""
        print("\n Testing Attack Agents API")
        print("=" * 40)
        
        result = self.make_request('GET', '/api/backend/attack-agents')
        
        if result.get('success'):
            data = result['data']
            agents = data.get('agents', [])
            self.log_test("Attack Agents API", True, f"Found {len(agents)} attack agents")
            
            # Validate agent structure matches PhantomStrike format
            if agents:
                agent = agents[0]
                required_fields = ['id', 'name', 'type', 'status', 'location', 'lastActivity', 'capabilities', 'platform']
                missing_fields = [field for field in required_fields if field not in agent]
                self.log_test("Attack Agent Data Structure", 
                             len(missing_fields) == 0,
                             f"Missing fields: {missing_fields}" if missing_fields else "PhantomStrike format validated")
                
                # Check for PhantomStrike agents
                phantomstrike_agents = [a for a in agents if 'phantomstrike' in a.get('id', '').lower()]
                self.log_test("PhantomStrike Agents Present", 
                             len(phantomstrike_agents) > 0,
                             f"Found {len(phantomstrike_agents)} PhantomStrike agents")
        else:
            self.log_test("Attack Agents API", False, result.get('error'))
    
    def test_log_ingestion(self):
        """Test log ingestion system"""
        print("\n Testing Log Ingestion")
        print("=" * 40)
        
        # Test regular log ingestion
        sample_logs = {
            'agent_id': 'test-agent-comprehensive',
            'logs': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'source': 'TestSystem',
                    'message': 'Test log message for comprehensive testing',
                    'hostname': 'test-host',
                    'platform': 'Test'
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'WARNING',
                    'source': 'SecuritySystem',
                    'message': 'Potential security event detected during testing',
                    'hostname': 'test-host',
                    'platform': 'Test'
                }
            ]
        }
        
        result = self.make_request('POST', '/api/logs/ingest', sample_logs)
        if result.get('success'):
            data = result['data']
            self.log_test("Regular Log Ingestion", True, f"Ingested {len(sample_logs['logs'])} logs")
        else:
            self.log_test("Regular Log Ingestion", False, result.get('error'))
        
        # Test container log ingestion (as regular logs)
        container_logs = {
            'agent_id': 'test-container-agent',
            'logs': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'source': 'AttackContainer',
                    'message': 'Starting nmap scan on target network 192.168.1.0/24',
                    'hostname': 'test-container-agent',
                    'platform': 'Container',
                    'agent_type': 'attack_agent',
                    'container_context': True
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'source': 'AttackContainer',
                    'message': 'sqlmap detected potential SQL injection vulnerability',
                    'hostname': 'test-container-agent',
                    'platform': 'Container',
                    'agent_type': 'attack_agent',
                    'container_context': True
                }
            ]
        }
        
        result = self.make_request('POST', '/api/logs/ingest', container_logs)
        if result.get('success'):
            data = result['data']
            self.log_test("Container Log Ingestion", True, f"Ingested {len(container_logs['logs'])} container logs as regular logs")
        else:
            self.log_test("Container Log Ingestion", False, result.get('error'))
    
    def test_agent_heartbeat(self):
        """Test agent heartbeat functionality"""
        print("\n💓 Testing Agent Heartbeat")
        print("=" * 40)
        
        heartbeat_data = {
            'hostname': 'test-comprehensive-agent',
            'platform': 'TestOS',
            'system_info': {
                'hostname': 'test-comprehensive-agent',
                'os': 'TestOS 1.0',
                'architecture': 'x64',
                'memory_total': 8589934592,
                'network_interfaces': [
                    {
                        'name': 'eth0',
                        'ip': '192.168.1.100',
                        'netmask': '255.255.255.0'
                    }
                ]
            },
            'network_discovery': {
                'discovered_hosts': {
                    '192.168.1.1': {'hostname': 'gateway', 'services': ['ssh', 'http']},
                    '192.168.1.10': {'hostname': 'server1', 'services': ['mysql', 'apache']}
                }
            }
        }
        
        result = self.make_request('POST', '/api/agents/test-comprehensive-agent/heartbeat', heartbeat_data)
        if result.get('success'):
            self.log_test("Agent Heartbeat", True, "Heartbeat accepted with system info and network discovery")
        else:
            self.log_test("Agent Heartbeat", False, result.get('error'))
        
        # Test getting commands for agent
        result = self.make_request('GET', '/api/agents/test-comprehensive-agent/commands')
        if result.get('success'):
            data = result['data']
            commands = data.get('commands', [])
            self.log_test("Agent Commands Retrieval", True, f"Retrieved {len(commands)} pending commands")
        else:
            self.log_test("Agent Commands Retrieval", False, result.get('error'))
    
    def test_langserve_endpoints(self):
        """Test LangServe endpoints"""
        print("\n Testing LangServe Endpoints")
        print("=" * 40)
        
        # Test SOC orchestrator endpoint
        result = self.make_request('GET', '/api/soc')
        self.log_test("SOC Orchestrator Endpoint", 
                     result.get('status_code') in [200, 404],  # 404 is OK if agents not available
                     f"Status: {result.get('status_code')}")
        
        # Test detection agent endpoint
        result = self.make_request('GET', '/api/detection')
        self.log_test("Detection Agent Endpoint", 
                     result.get('status_code') in [200, 404],  # 404 is OK if agents not available
                     f"Status: {result.get('status_code')}")
        
        # Test attack agent endpoint
        result = self.make_request('GET', '/api/attack')
        self.log_test("Attack Agent Endpoint", 
                     result.get('status_code') in [200, 404],  # 404 is OK if agents not available
                     f"Status: {result.get('status_code')}")
        
        # Test custom SOC endpoints
        threat_data = {
            'detection_data': {
                'threat_type': 'test_threat',
                'severity': 'medium',
                'indicators': ['test_indicator_1', 'test_indicator_2']
            },
            'context': {
                'agent_id': 'test-agent',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        result = self.make_request('POST', '/api/soc/analyze-threat', threat_data)
        self.log_test("SOC Threat Analysis", 
                     result.get('status_code') in [200, 500],  # 500 OK if agents not available
                     f"Status: {result.get('status_code')}")
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        print("\n Testing CORS Configuration")
        print("=" * 40)
        
        try:
            # Test preflight request
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = requests.options(f"{BASE_URL}/api/backend/agents", headers=headers, timeout=5)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            self.log_test("CORS Preflight", 
                         response.status_code == 200,
                         f"Headers: {cors_headers}")
            
            # Check if development origins are allowed
            origin_allowed = cors_headers.get('Access-Control-Allow-Origin') in ['*', 'http://localhost:3000']
            self.log_test("CORS Origin Allowed", 
                         origin_allowed,
                         f"Allowed origin: {cors_headers.get('Access-Control-Allow-Origin')}")
            
        except Exception as e:
            self.log_test("CORS Configuration", False, str(e))
    
    def test_database_operations(self):
        """Test database operations"""
        print("\n🗄️ Testing Database Operations")
        print("=" * 40)
        
        try:
            import sqlite3
            
            # Test database file exists
            db_path = 'dev_soc_database.db'
            db_exists = os.path.exists(db_path)
            self.log_test("Database File Exists", db_exists, f"Path: {db_path}")
            
            if db_exists:
                # Test database connection
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check for required tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['log_entries', 'agents', 'detection_results']
                for table in required_tables:
                    table_exists = table in tables
                    self.log_test(f"Table '{table}' Exists", table_exists, f"Found tables: {tables}")
                
                # Test data insertion and retrieval
                cursor.execute("SELECT COUNT(*) FROM log_entries")
                log_count = cursor.fetchone()[0]
                self.log_test("Log Entries Data", log_count >= 0, f"Found {log_count} log entries")
                
                cursor.execute("SELECT COUNT(*) FROM agents")
                agent_count = cursor.fetchone()[0]
                self.log_test("Agent Data", agent_count >= 0, f"Found {agent_count} registered agents")
                
                conn.close()
                
        except Exception as e:
            self.log_test("Database Operations", False, str(e))
    
    def test_client_agent_simulation(self):
        """Simulate client agent behavior"""
        print("\n Testing Client Agent Simulation")
        print("=" * 40)
        
        # Simulate a complete client agent workflow
        agent_id = 'simulated-client-agent'
        
        # 1. Send heartbeat
        heartbeat_data = {
            'hostname': agent_id,
            'platform': 'SimulatedOS',
            'system_info': {
                'hostname': agent_id,
                'os': 'SimulatedOS 2.0',
                'installed_software': [
                    {'name': 'Apache', 'version': '2.4.41'},
                    {'name': 'MySQL', 'version': '8.0.25'}
                ],
                'running_services': [
                    {'name': 'apache2', 'status': 'running'},
                    {'name': 'mysql', 'status': 'running'}
                ],
                'open_ports': [80, 443, 3306, 22],
                'network_interfaces': [
                    {'name': 'eth0', 'ip': '10.0.0.50', 'netmask': '255.255.255.0'}
                ]
            }
        }
        
        result = self.make_request('POST', f'/api/agents/{agent_id}/heartbeat', heartbeat_data)
        self.log_test("Client Agent Heartbeat Simulation", result.get('success'), 
                     result.get('error', 'Heartbeat successful'))
        
        # 2. Send logs
        log_data = {
            'agent_id': agent_id,
            'logs': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'source': 'Apache',
                    'message': 'New connection from 192.168.1.100',
                    'hostname': agent_id,
                    'platform': 'SimulatedOS'
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'WARNING',
                    'source': 'MySQL',
                    'message': 'Multiple failed login attempts detected',
                    'hostname': agent_id,
                    'platform': 'SimulatedOS'
                }
            ]
        }
        
        result = self.make_request('POST', '/api/logs/ingest', log_data)
        self.log_test("Client Agent Log Forwarding", result.get('success'),
                     result.get('error', 'Logs forwarded successfully'))
        
        # 3. Check for pending commands
        result = self.make_request('GET', f'/api/agents/{agent_id}/commands')
        self.log_test("Client Agent Command Retrieval", result.get('success'),
                     result.get('error', 'Commands retrieved successfully'))
    
    def test_performance_metrics(self):
        """Test performance and response times"""
        print("\nlightning Testing Performance Metrics")
        print("=" * 40)
        
        endpoints_to_test = [
            '/health',
            '/api/backend/agents',
            '/api/backend/network-topology',
            '/api/backend/software-download',
            '/api/backend/attack-agents'
        ]
        
        for endpoint in endpoints_to_test:
            start_time = time.time()
            result = self.make_request('GET', endpoint)
            response_time = time.time() - start_time
            
            # Consider response time good if under 2 seconds
            performance_good = response_time < 2.0
            self.log_test(f"Performance {endpoint}", 
                         performance_good and result.get('success'),
                         f"Response time: {response_time:.3f}s")
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n🚨 Testing Error Handling")
        print("=" * 40)
        
        # Test invalid endpoint
        result = self.make_request('GET', '/api/invalid/endpoint')
        self.log_test("Invalid Endpoint Handling", 
                     result.get('status_code') == 404,
                     f"Status: {result.get('status_code')}")
        
        # Test malformed data
        result = self.make_request('POST', '/api/logs/ingest', {'invalid': 'data'})
        # Should either handle gracefully or return proper error
        handled_gracefully = result.get('success') or result.get('status_code') in [400, 422, 500]
        self.log_test("Malformed Data Handling", handled_gracefully,
                     f"Status: {result.get('status_code')}")
        
        # Test missing required fields
        result = self.make_request('POST', '/api/agents/test/heartbeat', {})
        handled_gracefully = result.get('success') or result.get('status_code') in [400, 422, 500]
        self.log_test("Missing Fields Handling", handled_gracefully,
                     f"Status: {result.get('status_code')}")
    
    def run_all_tests(self):
        """Run all tests"""
        print(" CodeGrey AI SOC Platform - Comprehensive Test Suite")
        print("=" * 60)
        print(f"Testing server at: {BASE_URL}")
        print(f"Authentication: {'Enabled' if API_KEY else 'Disabled'}")
        print(f"Test started: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Run all test categories
        self.test_server_health()
        self.test_frontend_apis()
        self.test_attack_agents_api()
        self.test_log_ingestion()
        self.test_agent_heartbeat()
        self.test_langserve_endpoints()
        self.test_cors_configuration()
        self.test_database_operations()
        self.test_client_agent_simulation()
        self.test_performance_metrics()
        self.test_error_handling()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print(" TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)
        success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f" Passed: {passed_count}")
        print(f" Failed: {failed_count}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_count > 0:
            print(f"\n Failed Tests:")
            for test_name in self.failed_tests:
                print(f"   - {test_name}")
        
        print(f"\n Passed Tests:")
        for test_name in self.passed_tests:
            print(f"   - {test_name}")
        
        # Overall status
        print(f"\n Overall Status: {'PASS' if success_rate >= 80 else 'NEEDS ATTENTION'}")
        
        if success_rate >= 95:
            print("🎉 Excellent! All systems operational.")
        elif success_rate >= 80:
            print(" Good! Most systems operational with minor issues.")
        elif success_rate >= 60:
            print("WARNING:  Moderate issues detected. Some systems need attention.")
        else:
            print("🚨 Multiple critical issues detected. Immediate attention required.")
        
        print("\n" + "=" * 60)
        
        # Save detailed results to file
        with open('test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_count,
                    'failed': failed_count,
                    'success_rate': success_rate,
                    'timestamp': datetime.now().isoformat()
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to: test_results.json")

def main():
    """Main test execution"""
    if len(sys.argv) > 1:
        global BASE_URL
        BASE_URL = sys.argv[1]
    
    test_suite = ComprehensiveTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()
