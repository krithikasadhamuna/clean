#!/usr/bin/env python3
"""
Physical Location Detection for Network Topology
Detects actual geographic and physical locations of network endpoints
"""

import socket
import subprocess
import requests
import json
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LocationDetector:
    """Detect physical location of network endpoints"""
    
    def __init__(self):
        self.location_cache = {}
        self.gateway_info = None
        
    def detect_location(self, ip_address: str, hostname: str = None) -> Dict[str, Any]:
        """Detect physical location of an IP address"""
        
        # Check cache first
        if ip_address in self.location_cache:
            return self.location_cache[ip_address]
        
        location_info = {
            'ipAddress': ip_address,
            'hostname': hostname,
            'locationType': 'unknown',
            'physicalLocation': 'Unknown',
            'networkZone': 'Unknown',
            'city': 'Unknown',
            'country': 'Unknown',
            'organization': 'Unknown',
            'detectionMethod': 'unknown'
        }
        
        try:
            # 1. Local network detection
            if self._is_local_ip(ip_address):
                location_info.update(self._detect_local_location(ip_address, hostname))
            
            # 2. Public IP geolocation
            elif self._is_public_ip(ip_address):
                location_info.update(self._detect_public_location(ip_address))
            
            # 3. Private network analysis
            else:
                location_info.update(self._detect_private_network_location(ip_address, hostname))
            
            # Cache result
            self.location_cache[ip_address] = location_info
            
        except Exception as e:
            logger.error(f"Location detection failed for {ip_address}: {e}")
            location_info['detectionMethod'] = 'error'
        
        return location_info
    
    def _is_local_ip(self, ip: str) -> bool:
        """Check if IP is local loopback"""
        return ip.startswith('127.') or ip == 'localhost'
    
    def _is_public_ip(self, ip: str) -> bool:
        """Check if IP is public (not private/local)"""
        try:
            import ipaddress
            ip_obj = ipaddress.IPv4Address(ip)
            return ip_obj.is_global
        except:
            return False
    
    def _detect_local_location(self, ip: str, hostname: str) -> Dict[str, Any]:
        """Detect location for local/loopback IPs"""
        
        # Get actual physical location of the local machine
        physical_location = self._get_local_physical_location()
        
        return {
            'locationType': 'local',
            'physicalLocation': physical_location,
            'networkZone': 'Local Development',
            'city': self._get_local_city(),
            'country': self._get_local_country(),
            'organization': 'Development Environment',
            'detectionMethod': 'local_system_analysis'
        }
    
    def _detect_public_location(self, ip: str) -> Dict[str, Any]:
        """Detect location for public IPs using geolocation APIs"""
        try:
            # Try multiple geolocation services
            location_data = self._query_geolocation_api(ip)
            
            if location_data:
                return {
                    'locationType': 'public',
                    'physicalLocation': f"{location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}",
                    'networkZone': 'External Network',
                    'city': location_data.get('city', 'Unknown'),
                    'country': location_data.get('country', 'Unknown'),
                    'organization': location_data.get('org', 'Unknown'),
                    'detectionMethod': 'geolocation_api'
                }
            
        except Exception as e:
            logger.error(f"Public IP location detection failed: {e}")
        
        return {
            'locationType': 'public',
            'physicalLocation': 'External Location',
            'networkZone': 'External Network',
            'detectionMethod': 'fallback'
        }
    
    def _detect_private_network_location(self, ip: str, hostname: str) -> Dict[str, Any]:
        """Detect location for private network IPs"""
        
        # Analyze IP range patterns for physical location hints
        location_info = self._analyze_ip_patterns(ip)
        
        # Enhance with hostname analysis
        if hostname:
            hostname_info = self._analyze_hostname_patterns(hostname)
            location_info.update(hostname_info)
        
        # Get network zone based on IP range
        network_zone = self._determine_network_zone(ip)
        
        # Try to determine physical location from network infrastructure
        physical_location = self._determine_physical_location_from_network(ip, hostname)
        
        return {
            'locationType': 'private',
            'physicalLocation': physical_location,
            'networkZone': network_zone,
            'city': location_info.get('city', 'Unknown'),
            'country': location_info.get('country', 'Unknown'),
            'organization': location_info.get('organization', 'Corporate Network'),
            'detectionMethod': 'network_analysis'
        }
    
    def _get_local_physical_location(self) -> str:
        """Get physical location of local machine"""
        try:
            # Try to get location from system timezone
            import time
            timezone = time.tzname[0]
            
            # Map common timezones to locations
            timezone_locations = {
                'PST': 'West Coast, USA',
                'EST': 'East Coast, USA',
                'CST': 'Central USA',
                'GMT': 'United Kingdom',
                'CET': 'Central Europe',
                'JST': 'Japan',
                'IST': 'India',
                'AEST': 'Australia'
            }
            
            if timezone in timezone_locations:
                return timezone_locations[timezone]
            
            # Fallback: try to get from public IP
            try:
                public_ip = self._get_public_ip()
                if public_ip:
                    location_data = self._query_geolocation_api(public_ip)
                    if location_data:
                        return f"{location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}"
            except:
                pass
            
            return 'Local Development Environment'
            
        except Exception as e:
            logger.error(f"Local location detection failed: {e}")
            return 'Unknown Location'
    
    def _get_public_ip(self) -> Optional[str]:
        """Get public IP address"""
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            return response.text.strip()
        except:
            return None
    
    def _query_geolocation_api(self, ip: str) -> Optional[Dict]:
        """Query geolocation API for IP location"""
        try:
            # Use free geolocation service
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return None
    
    def _get_local_city(self) -> str:
        """Get local city from various sources"""
        try:
            # Try geolocation of public IP
            public_ip = self._get_public_ip()
            if public_ip:
                location_data = self._query_geolocation_api(public_ip)
                if location_data:
                    return location_data.get('city', 'Unknown')
        except:
            pass
        
        return 'Local'
    
    def _get_local_country(self) -> str:
        """Get local country"""
        try:
            public_ip = self._get_public_ip()
            if public_ip:
                location_data = self._query_geolocation_api(public_ip)
                if location_data:
                    return location_data.get('country', 'Unknown')
        except:
            pass
        
        return 'Local'
    
    def _analyze_ip_patterns(self, ip: str) -> Dict[str, Any]:
        """Analyze IP patterns for location hints"""
        
        # Common corporate IP patterns
        if ip.startswith('192.168.1.'):
            return {'organization': 'Main Office Network', 'city': 'Headquarters'}
        elif ip.startswith('192.168.2.'):
            return {'organization': 'Branch Office Network', 'city': 'Branch Location'}
        elif ip.startswith('10.0.'):
            return {'organization': 'Data Center Network', 'city': 'Data Center'}
        elif ip.startswith('10.1.'):
            return {'organization': 'Production Network', 'city': 'Production Facility'}
        elif ip.startswith('172.16.'):
            return {'organization': 'DMZ Network', 'city': 'Edge Location'}
        
        return {'organization': 'Corporate Network', 'city': 'Unknown'}
    
    def _analyze_hostname_patterns(self, hostname: str) -> Dict[str, Any]:
        """Analyze hostname for location clues"""
        hostname_lower = hostname.lower()
        
        # Look for location indicators in hostname
        location_patterns = {
            'ny': 'New York',
            'la': 'Los Angeles', 
            'chicago': 'Chicago',
            'london': 'London',
            'tokyo': 'Tokyo',
            'mumbai': 'Mumbai',
            'singapore': 'Singapore',
            'sydney': 'Sydney',
            'dc': 'Data Center',
            'hq': 'Headquarters',
            'branch': 'Branch Office',
            'prod': 'Production',
            'dev': 'Development',
            'test': 'Test Environment'
        }
        
        for pattern, location in location_patterns.items():
            if pattern in hostname_lower:
                return {'city': location}
        
        return {}
    
    def _determine_network_zone(self, ip: str) -> str:
        """Determine network security zone"""
        if ip.startswith('192.168.1.'):
            return 'Corporate LAN'
        elif ip.startswith('192.168.2.'):
            return 'Guest Network'
        elif ip.startswith('10.0.'):
            return 'Data Center'
        elif ip.startswith('10.1.'):
            return 'Production Network'
        elif ip.startswith('172.16.'):
            return 'DMZ'
        elif ip.startswith('172.17.'):
            return 'Container Network'
        else:
            return 'Private Network'
    
    def _determine_physical_location_from_network(self, ip: str, hostname: str) -> str:
        """Determine physical location from network analysis"""
        
        # Combine IP and hostname analysis
        ip_hints = self._analyze_ip_patterns(ip)
        hostname_hints = self._analyze_hostname_patterns(hostname) if hostname else {}
        
        # Priority: hostname hints > IP hints > defaults
        if hostname_hints.get('city'):
            return hostname_hints['city']
        elif ip_hints.get('city'):
            return ip_hints['city']
        else:
            # Try to get from gateway/router info
            gateway_location = self._get_gateway_location()
            if gateway_location:
                return gateway_location
            
            return 'Corporate Office'
    
    def _get_gateway_location(self) -> Optional[str]:
        """Get location information from network gateway"""
        try:
            # Get default gateway
            result = subprocess.run(['route', 'print', '0.0.0.0'], 
                                  capture_output=True, text=True, timeout=10)
            
            # Parse gateway IP from route output
            for line in result.stdout.split('\n'):
                if '0.0.0.0' in line and 'Gateway' not in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        gateway_ip = parts[2]
                        
                        # Try to get hostname of gateway
                        try:
                            gateway_hostname = socket.gethostbyaddr(gateway_ip)[0]
                            # Analyze gateway hostname for location clues
                            return self._analyze_hostname_patterns(gateway_hostname).get('city', 'Corporate Network')
                        except:
                            pass
            
        except Exception as e:
            logger.debug(f"Gateway location detection failed: {e}")
        
        return None

# Global instance
location_detector = LocationDetector()
