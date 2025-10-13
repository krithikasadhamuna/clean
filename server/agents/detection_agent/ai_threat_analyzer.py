#!/usr/bin/env python3
"""
AI Threat Analyzer - Full AI-Powered Detection
Uses cybersec-ai LLM for intelligent threat analysis and decision making
"""

import os
import json
import logging
import requests
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio

from .real_threat_detector import real_threat_detector

logger = logging.getLogger(__name__)

class AIThreatAnalyzer:
    """AI-powered threat analysis using cybersec-ai LLM"""
    
    def __init__(self, db_path: str = "soc_database.db"):
        self.db_path = db_path
        self.config = self._load_config()
        
        # AI model configuration (use OpenAI GPT-3.5-turbo)
        self.llm_config = self.config['llm']
        self.api_key = self.llm_config.get('api_key') or os.getenv('OPENAI_API_KEY')
        
        # AI threat knowledge base
        self.threat_intelligence = {}
        self.attack_patterns = {}
        self.false_positive_patterns = {}
        
        # Learning parameters
        self.confidence_threshold = 0.7
        self.ai_enabled = True
        
        logger.info("AI Threat Analyzer initialized with OpenAI GPT-3.5-turbo intelligence")
    
    def _load_config(self) -> Dict:
        """Load AI configuration dynamically"""
        try:
            # Try to load from server config first
            import sys
            from pathlib import Path
            server_path = Path(__file__).parent.parent.parent / "log_forwarding"
            sys.path.insert(0, str(server_path))
            
            from shared.config import config
            server_config = config.load_server_config()
            llm_config = server_config.get('llm', {})
            
            if llm_config:
                return {
                    'llm': {
                        'provider': llm_config.get('provider', 'openai'),
                        'model': llm_config.get('model', 'gpt-3.5-turbo'),
                        'api_key': llm_config.get('api_key', ''),
                        'temperature': llm_config.get('temperature', 0.2),
                        'max_tokens': llm_config.get('max_tokens', 1024)
                    }
                }
        except Exception as e:
            logger.debug(f"Could not load server config: {e}")
        
        # Fallback to auto-detected config
        return self._generate_dynamic_ai_config()
    
    def _generate_dynamic_ai_config(self) -> Dict:
        """Generate dynamic AI configuration"""
        # Test if Ollama is available
        ollama_available = self._test_ollama_availability()
        
        # Prefer OpenAI, fallback to Ollama, then mock
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if openai_key:
            return {
                'llm': {
                    'provider': 'openai',
                    'model': 'gpt-3.5-turbo',
                    'api_key': openai_key,
                    'temperature': 0.2,
                    'max_tokens': 1024,
                    'available': True
                }
            }
        elif ollama_available:
            return {
                'llm': {
                    'provider': 'ollama',
                    'endpoint': 'http://localhost:11434',
                    'model': 'llama2',
                    'temperature': 0.2,
                    'max_tokens': 1024,
                    'available': ollama_available
                }
            }
        else:
            return {
                'llm': {
                    'provider': 'mock',
                    'model': 'mock-model',
                    'temperature': 0.2,
                    'max_tokens': 1024,
                    'available': False
                }
            }
    
    def _test_ollama_availability(self) -> bool:
        """Test if Ollama is available"""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=3)
            return response.status_code == 200
        except:
            return False
    
    async def analyze_threat_with_ai(self, detection_data: Dict, context: Dict) -> Dict:
        """Analyze threat using AI intelligence"""
        import time
        
        if not self.ai_enabled:
            return self._fallback_analysis(detection_data)
        
        try:
            from agents.gpt_interaction_logger import gpt_logger
            
            start_time = time.time()
            
            # Build comprehensive analysis prompt
            prompt = self._build_threat_analysis_prompt(detection_data, context)
            
            # Get AI analysis
            ai_response = await self._query_cybersec_ai(prompt)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse AI analysis
            ai_analysis = self._parse_ai_analysis(ai_response)
            
            # Enhance with traditional ML
            ml_analysis = self._get_ml_analysis(detection_data)
            
            # Combine AI and ML insights
            final_analysis = self._combine_analyses(ai_analysis, ml_analysis, detection_data)
            
            # Log success
            await gpt_logger.log_success(
                interaction_type="threat_analysis",
                prompt=prompt,
                response=str(ai_response)[:5000],
                response_time_ms=response_time_ms,
                user_request=f"Analyze detection from {detection_data.get('source', 'unknown')}",
                result_summary=f"Threat: {final_analysis.get('is_threat', False)}, Severity: {final_analysis.get('severity', 'unknown')}",
                component="ai_threat_analyzer",
                tokens_used=1200
            )
            
            return final_analysis
            
        except Exception as e:
            logger.error(f"AI threat analysis failed: {e}")
            
            # Log failure
            try:
                from agents.gpt_interaction_logger import gpt_logger
                await gpt_logger.log_failure(
                    interaction_type="threat_analysis",
                    prompt=prompt if 'prompt' in locals() else "",
                    error_message=str(e),
                    response_time_ms=int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0,
                    user_request=f"Analyze detection from {detection_data.get('source', 'unknown')}",
                    component="ai_threat_analyzer"
                )
            except:
                pass
            
            return self._fallback_analysis(detection_data)
    
    def _build_threat_analysis_prompt(self, detection_data: Dict, context: Dict) -> str:
        """Build comprehensive threat analysis prompt"""
        
        # Get historical context
        similar_threats = self._get_similar_threats(detection_data)
        recent_activity = context.get('recent_activity', [])
        
        # Extract enhanced context information
        agent_info = context.get('agent_info', {})
        log_context = context.get('log_context', {})
        
        prompt = f"""
You are an elite cybersecurity analyst with deep knowledge of MITRE ATT&CK and threat hunting.

SYSTEM INFORMATION:
- Hostname: {agent_info.get('hostname', 'unknown')}
- Platform: {agent_info.get('platform', 'unknown')}
- IP Address: {agent_info.get('ip_address', 'unknown')}
- Agent ID: {context.get('agent_id', 'unknown')}

LOG DETAILS TO ANALYZE:
- Full Message: "{log_context.get('full_message', detection_data.get('message', 'No message'))}"
- Log Source: {log_context.get('log_source', 'unknown')}
- Log Level: {log_context.get('log_level', 'unknown')}
- Process: {log_context.get('process', 'unknown')}
- Command Line: {log_context.get('command_line', 'unknown')}
- User: {log_context.get('user', 'unknown')}
- PID: {log_context.get('pid', 'unknown')}
- Timestamp: {log_context.get('timestamp', 'unknown')}

ADDITIONAL CONTEXT:
{json.dumps(log_context.get('additional_fields', {}), indent=2)}

THREAT CLASSIFICATION GUIDELINES:
- "malware": Malicious software, trojans, viruses, ransomware, suspicious executables
- "apt": Advanced persistent threats, nation-state actors, sophisticated campaigns
- "insider": Internal threats, privilege abuse, unauthorized access by employees
- "lateral_movement": Network propagation, credential theft, remote access attempts  
- "false_positive": Legitimate activity misclassified, normal operations
- "unknown": Insufficient data for classification (avoid this unless truly unclear)

SPECIFIC INDICATORS TO LOOK FOR:
- PowerShell with encoded commands, suspicious scripts → "malware"
- Connections to known C2 servers, APT TTPs → "apt" 
- Off-hours admin activity, privilege escalation → "insider"
- SMB/RDP lateral connections, credential dumping → "lateral_movement"
- Normal software updates, scheduled tasks → "false_positive"

RECENT ACTIVITY (Last 1 hour):
{json.dumps(recent_activity[-5:], indent=2) if recent_activity else 'No recent activity'}

SIMILAR HISTORICAL THREATS:
{json.dumps(similar_threats[:3], indent=2) if similar_threats else 'No similar threats found'}

CRITICAL ANALYSIS REQUIREMENTS:
1. Analyze the FULL log message for threat indicators
2. Consider the process, command line, and user context
3. Map to specific MITRE ATT&CK techniques
4. Classify based on actual threat behavior, not generic patterns
5. Provide high confidence (>0.7) for clear threats, lower for ambiguous cases

Respond with JSON format:
{{
    "threat_classification": "malware|apt|insider|lateral_movement|false_positive|unknown", (these are just recommendations, you can suggest more threat classifications based on the log message and context)
    "confidence_level": 0.85, (this is just a recommendation, you can suggest more confidence levels based on the log message and context)
    "threat_severity": "low|medium|high|critical", (these are just recommendations, you can suggest more threat severities based on the log message and context)
    "mitre_techniques": ["T1059.001", "T1055"], (these are just recommendations, you can suggest more MITRE techniques based on the log message and context)
    "attack_phase": "reconnaissance|initial_access|execution|persistence|privilege_escalation|defense_evasion|credential_access|discovery|lateral_movement|collection|exfiltration|impact", (these are just recommendations, you can suggest more attack phases based on the log message and context)
    "threat_actor_profile": {{
        "sophistication": "low|medium|high|nation_state",
        "likely_group": "APT29|Lazarus|Emotet|Unknown", (these are just recommendations, you can suggest more likely groups based on the log message and context)
        "motivation": "espionage|financial|disruption|testing" (these are just recommendations, you can suggest more motivations based on the log message and context)
    }},
    "impact_assessment": {{
        "data_risk": "low|medium|high|critical", (these are just recommendations, you can suggest more data risks based on the log message and context)
        "system_risk": "low|medium|high|critical", (these are just recommendations, you can suggest more system risks based on the log message and context)
        "business_impact": "minimal|moderate|significant|severe" (these are just recommendations, you can suggest more business impacts based on the log message and context)
    }},
    "false_positive_likelihood": 0.15, (this is just a recommendation, you can suggest more false positive likelihoods based on the log message and context)
    "recommended_actions": [
        "isolate_endpoint", (these are just recommendations, you can suggest more actions based on the log message and context)
        "collect_memory_dump",  (these are just recommendations, you can suggest more actions based on the log message and context)
        "analyze_network_traffic", (these are just recommendations, you can suggest more actions based on the log message and context)
        "check_lateral_movement"   (these are just recommendations, you can suggest more actions based on the log message and context)
    ],
    "reasoning": "Detailed explanation based on the specific log message and context along with the commands or behaviours exhibited. please explain thoroughly",
    "indicators_of_compromise": ["EXTRACT REAL IOCs FROM THE LOG - file paths, IPs, domains, process names, hashes, registry keys, commands. If none found, return empty array []"],
    "hunting_queries": ["Create actual hunting queries based on the specific IOCs and behaviors in THIS log"],
    "soc_analyst_report": "A professional, comprehensive report for SOC analysts and CISOs. Write this in a narrative format that explains WHAT happened, WHY it's dangerous, WHAT the business impact is, and WHAT actions to take. Make it clear, concise, and actionable. Include threat intelligence context, attack timeline, and specific technical details that help analysts investigate. This should be 3-5 paragraphs that a CISO could read and immediately understand the threat and required response."
}}

CRITICAL INSTRUCTIONS:
1. Extract REAL indicators_of_compromise from the actual log content above - do NOT use placeholder values
2. Look for: file paths, IP addresses, domains, process names, commands, registry keys, URLs
3. If no IOCs are present in the log, return an empty array: "indicators_of_compromise": []
4. Create hunting_queries based on the ACTUAL IOCs and behaviors you found
5. Base your classification on the actual log content and context provided. Be specific in your reasoning."""
        
        return prompt
    
    async def correlate_threats_with_ai(self, threat_events: List[Dict], 
                                      time_window: int = 3600) -> Dict:
        """AI-powered threat correlation across multiple events"""
        
        if not self.ai_enabled or len(threat_events) < 2:
            return {'correlation_found': False, 'reason': 'Insufficient data or AI disabled'}
        
        try:
            prompt = f"""
You are analyzing multiple security events for potential correlation and attack campaigns.

SECURITY EVENTS (Last {time_window} seconds):
{json.dumps(threat_events, indent=2)}

CORRELATION ANALYSIS REQUIRED:
1. Are these events part of a coordinated attack?
2. What is the attack progression/kill chain?
3. Which events are related vs. independent?
4. What is the overall campaign objective?
5. Threat actor attribution analysis
6. Predicted next attack steps

Consider:
- Timing patterns and sequences
- Target relationships
- Technique progression
- Infrastructure overlap
- Behavioral consistency

Respond with JSON:
{{
    "correlation_found": true,
    "campaign_name": "Suspected APT Campaign Alpha",
    "confidence_level": 0.92,
    "attack_progression": [
        {{
            "phase": "initial_access",
            "events": ["event_id_1", "event_id_2"],
            "techniques": ["T1566.001"]
        }}
    ],
    "threat_actor_assessment": {{
        "likely_group": "APT29",
        "confidence": 0.75,
        "attribution_factors": ["technique_overlap", "infrastructure_reuse"]
    }},
    "campaign_objective": "credential_harvesting",
    "predicted_next_steps": ["lateral_movement", "privilege_escalation"],
    "recommended_response": [
        "activate_incident_response",
        "isolate_affected_systems",
        "hunt_for_additional_compromises"
    ],
    "timeline_analysis": "Events show clear progression from spearphishing to code execution",
    "risk_assessment": "high"
}}
"""
            
            ai_response = await self._query_cybersec_ai(prompt)
            correlation = self._parse_correlation_analysis(ai_response)
            
            return correlation
            
        except Exception as e:
            logger.error(f"AI threat correlation failed: {e}")
            return {'correlation_found': False, 'error': str(e)}
    
    async def generate_threat_intelligence(self, threat_data: Dict) -> Dict:
        """Generate actionable threat intelligence using AI"""
        
        if not self.ai_enabled:
            return {'intelligence_available': False}
        
        try:
            prompt = f"""
Generate actionable threat intelligence based on this security event:

THREAT DATA:
{json.dumps(threat_data, indent=2)}

INTELLIGENCE REQUIREMENTS:
1. Threat attribution and profiling
2. Infrastructure analysis (IPs, domains, hashes)
3. Behavioral pattern analysis
4. Defense recommendations
5. Hunting opportunities
6. Similar attack campaigns

Generate comprehensive threat intelligence report in JSON:
{{
    "threat_profile": {{
        "name": "Cobalt Strike Beacon Activity",
        "family": "post_exploitation_framework",
        "first_seen": "2024-01-15",
        "last_seen": "2024-09-24"
    }},
    "infrastructure_analysis": {{
        "command_control_servers": ["192.0.2.1", "malicious.example.com"],
        "infrastructure_confidence": 0.85,
        "hosting_analysis": "Bulletproof hosting provider"
    }},
    "behavioral_patterns": [
        "Uses living-off-the-land techniques",
        "Employs process hollowing for stealth",
        "Communicates via HTTPS on port 443"
    ],
    "defense_recommendations": [
        "Block C2 domains at DNS level",
        "Monitor for process injection techniques",
        "Implement application whitelisting"
    ],
    "hunting_opportunities": [
        "Search for similar process injection patterns",
        "Hunt for network beaconing behavior",
        "Look for persistence mechanisms"
    ],
    "similar_campaigns": [
        {{
            "name": "APT29 Campaign 2024",
            "similarity_score": 0.78,
            "shared_ttps": ["T1055", "T1071.001"]
        }}
    ],
    "yara_rules": "rule Cobalt_Strike_Beacon {{ ... }}",
    "sigma_rules": "title: Cobalt Strike Process Injection\\ndetection: ...",
    "confidence_assessment": 0.88
}}
"""
            
            ai_response = await self._query_cybersec_ai(prompt)
            intelligence = self._parse_threat_intelligence(ai_response)
            
            # Store intelligence for future reference
            self._store_threat_intelligence(threat_data, intelligence)
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Threat intelligence generation failed: {e}")
            return {'intelligence_available': False, 'error': str(e)}
    
    async def adaptive_threshold_tuning(self, detection_history: List[Dict]) -> Dict:
        """AI-powered adaptive threshold tuning based on environment"""
        
        if not self.ai_enabled or len(detection_history) < 10:
            return {'tuning_applied': False, 'reason': 'Insufficient data'}
        
        try:
            # Analyze detection patterns
            false_positives = [d for d in detection_history if d.get('false_positive', False)]
            true_positives = [d for d in detection_history if not d.get('false_positive', False)]
            
            prompt = f"""
Analyze detection patterns and recommend threshold adjustments:

DETECTION HISTORY SUMMARY:
- Total Detections: {len(detection_history)}
- True Positives: {len(true_positives)}
- False Positives: {len(false_positives)}
- False Positive Rate: {len(false_positives)/len(detection_history)*100:.1f}%

RECENT FALSE POSITIVES:
{json.dumps(false_positives[-5:], indent=2)}

RECENT TRUE POSITIVES:
{json.dumps(true_positives[-5:], indent=2)}

CURRENT THRESHOLDS:
- Anomaly Score: 0.7
- Malware Confidence: 0.8
- Behavioral Risk: 0.6
- Network Anomaly: 0.75

OPTIMIZATION GOALS:
1. Reduce false positive rate to <5%
2. Maintain 95%+ true positive detection
3. Adapt to environment baseline
4. Consider business impact

Recommend threshold adjustments in JSON:
{{
    "threshold_adjustments": {{
        "anomaly_score": 0.75,
        "malware_confidence": 0.85,
        "behavioral_risk": 0.65,
        "network_anomaly": 0.8
    }},
    "confidence_level": 0.82,
    "expected_improvements": {{
        "false_positive_reduction": "15%",
        "detection_accuracy": "97%"
    }},
    "reasoning": "Analysis shows current thresholds are too sensitive for this environment",
    "monitoring_recommendations": [
        "Monitor FP rate for 7 days",
        "Adjust if FP rate exceeds 3%"
    ]
}}
"""
            
            ai_response = await self._query_cybersec_ai(prompt)
            tuning = self._parse_threshold_tuning(ai_response)
            
            # Apply tuning if confidence is high enough
            if tuning.get('confidence_level', 0) > self.confidence_threshold:
                self._apply_threshold_tuning(tuning)
            
            return tuning
            
        except Exception as e:
            logger.error(f"Adaptive threshold tuning failed: {e}")
            return {'tuning_applied': False, 'error': str(e)}
    
    async def _query_cybersec_ai(self, prompt: str) -> str:
        """Query OpenAI GPT-3.5-turbo for real AI analysis"""
        
        try:
            # Use new OpenAI API (v1.0+)
            from langchain_openai import ChatOpenAI
            
            # Initialize ChatOpenAI with API key
            llm = ChatOpenAI(
                model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                temperature=self.llm_config.get('temperature', 0.2),
                max_tokens=self.llm_config.get('max_tokens', 2048),
                api_key=self.api_key
            )
            
            # Create system + user message format
            from langchain.schema import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content="You are a cybersecurity expert AI assistant specializing in threat analysis and detection."),
                HumanMessage(content=prompt)
            ]
            
            # Make async API call
            response = await llm.ainvoke(messages)
            
            return response.content
            
        except ImportError:
            # Fallback to langchain OpenAI if openai package not available
            try:
                from langchain_openai import ChatOpenAI
                
                # Get API key from config or environment - NO HARDCODED FALLBACK
                api_key = self.api_key or os.getenv("OPENAI_API_KEY")
                
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")
                
                llm = ChatOpenAI(
                    model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                    temperature=self.llm_config.get('temperature', 0.2),
                    max_tokens=self.llm_config.get('max_tokens', 2048),
                    openai_api_key=api_key
                )
                
                response = await llm.ainvoke(prompt)
                return response.content
                
            except Exception as e:
                logger.error(f"LangChain OpenAI query failed: {e}")
                return ""
                
        except Exception as e:
            logger.error(f"OpenAI GPT-3.5-turbo query failed: {e}")
            return ""
    
    def _parse_ai_analysis(self, ai_response: str) -> Dict:
        """Parse AI threat analysis response"""
        
        try:
            if '{' in ai_response:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                json_str = ai_response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"AI analysis parsing failed: {e}")
        
        return {
            'threat_classification': 'unknown',
            'confidence_level': 0.5,
            'threat_severity': 'medium',
            'reasoning': 'AI analysis parsing failed'
        }
    
    def _parse_correlation_analysis(self, ai_response: str) -> Dict:
        """Parse AI correlation analysis"""
        
        try:
            if '{' in ai_response:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                json_str = ai_response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Correlation analysis parsing failed: {e}")
        
        return {'correlation_found': False, 'error': 'Parsing failed'}
    
    def _parse_threat_intelligence(self, ai_response: str) -> Dict:
        """Parse threat intelligence response"""
        
        try:
            if '{' in ai_response:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                json_str = ai_response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Threat intelligence parsing failed: {e}")
        
        return {'intelligence_available': False, 'error': 'Parsing failed'}
    
    def _parse_threshold_tuning(self, ai_response: str) -> Dict:
        """Parse threshold tuning recommendations"""
        
        try:
            if '{' in ai_response:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                json_str = ai_response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Threshold tuning parsing failed: {e}")
        
        return {'tuning_applied': False, 'error': 'Parsing failed'}
    
    def _get_ml_analysis(self, detection_data: Dict) -> Dict:
        """Get traditional ML analysis from existing detector"""
        
        try:
            # Use existing ML models for comparison
            if detection_data.get('type') == 'process_anomaly':
                ml_result = real_threat_detector.detect_process_anomaly(detection_data)
            elif detection_data.get('type') == 'file_threat':
                ml_result = real_threat_detector.detect_file_threat(detection_data)
            else:
                ml_result = {'threat_detected': False, 'confidence': 0.5}
            
            return {
                'ml_threat_detected': ml_result.get('threat_detected', False),
                'ml_confidence': ml_result.get('final_score', 0.5),
                'ml_reasoning': 'Traditional ML analysis'
            }
            
        except Exception as e:
            logger.error(f"ML analysis failed: {e}")
            return {'ml_threat_detected': False, 'ml_confidence': 0.0}
    
    def _combine_analyses(self, ai_analysis: Dict, ml_analysis: Dict, 
                         detection_data: Dict) -> Dict:
        """Combine AI and ML analyses for final decision"""
        
        # Weight AI analysis higher (70%) vs ML (30%)
        ai_weight = 0.7
        ml_weight = 0.3
        
        ai_confidence = ai_analysis.get('confidence_level', 0.5)
        ml_confidence = ml_analysis.get('ml_confidence', 0.5)
        
        combined_confidence = (ai_confidence * ai_weight) + (ml_confidence * ml_weight)
        
        # Final threat determination
        ai_threat = ai_analysis.get('threat_classification') not in ['false_positive', 'unknown']
        ml_threat = ml_analysis.get('ml_threat_detected', False)
        
        final_threat_detected = ai_threat or (ml_threat and combined_confidence > 0.6)
        
        return {
            'ai_enhanced': True,
            'final_threat_detected': final_threat_detected,
            'combined_confidence': combined_confidence,
            'threat_classification': ai_analysis.get('threat_classification', 'unknown'),
            'threat_severity': ai_analysis.get('threat_severity', 'medium'),
            'mitre_techniques': ai_analysis.get('mitre_techniques', []),
            'attack_phase': ai_analysis.get('attack_phase', 'unknown'),
            'false_positive_likelihood': ai_analysis.get('false_positive_likelihood', 0.5),
            'recommended_actions': ai_analysis.get('recommended_actions', []),
            'ai_reasoning': ai_analysis.get('reasoning', 'No reasoning provided'),
            'ml_contribution': ml_analysis,
            'indicators_of_compromise': ai_analysis.get('indicators_of_compromise', []),
            'hunting_queries': ai_analysis.get('hunting_queries', []),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_similar_threats(self, detection_data: Dict, limit: int = 5) -> List[Dict]:
        """Get similar historical threats for context"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple similarity based on detection type
            detection_type = detection_data.get('type', 'unknown')
            
            cursor.execute('''
                SELECT ml_results FROM detection_results 
                WHERE threat_type = ? 
                ORDER BY detected_at DESC 
                LIMIT ?
            ''', (detection_type, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            similar_threats = []
            for result in results:
                try:
                    threat_data = json.loads(result[0])
                    similar_threats.append(threat_data)
                except:
                    continue
            
            return similar_threats
            
        except Exception as e:
            logger.error(f"Failed to get similar threats: {e}")
            return []
    
    def _store_threat_intelligence(self, threat_data: Dict, intelligence: Dict):
        """Store generated threat intelligence"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create threat_intelligence table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS threat_intelligence (
                    id TEXT PRIMARY KEY,
                    threat_data TEXT,
                    intelligence_data TEXT,
                    created_at TEXT,
                    confidence_level REAL
                )
            ''')
            
            intel_id = f"intel-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            cursor.execute('''
                INSERT INTO threat_intelligence 
                (id, threat_data, intelligence_data, created_at, confidence_level)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                intel_id,
                json.dumps(threat_data),
                json.dumps(intelligence),
                datetime.now().isoformat(),
                intelligence.get('confidence_assessment', 0.5)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store threat intelligence: {e}")
    
    def _apply_threshold_tuning(self, tuning: Dict):
        """Apply AI-recommended threshold tuning"""
        
        try:
            adjustments = tuning.get('threshold_adjustments', {})
            
            # Update real threat detector thresholds
            for threshold_name, new_value in adjustments.items():
                if hasattr(real_threat_detector, 'thresholds') and threshold_name in real_threat_detector.thresholds:
                    old_value = real_threat_detector.thresholds[threshold_name]
                    real_threat_detector.thresholds[threshold_name] = new_value
                    logger.info(f"Threshold tuned: {threshold_name} {old_value} -> {new_value}")
            
            logger.info("AI threshold tuning applied")
            
        except Exception as e:
            logger.error(f"Threshold tuning application failed: {e}")
    
    def _fallback_analysis(self, detection_data: Dict) -> Dict:
        """Fallback analysis when AI is unavailable"""
        
        return {
            'ai_enhanced': False,
            'final_threat_detected': detection_data.get('threat_detected', False),
            'combined_confidence': 0.5,
            'threat_classification': 'unknown',
            'threat_severity': 'medium',
            'reasoning': 'AI analysis unavailable - using fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def enable_ai(self):
        """Enable AI analysis"""
        self.ai_enabled = True
        logger.info("AI threat analysis enabled")
    
    def disable_ai(self):
        """Disable AI analysis"""
        self.ai_enabled = False
        logger.info("AI threat analysis disabled")
    
    def get_ai_status(self) -> Dict:
        """Get AI analyzer status"""
        return {
            'ai_enabled': self.ai_enabled,
            'ai_model': self.ollama_model,
            'confidence_threshold': self.confidence_threshold,
            'threat_intelligence_count': len(self.threat_intelligence),
            'attack_patterns_count': len(self.attack_patterns)
        }

# Global AI threat analyzer instance
ai_threat_analyzer = AIThreatAnalyzer()
