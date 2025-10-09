#!/usr/bin/env python3
"""
AI-Powered Threat Scoring System
Uses GPT-3.5-Turbo to intelligently score threats with context awareness
Combines fast rule-based filtering with AI-powered analysis
"""

import logging
import os
import json
from typing import Dict, List, Any
from datetime import datetime
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class AIPoweredThreatScorer:
    """
    Hybrid threat scoring system:
    1. Fast rule-based pre-filtering (1-5ms)
    2. AI-powered intelligent scoring for suspicious events (200-500ms)
    Best of both worlds: Speed + Intelligence
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.use_ai_scoring = bool(self.openai_api_key)
        
        # Quick patterns for pre-filtering (fast)
        self.suspicious_indicators = {
            'attack_tools': ['nmap', 'sqlmap', 'metasploit', 'mimikatz', 'psexec'],
            'suspicious_commands': ['whoami', 'net user', 'netstat', 'tasklist'],
            'malicious_patterns': ['reverse shell', 'backdoor', 'privilege escalation'],
            'network_attacks': ['port scan', 'brute force', 'ddos'],
            'system_compromise': ['malware', 'ransomware', 'trojan', 'keylogger'],
            'auth_failures': ['failed login', 'authentication failed', 'access denied']
        }
        
        logger.info(f"AI-Powered Threat Scorer initialized (AI enabled: {self.use_ai_scoring})")
    
    async def score_threat(self, message: str, source: str, log_entry: Dict,
                          agent_id: str = None, hostname: str = None, 
                          ip_address: str = None) -> Dict[str, Any]:
        """
        Hybrid threat scoring:
        1. Quick rule-based check (fast)
        2. If suspicious, use AI for intelligent scoring
        """
        
        # STAGE 1: Fast pre-filtering (1-5ms)
        is_suspicious, quick_assessment = self._quick_rule_check(message, source, log_entry)
        
        if not is_suspicious:
            # Benign - no need for AI
            return {
                'threat_score': 0.0,
                'threat_type': 'benign',
                'severity': 'info',
                'indicators': [],
                'confidence': 1.0,
                'analysis_method': 'rule_based_benign',
                'processing_time_ms': '<5ms'
            }
        
        # STAGE 2: AI-Powered Intelligent Scoring (200-500ms)
        if self.use_ai_scoring:
            logger.info(f"Suspicious log detected - requesting AI scoring")
            ai_assessment = await self._ai_intelligent_scoring(
                message, source, log_entry, agent_id, hostname, ip_address, quick_assessment
            )
            return ai_assessment
        else:
            # Fallback to enhanced rule-based scoring if no AI
            logger.warning("AI scoring not available - using fallback rule-based scoring")
            return self._fallback_rule_scoring(quick_assessment, message, hostname)
    
    def _quick_rule_check(self, message: str, source: str, log_entry: Dict) -> tuple:
        """
        Fast rule-based pre-filter (1-5ms)
        Returns: (is_suspicious, quick_assessment)
        """
        message_lower = message.lower()
        source_lower = source.lower()
        
        matched_categories = []
        indicators = []
        
        # Quick pattern matching
        for category, patterns in self.suspicious_indicators.items():
            for pattern in patterns:
                if pattern in message_lower:
                    matched_categories.append(category)
                    indicators.append(pattern)
                    break  # One match per category is enough for pre-filter
        
        # Check container context
        if log_entry.get('container_context') or 'attackcontainer' in source_lower:
            matched_categories.append('container_attack')
            indicators.append('container_context')
        
        is_suspicious = len(matched_categories) > 0
        
        return is_suspicious, {
            'matched_categories': matched_categories,
            'indicators': indicators,
            'indicator_count': len(indicators)
        }
    
    async def _ai_intelligent_scoring(self, message: str, source: str, log_entry: Dict,
                                     agent_id: str, hostname: str, ip_address: str,
                                     quick_assessment: Dict) -> Dict[str, Any]:
        """
        Use AI (GPT-3.5-Turbo) for intelligent threat scoring
        AI considers: context, asset criticality, time, correlation, sophistication
        """
        
        start_time = datetime.now()
        
        # Prepare context for AI
        context = {
            'message': message,
            'source': source,
            'hostname': hostname or 'unknown',
            'ip_address': ip_address or 'unknown',
            'timestamp': log_entry.get('timestamp', datetime.now().isoformat()),
            'log_level': log_entry.get('level', 'unknown'),
            'matched_indicators': quick_assessment['indicators'],
            'matched_categories': quick_assessment['matched_categories'],
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'day_of_week': datetime.now().strftime('%A'),
            'hour': datetime.now().hour
        }
        
        # Create intelligent AI prompt
        prompt = f"""You are an expert cybersecurity analyst scoring a potential security threat.

CONTEXT:
- Log Message: {context['message'][:500]}
- Source: {context['source']}
- Hostname: {context['hostname']}
- IP Address: {context['ip_address']}
- Timestamp: {context['timestamp']}
- Current Time: {context['current_time']} ({context['day_of_week']}, {context['hour']}:00)
- Log Level: {context['log_level']}

PRELIMINARY ANALYSIS:
- Matched Categories: {', '.join(context['matched_categories'])}
- Indicators Detected: {', '.join(context['matched_indicators'])}

SCORING INSTRUCTIONS:
1. Analyze the threat considering:
   - Asset criticality (domain controllers, database servers are more critical)
   - Time context (off-hours activity is more suspicious)
   - Attack sophistication
   - False positive likelihood
   - Correlation potential (is this part of a larger attack?)

