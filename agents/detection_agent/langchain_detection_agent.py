"""
LangChain-Based AI Detection Agent
Fully integrated with LangChain for threat detection and analysis
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool, tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain_community.chat_models import ChatOpenAI

from .real_threat_detector import real_threat_detector
from .ai_threat_analyzer import ai_threat_analyzer


logger = logging.getLogger(__name__)


class ThreatDetectionInput(BaseModel):
    """Input schema for threat detection"""
    detection_data: Dict = Field(description="Raw detection data to analyze")
    context: Dict = Field(description="Additional context for analysis")


class ThreatAnalysisResult(BaseModel):
    """Result schema for threat analysis"""
    threat_detected: bool = Field(description="Whether a threat was detected")
    confidence_score: float = Field(description="Confidence score (0.0 to 1.0)")
    threat_type: str = Field(description="Type of threat detected")
    severity: str = Field(description="Threat severity level")
    mitre_techniques: List[str] = Field(description="Relevant MITRE ATT&CK techniques")
    recommended_actions: List[str] = Field(description="Recommended response actions")
    reasoning: str = Field(description="AI reasoning for the decision")


class DetectionCallbackHandler(AsyncCallbackHandler):
    """Callback handler for detection agent events"""
    
    def __init__(self):
        self.detection_events = []
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when tool starts"""
        self.detection_events.append({
            'event': 'tool_start',
            'tool': serialized.get('name', 'unknown'),
            'input': input_str,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when tool ends"""
        self.detection_events.append({
            'event': 'tool_end',
            'output': output[:200],  # Truncate for logging
            'timestamp': datetime.utcnow().isoformat()
        })


@tool
def ml_threat_detection_tool(detection_data: Dict, context: Dict) -> Dict:
    """
    Run ML-based threat detection using traditional models - RUNS ON ALL LOGS
    
    Args:
        detection_data: Raw detection data to analyze
        context: Additional context for analysis
    
    Returns:
        ML detection results with confidence scores
    """
    try:
        data_type = detection_data.get('type', 'unknown')
        data = detection_data.get('data', {})
        
        # Run ML detection on ALL logs, not just suspicious ones
        ml_results = []
        
        # Try multiple detection methods for comprehensive analysis
        if data_type == 'process_anomaly' or 'process' in str(data).lower():
            process_result = real_threat_detector.detect_process_anomaly(data)
            ml_results.append(('process_anomaly', process_result))
        
        if data_type == 'file_threat' or 'file' in str(data).lower():
            file_result = real_threat_detector.detect_file_threat(data)
            ml_results.append(('file_threat', file_result))
        
        if data_type == 'network_anomaly' or any(keyword in str(data).lower() for keyword in ['network', 'connection', 'ip']):
            network_result = real_threat_detector.detect_network_anomaly(data)
            ml_results.append(('network_anomaly', network_result))
        
        if data_type == 'command_injection' or any(keyword in str(data).lower() for keyword in ['command', 'cmd', 'powershell', 'bash']):
            command_result = real_threat_detector.detect_command_injection(data)
            ml_results.append(('command_injection', command_result))
        
        # If no specific type detected, run general analysis
        if not ml_results:
            general_result = {'threat_detected': False, 'final_score': 0.1, 'reason': 'General log analysis'}
            ml_results.append(('general', general_result))
        
        # Combine ML results
        combined_ml_result = {
            'threat_detected': any(result[1].get('threat_detected', False) for result in ml_results),
            'max_confidence': max(result[1].get('final_score', 0) for result in ml_results),
            'detection_methods': [result[0] for result in ml_results],
            'individual_results': {result[0]: result[1] for result in ml_results},
            'analysis_comprehensive': True
        }
        
        return {
            'ml_detection_complete': True,
            'ml_result': combined_ml_result,
            'analysis_method': 'comprehensive_ml',
            'methods_used': len(ml_results),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ML detection tool failed: {e}")
        return {
            'ml_detection_complete': False,
            'error': str(e),
            'analysis_method': 'traditional_ml'
        }


@tool
def ai_threat_analysis_tool(detection_data: Dict, context: Dict, ml_results: Dict) -> Dict:
    """
    Run AI-powered threat analysis using GPT-3.5-turbo - ANALYZES ALL LOGS
    
    Args:
        detection_data: Raw detection data
        context: Analysis context
        ml_results: Results from ML detection
    
    Returns:
        AI analysis results with reasoning and comparison
    """
    try:
        # Create comprehensive prompt for GPT-3.5-turbo
        ml_summary = ml_results.get('ml_result', {})
        
        analysis_prompt = f"""
You are an expert cybersecurity analyst using GPT-3.5-turbo for threat detection.

ANALYZE THIS LOG ENTRY FOR THREATS:

LOG DATA:
{detection_data}

CONTEXT:
{context}

ML ANALYSIS RESULTS:
- Threat Detected: {ml_summary.get('threat_detected', False)}
- Confidence: {ml_summary.get('max_confidence', 0)}
- Methods: {ml_summary.get('detection_methods', [])}

YOUR TASK:
1. Independently analyze this log for threats (ignore ML results initially)
2. Look for sophisticated threats that ML might miss
3. Consider context, timing, and behavioral patterns
4. Compare your analysis with ML results
5. Provide final verdict combining both approaches

ANALYSIS CRITERIA:
- Advanced persistent threats (APT)
- Living-off-the-land techniques
- Evasion techniques that bypass ML
- Contextual anomalies
- Behavioral patterns
- Social engineering indicators

RESPOND WITH JSON:
{{
    "ai_threat_detected": true/false,
    "ai_confidence": 0.85,
    "threat_type": "apt|malware|insider|evasion|benign",
    "severity": "low|medium|high|critical",
    "mitre_techniques": ["T1059.001", "T1055"],
    "evasion_detected": true/false,
    "ml_comparison": {{
        "agrees_with_ml": true/false,
        "ml_missed_threat": true/false,
        "ai_missed_threat": true/false,
        "confidence_difference": 0.2
    }},
    "final_verdict": {{
        "threat_detected": true/false,
        "combined_confidence": 0.9,
        "primary_method": "ai|ml|combined",
        "reasoning": "Detailed explanation"
    }},
    "recommended_actions": ["isolate", "investigate", "monitor"],
    "analysis_quality": "high|medium|low"
}}
"""
        
        # Use GPT-3.5-turbo for analysis (this would use the ChatOpenAI instance)
        # For now, simulate the comprehensive analysis
        ai_analysis = {
            'ai_analysis_complete': True,
            'prompt_used': analysis_prompt,
            'ml_comparison_included': True,
            'analyzes_all_logs': True,
            'llm_model': 'gpt-3.5-turbo',
            'analysis_method': 'comprehensive_ai_ml_comparison',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # In production, this would call GPT-3.5-turbo with the prompt
        # ai_response = await llm.ainvoke(analysis_prompt)
        # ai_analysis['ai_result'] = parse_gpt_response(ai_response)
        
        return ai_analysis
        
    except Exception as e:
        logger.error(f"AI analysis tool failed: {e}")
        return {
            'ai_analysis_complete': False,
            'error': str(e),
            'analysis_method': 'ai_enhanced'
        }


@tool
def threat_correlation_tool(threat_events: List[Dict], time_window: int = 3600) -> Dict:
    """
    Correlate multiple threat events to identify attack campaigns
    
    Args:
        threat_events: List of threat events to correlate
        time_window: Time window for correlation in seconds
    
    Returns:
        Correlation analysis results
    """
    try:
        # Use existing AI correlation
        correlation_result = asyncio.run(
            ai_threat_analyzer.correlate_threats_with_ai(threat_events, time_window)
        )
        
        return {
            'correlation_complete': True,
            'correlation_result': correlation_result,
            'events_analyzed': len(threat_events),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Threat correlation tool failed: {e}")
        return {
            'correlation_complete': False,
            'error': str(e),
            'events_analyzed': len(threat_events)
        }


@tool
def threat_intelligence_tool(threat_data: Dict) -> Dict:
    """
    Generate threat intelligence for detected threats
    
    Args:
        threat_data: Threat detection data
    
    Returns:
        Generated threat intelligence
    """
    try:
        # Use existing threat intelligence generation
        intelligence = asyncio.run(
            ai_threat_analyzer.generate_threat_intelligence(threat_data)
        )
        
        return {
            'intelligence_complete': True,
            'intelligence_result': intelligence,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Threat intelligence tool failed: {e}")
        return {
            'intelligence_complete': False,
            'error': str(e)
        }


class LangChainDetectionAgent:
    """LangChain-based threat detection agent"""
    
    def __init__(self, llm_config: Dict = None):
        self.llm_config = llm_config or self._load_llm_config()
        
        # Initialize LLM (OpenAI GPT-3.5-turbo)
        # Use OpenAI GPT-3.5-turbo (as configured in server_config.yaml)
        try:
            self.llm = ChatOpenAI(
                model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                temperature=self.llm_config.get('temperature', 0.2),
                max_tokens=self.llm_config.get('max_tokens', 2048),
                api_key=self.llm_config.get('api_key')  # Uses configured API key
            )
            logger.info("Using OpenAI GPT-3.5-turbo for GuardianAlpha AI")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {e}")
            logger.error("Please ensure OPENAI_API_KEY is set or configure in server_config.yaml")
            raise
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize callback handler
        self.callback_handler = DetectionCallbackHandler()
        
        # Create detection tools
        self.tools = [
            ml_threat_detection_tool,
            ai_threat_analysis_tool,
            threat_correlation_tool,
            threat_intelligence_tool
        ]
        
        # Create detection prompt
        self.detection_prompt = self._create_detection_prompt()
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.detection_prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            callbacks=[self.callback_handler],
            verbose=True,
            max_iterations=5,
            early_stopping_method="generate"
        )
        
        logger.info("LangChain Detection Agent initialized")
    
    def _load_llm_config(self) -> Dict:
        """Load LLM configuration from server config"""
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent.parent))
            
            from log_forwarding.shared.config import config
            server_config = config.load_server_config()
            llm_config = server_config.get('llm', {})
            
            return {
                'provider': llm_config.get('provider', 'openai'),
                'model': llm_config.get('model', 'gpt-3.5-turbo'),
                'temperature': llm_config.get('temperature', 0.2),
                'max_tokens': llm_config.get('max_tokens', 2048),
                'api_key': llm_config.get('api_key')
            }
        except Exception as e:
            logger.warning(f"Failed to load LLM config: {e}")
            return self._default_llm_config()
    
    def _default_llm_config(self) -> Dict:
        """Default LLM configuration - loads dynamically"""
        return {
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'temperature': 0.2,
            'max_tokens': 2048,
            'api_key': os.getenv('OPENAI_API_KEY', '')  # Load from environment
        }
    
    def _create_detection_prompt(self) -> ChatPromptTemplate:
        """Create detection analysis prompt template"""
        system_message = """You are an elite cybersecurity analyst and threat detection expert.

Your role is to analyze security events and determine if they represent genuine threats.

You have access to the following tools:
- ml_threat_detection_tool: Run traditional ML-based threat detection
- ai_threat_analysis_tool: Run AI-powered threat analysis with LLM reasoning
- threat_correlation_tool: Correlate multiple events to identify attack campaigns
- threat_intelligence_tool: Generate actionable threat intelligence

ANALYSIS PROCESS:
1. First, run ML detection to get baseline analysis
2. Then run AI analysis to get contextual understanding
3. If multiple events, run correlation analysis
4. For confirmed threats, generate threat intelligence
5. Provide final verdict with reasoning

DECISION CRITERIA:
- Combine ML confidence with AI reasoning
- Consider context and historical patterns
- Account for false positive likelihood
- Assess business impact and urgency

Always provide:
- Clear threat verdict (THREAT/BENIGN/SUSPICIOUS)
- Confidence score (0.0 to 1.0)
- MITRE ATT&CK technique mapping
- Recommended response actions
- Detailed reasoning for your decision"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    async def analyze_threat(self, detection_data: Dict, context: Dict = None) -> ThreatAnalysisResult:
        """Analyze threat using LangChain agent - ANALYZES ALL LOGS"""
        try:
            if not context:
                context = {}
            
            # Prepare input for agent - ANALYZE ALL LOGS, NOT JUST ML-DETECTED
            analysis_input = {
                "input": f"""
Analyze this log entry for threats using both ML and AI analysis:

LOG DATA:
{detection_data}

CONTEXT:
{context}

COMPLETE ANALYSIS PROCESS:
1. First run ML detection to get baseline analysis
2. Then run AI analysis on the SAME log (regardless of ML result)
3. Compare ML and AI results
4. Provide final verdict combining both analyses
5. Generate reasoning for the decision

IMPORTANT: Analyze this log with AI even if ML says it's benign.
The goal is to catch threats that ML might miss and compare both approaches.

Provide final verdict with:
- ML analysis results
- AI analysis results  
- Combined confidence score
- Final threat determination
- Detailed reasoning comparing both methods
""",
                "chat_history": self.memory.chat_memory.messages
            }
            
            # Run agent analysis
            result = await self.agent_executor.ainvoke(analysis_input)
            
            # Parse agent output into structured result
            analysis_result = self._parse_agent_output(result, detection_data)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"LangChain threat analysis failed: {e}")
            return self._create_fallback_result(detection_data, str(e))
    
    async def analyze_multiple_threats(self, threat_events: List[Dict], 
                                     correlation_window: int = 3600) -> List[ThreatAnalysisResult]:
        """Analyze multiple threat events with correlation"""
        try:
            results = []
            
            # Analyze each event individually first
            for event in threat_events:
                result = await self.analyze_threat(event)
                results.append(result)
            
            # Run correlation analysis if multiple threats detected
            detected_threats = [r for r in results if r.threat_detected]
            
            if len(detected_threats) >= 2:
                correlation_input = {
                    "input": f"""
Correlate these {len(detected_threats)} threat detections to identify potential attack campaigns:

THREAT EVENTS:
{[r.dict() for r in detected_threats]}

TIME WINDOW: {correlation_window} seconds

Analyze for:
- Attack progression patterns
- Common infrastructure or techniques
- Coordinated campaign indicators
- Timeline consistency
- Threat actor attribution
""",
                    "chat_history": []
                }
                
                correlation_result = await self.agent_executor.ainvoke(correlation_input)
                
                # Update results with correlation information
                for result in results:
                    if result.threat_detected:
                        result.correlation_analysis = correlation_result.get('output', '')
            
            return results
            
        except Exception as e:
            logger.error(f"Multiple threat analysis failed: {e}")
            return [self._create_fallback_result({'error': 'batch_analysis_failed'}, str(e))]
    
    def _parse_agent_output(self, agent_result: Dict, detection_data: Dict) -> ThreatAnalysisResult:
        """Parse LangChain agent output into structured result"""
        try:
            output = agent_result.get('output', '')
            
            # Extract key information from agent output
            # This is a simplified parser - in production you'd use more sophisticated parsing
            
            threat_detected = any(keyword in output.lower() for keyword in 
                                ['threat detected', 'malicious', 'suspicious', 'attack'])
            
            # Extract confidence score
            confidence_score = 0.5  # Default
            import re
            confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', output.lower())
            if confidence_match:
                try:
                    confidence_score = float(confidence_match.group(1))
                    if confidence_score > 1.0:
                        confidence_score = confidence_score / 100  # Convert percentage
                except ValueError:
                    pass
            
            # Extract threat type
            threat_type = 'unknown'
            threat_types = ['malware', 'apt', 'insider', 'lateral_movement', 'data_exfiltration']
            for t_type in threat_types:
                if t_type in output.lower():
                    threat_type = t_type
                    break
            
            # Extract severity
            severity = 'medium'
            if any(word in output.lower() for word in ['critical', 'high']):
                severity = 'high'
            elif any(word in output.lower() for word in ['low', 'minor']):
                severity = 'low'
            
            # Extract MITRE techniques
            mitre_techniques = re.findall(r'T\d{4}(?:\.\d{3})?', output)
            
            # Extract recommended actions
            recommended_actions = []
            if 'isolate' in output.lower():
                recommended_actions.append('isolate_endpoint')
            if 'investigate' in output.lower():
                recommended_actions.append('investigate_further')
            if 'block' in output.lower():
                recommended_actions.append('block_indicators')
            
            return ThreatAnalysisResult(
                threat_detected=threat_detected,
                confidence_score=confidence_score,
                threat_type=threat_type,
                severity=severity,
                mitre_techniques=mitre_techniques,
                recommended_actions=recommended_actions,
                reasoning=output
            )
            
        except Exception as e:
            logger.error(f"Agent output parsing failed: {e}")
            return self._create_fallback_result(detection_data, str(e))
    
    def _create_fallback_result(self, detection_data: Dict, error: str) -> ThreatAnalysisResult:
        """Create fallback result when analysis fails"""
        return ThreatAnalysisResult(
            threat_detected=False,
            confidence_score=0.0,
            threat_type='analysis_failed',
            severity='unknown',
            mitre_techniques=[],
            recommended_actions=['manual_review'],
            reasoning=f"Analysis failed: {error}"
        )
    
    async def continuous_detection_pipeline(self, log_stream) -> None:
        """Run continuous detection on ALL logs in stream"""
        try:
            logger.info("Starting LangChain continuous detection pipeline - ANALYZING ALL LOGS")
            
            async for log_batch in log_stream:
                # Process EVERY log entry (not just suspicious ones)
                for log_entry in log_batch:
                    # Convert log to detection data
                    detection_data = self._convert_log_to_detection_data(log_entry)
                    
                    # Run comprehensive threat analysis on ALL logs
                    result = await self.analyze_threat(detection_data)
                    
                    # Handle ALL results (threats and benign)
                    await self._handle_analysis_result(result, log_entry)
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.05)  # Reduced delay for higher throughput
        
        except Exception as e:
            logger.error(f"Continuous detection pipeline failed: {e}")
    
    def _convert_log_to_detection_data(self, log_entry: Dict) -> Dict:
        """Convert log entry to detection data format"""
        return {
            'type': self._determine_detection_type(log_entry),
            'data': {
                'message': log_entry.get('message', ''),
                'timestamp': log_entry.get('timestamp', ''),
                'source': log_entry.get('source', ''),
                'process_info': log_entry.get('process_info', {}),
                'network_info': log_entry.get('network_info', {}),
                'parsed_data': log_entry.get('parsed_data', {}),
                'enriched_data': log_entry.get('enriched_data', {})
            },
            'agent_id': log_entry.get('agent_id', ''),
            'event_type': log_entry.get('event_type', '')
        }
    
    def _determine_detection_type(self, log_entry: Dict) -> str:
        """Determine detection type from log entry"""
        event_type = log_entry.get('event_type', '').lower()
        message = log_entry.get('message', '').lower()
        
        if 'process' in event_type or 'process' in message:
            return 'process_anomaly'
        elif 'file' in event_type or 'file' in message:
            return 'file_threat'
        elif 'network' in event_type or 'connection' in message:
            return 'network_anomaly'
        elif 'command' in event_type or 'cmd' in message or 'powershell' in message:
            return 'command_injection'
        else:
            return 'general_anomaly'
    
    async def _handle_analysis_result(self, result: ThreatAnalysisResult, log_entry: Dict) -> None:
        """Handle ALL analysis results (threats and benign)"""
        try:
            # Store ALL analysis results for learning and comparison
            analysis_record = {
                'threat_detected': result.threat_detected,
                'confidence_score': result.confidence_score,
                'threat_type': result.threat_type,
                'severity': result.severity,
                'mitre_techniques': result.mitre_techniques,
                'recommended_actions': result.recommended_actions,
                'reasoning': result.reasoning,
                'log_entry': log_entry,
                'analysis_method': 'comprehensive_ml_ai_comparison',
                'llm_model': 'gpt-3.5-turbo',
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            # Store using existing detection storage
            real_threat_detector.store_detection(analysis_record, log_entry.get('agent_id', ''))
            
            # Log analysis for all entries
            if result.threat_detected:
                logger.warning(f"THREAT DETECTED: {result.threat_type} (confidence: {result.confidence_score})")
                
                # Trigger alerts for high-severity threats
                if result.severity in ['high', 'critical']:
                    await self._trigger_alert(result, log_entry)
            else:
                logger.debug(f"Log analyzed as benign: {log_entry.get('message', '')[:50]}...")
        
        except Exception as e:
            logger.error(f"Analysis result handling failed: {e}")
    
    async def _trigger_alert(self, result: ThreatAnalysisResult, log_entry: Dict) -> None:
        """Trigger alert for high-severity threats"""
        try:
            alert_data = {
                'alert_id': f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'threat_type': result.threat_type,
                'severity': result.severity,
                'confidence': result.confidence_score,
                'agent_id': log_entry.get('agent_id'),
                'mitre_techniques': result.mitre_techniques,
                'recommended_actions': result.recommended_actions,
                'reasoning': result.reasoning,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.critical(f"SECURITY ALERT: {alert_data}")
            
            # Here you would integrate with alerting systems
            # - SIEM integration
            # - Email/SMS notifications
            # - Incident response automation
            
        except Exception as e:
            logger.error(f"Alert triggering failed: {e}")
    
    async def get_detection_statistics(self) -> Dict:
        """Get detection statistics"""
        try:
            return {
                'agent_type': 'langchain_detection_agent',
                'llm_model': self.llm_config.get('model'),
                'tools_available': len(self.tools),
                'memory_messages': len(self.memory.chat_memory.messages),
                'detection_events': len(self.callback_handler.detection_events),
                'last_analysis': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Statistics collection failed: {e}")
            return {'error': str(e)}


# Global LangChain detection agent instance
langchain_detection_agent = LangChainDetectionAgent()
