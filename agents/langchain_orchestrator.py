"""
LangChain-Based AI SOC Platform Orchestrator
Coordinates all agents and workflows using LangChain
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import AsyncCallbackHandler

try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

from .detection_agent.langchain_detection_agent import langchain_detection_agent
from .attack_agent.langchain_attack_agent import phantomstrike_ai
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from log_forwarding.langchain_tools.log_processing_tools import (
    query_recent_logs_tool,
    network_topology_analysis_tool,
    log_enrichment_tool,
    threat_hunting_tool
)


logger = logging.getLogger(__name__)


class SOCOrchestrationCallbackHandler(AsyncCallbackHandler):
    """Callback handler for SOC orchestration events"""
    
    def __init__(self):
        self.orchestration_events = []
        self.user_interactions = []
    
    async def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        """Called when chain starts"""
        self.orchestration_events.append({
            'event': 'chain_start',
            'inputs': str(inputs)[:200],
            'timestamp': datetime.utcnow().isoformat()
        })


@tool
def detection_analysis_tool(log_data: Dict, context: Dict) -> Dict:
    """
    Run comprehensive threat detection analysis
    
    Args:
        log_data: Log data to analyze
        context: Analysis context
    
    Returns:
        Detection analysis results
    """
    try:
        # Use LangChain detection agent
        result = asyncio.run(
            langchain_detection_agent.analyze_threat(log_data, context)
        )
        
        return {
            'detection_analysis_complete': True,
            'detection_result': result.dict() if hasattr(result, 'dict') else result,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Detection analysis tool failed: {e}")
        return {
            'detection_analysis_complete': False,
            'error': str(e)
        }


@tool
def attack_planning_tool(attack_request: str, network_context: Dict, constraints: Dict = None) -> Dict:
    """
    Plan attack scenarios using PhantomStrike AI
    
    Args:
        attack_request: Attack objective or request
        network_context: Current network topology context
        constraints: Attack constraints
    
    Returns:
        Attack planning results
    """
    try:
        if not constraints:
            constraints = {}
        
        # Use LangChain attack agent
        scenario = asyncio.run(
            phantomstrike_ai.plan_attack_scenario(attack_request, network_context, constraints)
        )
        
        return {
            'attack_planning_complete': True,
            'scenario': scenario.dict() if hasattr(scenario, 'dict') else scenario,
            'requires_approval': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Attack planning tool failed: {e}")
        return {
            'attack_planning_complete': False,
            'error': str(e)
        }


@tool
def correlation_analysis_tool(events: List[Dict], analysis_type: str = "threat_correlation") -> Dict:
    """
    Perform correlation analysis across multiple events
    
    Args:
        events: Events to correlate
        analysis_type: Type of correlation analysis
    
    Returns:
        Correlation analysis results
    """
    try:
        # Use detection agent for correlation
        if analysis_type == "threat_correlation":
            results = asyncio.run(
                langchain_detection_agent.analyze_multiple_threats(events)
            )
        else:
            results = []
        
        return {
            'correlation_analysis_complete': True,
            'analysis_type': analysis_type,
            'events_analyzed': len(events),
            'correlations_found': len([r for r in results if getattr(r, 'threat_detected', False)]),
            'results': [r.dict() if hasattr(r, 'dict') else r for r in results],
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Correlation analysis tool failed: {e}")
        return {
            'correlation_analysis_complete': False,
            'error': str(e)
        }


class LangChainSOCOrchestrator:
    """LangChain-based SOC platform orchestrator"""
    
    def __init__(self, llm_config: Dict = None):
        self.llm_config = llm_config or self._default_llm_config()
        
        # Initialize LLM
        self.llm = ChatOllama(
            model=self.llm_config.get('model', 'cybersec-ai'),
            base_url=self.llm_config.get('endpoint', 'http://localhost:11434'),
            temperature=self.llm_config.get('temperature', 0.5)
        )
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize callback handler
        self.callback_handler = SOCOrchestrationCallbackHandler()
        
        # Combine all tools
        self.tools = [
            # Log processing tools
            query_recent_logs_tool,
            network_topology_analysis_tool,
            log_enrichment_tool,
            threat_hunting_tool,
            
            # Detection and analysis tools
            detection_analysis_tool,
            correlation_analysis_tool,
            
            # Attack planning tools
            attack_planning_tool
        ]
        
        # Create orchestration prompt
        self.orchestration_prompt = self._create_orchestration_prompt()
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.orchestration_prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            callbacks=[self.callback_handler],
            verbose=True,
            max_iterations=15,
            early_stopping_method="generate"
        )
        
        logger.info("LangChain SOC Orchestrator initialized")
    
    def _default_llm_config(self) -> Dict:
        """Default LLM configuration"""
        return {
            'endpoint': 'http://localhost:11434',
            'model': 'cybersec-ai',
            'temperature': 0.5,
            'max_tokens': 4096
        }
    
    def _create_orchestration_prompt(self) -> ChatPromptTemplate:
        """Create SOC orchestration prompt"""
        system_message = """You are the AI SOC Platform Orchestrator, coordinating all security operations.

You manage:
- Threat detection and analysis
- Attack simulation and red team exercises  
- Network topology analysis
- Log processing and correlation
- Incident response coordination