2. Provide a threat score from 0.0 to 1.0:
   - 0.0-0.2: Benign/False Positive
   - 0.2-0.4: Low threat (routine investigation)
   - 0.4-0.6: Medium threat (prioritized investigation)
   - 0.6-0.8: High threat (urgent investigation)
   - 0.8-1.0: Critical threat (immediate action)

3. Consider severity levels:
   - info: No real threat
   - low: Minor security concern
   - medium: Needs investigation
   - high: Urgent security issue
   - critical: Active compromise or severe threat

IMPORTANT: 
- Be aggressive in detection (better false positive than missing real threat)
- Consider context heavily (same activity at 3 AM vs 3 PM has different risk)
- Domain controllers, database servers warrant higher scores
- Multiple correlated indicators increase severity

Respond with ONLY valid JSON:
{{
  "threat_score": <float 0.0-1.0>,
  "severity": "<info|low|medium|high|critical>",
  "threat_type": "<specific threat type>",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<brief explanation why this score>",
  "indicators": ["<list of specific threat indicators>"],
  "recommended_action": "<what should analyst do>",
  "false_positive_likelihood": "<low|medium|high>",
  "asset_risk_factor": <float 1.0-2.0>,
  "temporal_risk_factor": <float 1.0-1.5>,
  "sophistication_level": "<low|medium|high|advanced>"
}}"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert cybersecurity analyst. Always respond with valid JSON only. Be aggressive in threat detection - better to investigate a false positive than miss a real threat."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.3,  # Lower temperature for consistent scoring
                        "max_tokens": 800
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # Remove markdown if present
                        if '```json' in content:
                            content = content.split('```json')[1].split('```')[0].strip()
                        elif '```' in content:
                            content = content.split('```')[1].split('```')[0].strip()
                        
                        ai_score = json.loads(content)
                        
                        # Calculate processing time
                        processing_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        return {
                            'threat_score': ai_score.get('threat_score', 0.5),
                            'threat_type': ai_score.get('threat_type', 'unknown'),
                            'severity': ai_score.get('severity', 'medium'),
                            'indicators': ai_score.get('indicators', context['matched_indicators']),
                            'confidence': ai_score.get('confidence', 0.7),
                            'reasoning': ai_score.get('reasoning', 'AI analysis completed'),
                            'recommended_action': ai_score.get('recommended_action', 'Investigate this event'),
                            'false_positive_likelihood': ai_score.get('false_positive_likelihood', 'medium'),
                            'asset_risk_factor': ai_score.get('asset_risk_factor', 1.0),
                            'temporal_risk_factor': ai_score.get('temporal_risk_factor', 1.0),
                            'sophistication_level': ai_score.get('sophistication_level', 'medium'),
                            'analysis_method': 'ai_powered_gpt3.5',
                            'processing_time_ms': f'{processing_time:.0f}ms',
                            'matched_categories': context['matched_categories']
                        }
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return self._fallback_rule_scoring(quick_assessment, message, hostname)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._fallback_rule_scoring(quick_assessment, message, hostname)
        
        except Exception as e:
            logger.error(f"AI scoring failed: {e}")
            return self._fallback_rule_scoring(quick_assessment, message, hostname)
    
    def _fallback_rule_scoring(self, quick_assessment: Dict, message: str, 
                               hostname: str) -> Dict[str, Any]:
        """
        Fallback to rule-based scoring if AI is unavailable
        Uses weighted maximum approach from enhanced_threat_scorer
        """
        
        # Base scores for each category
        category_scores = {
            'attack_tools': 0.7,
            'suspicious_commands': 0.4,
            'malicious_patterns': 0.8,
            'network_attacks': 0.6,
            'system_compromise': 0.9,
            'auth_failures': 0.5,
            'container_attack': 0.5
        }
        
        matched_categories = quick_assessment['matched_categories']
        
        if not matched_categories:
            return {
                'threat_score': 0.0,
                'threat_type': 'benign',
                'severity': 'info',
                'indicators': [],
                'confidence': 1.0,
                'analysis_method': 'rule_based_fallback'
            }
        
        # Weighted maximum scoring
        base_scores = [category_scores.get(cat, 0.4) for cat in matched_categories]
        max_score = max(base_scores)
        
        # Correlation boost
        if len(matched_categories) > 1:
            correlation_boost = (len(matched_categories) - 1) * (max_score * 0.1)
            threat_score = min(max_score + correlation_boost, 1.0)
        else:
            threat_score = max_score
        
        # Determine threat type
        threat_type_map = {
            'attack_tools': 'attack_tool_usage',
            'suspicious_commands': 'reconnaissance',
            'malicious_patterns': 'active_attack',
            'network_attacks': 'network_attack',
            'system_compromise': 'system_compromise',
            'auth_failures': 'authentication_attack',
            'container_attack': 'container_attack'
        }
        
        primary_category = max(matched_categories, key=lambda x: category_scores.get(x, 0.4))
        threat_type = threat_type_map.get(primary_category, 'unknown')
        
        # Calculate severity
        if threat_score >= 0.85:
            severity = 'critical'
        elif threat_score >= 0.65:
            severity = 'high'
        elif threat_score >= 0.45:
            severity = 'medium'
        elif threat_score >= 0.25:
            severity = 'low'
        else:
            severity = 'info'
        
        return {
            'threat_score': round(threat_score, 3),
            'threat_type': threat_type,
            'severity': severity,
            'indicators': quick_assessment['indicators'],
            'confidence': 0.8,  # Rule-based has good confidence
            'reasoning': f"Rule-based detection: {len(matched_categories)} suspicious categories matched",
            'analysis_method': 'rule_based_fallback',
            'matched_categories': matched_categories
        }


# Global instance
ai_powered_threat_scorer = AIPoweredThreatScorer()