Available tools:
- query_recent_logs_tool: Query and retrieve log data
- network_topology_analysis_tool: Analyze network topology
- log_enrichment_tool: Enrich logs with intelligence
- threat_hunting_tool: Conduct proactive threat hunting
- detection_analysis_tool: Run threat detection analysis
- correlation_analysis_tool: Correlate multiple security events
- attack_planning_tool: Plan red team attack scenarios

OPERATIONAL MODES:

1. DETECTION MODE:
   - Continuously analyze incoming logs
   - Detect threats and anomalies
   - Correlate related events
   - Generate alerts and recommendations

2. ATTACK SIMULATION MODE:
   - Plan realistic attack scenarios
   - Present scenarios for approval
   - Execute approved attacks safely
   - Generate detection test data

3. INVESTIGATION MODE:
   - Investigate security incidents
   - Hunt for advanced threats
   - Analyze attack campaigns
   - Provide forensic analysis

4. MONITORING MODE:
   - Monitor network topology changes
   - Track system health and performance
   - Provide operational intelligence

Always:
- Prioritize security and safety
- Require approval for attack executions
- Provide clear reasoning for decisions
- Maintain audit trails
- Consider business impact"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    async def process_soc_request(self, request: str, context: Dict = None) -> Dict[str, Any]:
        """Process SOC operation request"""
        try:
            if not context:
                context = {}
            
            # Prepare input for orchestrator
            orchestration_input = {
                "input": f"""
SOC Operation Request: {request}

Context: {context}

Please analyze this request and execute the appropriate SOC operations:

1. Determine the type of operation (detection, attack simulation, investigation, monitoring)
2. Use the appropriate tools to fulfill the request
3. Provide comprehensive results and recommendations
4. If this is an attack request, ensure proper approval workflow
5. If this is a detection request, provide threat analysis and recommendations

Be thorough and use multiple tools as needed to provide complete analysis.
""",
                "chat_history": self.memory.chat_memory.messages
            }
            
            # Execute orchestration
            result = await self.agent_executor.ainvoke(orchestration_input)
            
            return {
                'success': True,
                'operation_type': self._classify_operation_type(request),
                'result': result,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"SOC request processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }
    
    def _classify_operation_type(self, request: str) -> str:
        """Classify the type of SOC operation"""
        request_lower = request.lower()
        
        if any(term in request_lower for term in ['attack', 'simulate', 'red team', 'penetration']):
            return 'attack_simulation'
        elif any(term in request_lower for term in ['detect', 'analyze', 'threat', 'malicious']):
            return 'threat_detection'
        elif any(term in request_lower for term in ['investigate', 'hunt', 'forensic', 'incident']):
            return 'investigation'
        elif any(term in request_lower for term in ['monitor', 'status', 'health', 'topology']):
            return 'monitoring'
        else:
            return 'general'
    
    async def continuous_soc_operations(self, log_stream) -> None:
        """Run continuous SOC operations on log stream"""
        try:
            logger.info("Starting LangChain continuous SOC operations")
            
            async for log_batch in log_stream:
                # Process batch for threats
                batch_analysis = await self.process_soc_request(
                    f"Analyze this log batch for threats: {len(log_batch)} entries",
                    {'log_batch': log_batch}
                )
                
                # Handle any detected threats
                if batch_analysis.get('success'):
                    await self._handle_batch_analysis_result(batch_analysis, log_batch)
        
        except Exception as e:
            logger.error(f"Continuous SOC operations failed: {e}")
    
    async def _handle_batch_analysis_result(self, analysis_result: Dict, log_batch: List) -> None:
        """Handle results from batch analysis"""
        try:
            # Extract any threats or important findings
            result_output = analysis_result.get('result', {}).get('output', '')
            
            if any(keyword in result_output.lower() for keyword in ['threat', 'malicious', 'suspicious']):
                logger.warning(f"Potential threats found in batch analysis")
                
                # Trigger detailed analysis for suspicious logs
                for log_entry in log_batch:
                    await self._detailed_threat_analysis(log_entry)
        
        except Exception as e:
            logger.error(f"Batch analysis result handling failed: {e}")
    
    async def _detailed_threat_analysis(self, log_entry: Dict) -> None:
        """Run detailed threat analysis on suspicious log entry"""
        try:
            analysis_request = f"""
Run detailed threat analysis on this suspicious log entry:

LOG ENTRY: {log_entry}

Please:
1. Run ML detection
2. Run AI threat analysis
3. Check for correlations
4. Generate threat intelligence if needed
5. Provide final verdict and recommendations
"""
            
            result = await self.process_soc_request(analysis_request)
            
            if result.get('success'):
                logger.info(f"Detailed analysis completed for log: {log_entry.get('id', 'unknown')}")
        
        except Exception as e:
            logger.error(f"Detailed threat analysis failed: {e}")
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        try:
            return {
                'orchestrator_type': 'langchain_soc_orchestrator',
                'llm_model': self.llm_config.get('model'),
                'tools_available': len(self.tools),
                'memory_messages': len(self.memory.chat_memory.messages),
                'orchestration_events': len(self.callback_handler.orchestration_events),
                'detection_agent_status': await langchain_detection_agent.get_detection_statistics(),
                'attack_agent_status': await phantomstrike_ai.get_execution_status(),
                'last_update': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {'error': str(e)}


# Global LangChain SOC orchestrator instance
soc_orchestrator = LangChainSOCOrchestrator()
