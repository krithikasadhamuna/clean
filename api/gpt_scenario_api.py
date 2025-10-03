"""
GPT Scenario Request API
API endpoints for requesting custom attack scenarios from GPT
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.attack_agent.gpt_scenario_requester import GPTScenarioRequester, request_gpt_scenario

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/gpt-scenarios", tags=["GPT Scenarios"])


class ScenarioRequest(BaseModel):
    """Request model for GPT scenario generation"""
    user_request: str
    network_context: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None


class ScenarioResponse(BaseModel):
    """Response model for GPT scenario generation"""
    success: bool
    scenario: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


@router.post("/request", response_model=ScenarioResponse)
async def request_custom_scenario(request: ScenarioRequest):
    """
    Request a custom attack scenario from GPT
    
    Args:
        request: Scenario request with user input and context
        
    Returns:
        GPT-generated custom attack scenario
    """
    try:
        # Import LLM
        from langchain_openai import ChatOpenAI
        
        # Initialize GPT requester
        llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)
        requester = GPTScenarioRequester(llm)
        
        # Generate custom scenario
        scenario = await requester.request_custom_scenario(
            user_request=request.user_request,
            network_context=request.network_context or {},
            constraints=request.constraints or {}
        )
        
        logger.info(f"Generated custom GPT scenario: {scenario.get('name', 'Unknown')}")
        
        return ScenarioResponse(
            success=True,
            scenario=scenario,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"GPT scenario request failed: {e}")
        return ScenarioResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow().isoformat()
        )


@router.get("/suggestions")
async def get_scenario_suggestions(network_context: Optional[Dict[str, Any]] = None):
    """
    Get GPT-generated scenario suggestions based on network context
    
    Args:
        network_context: Network context information
        
    Returns:
        List of scenario suggestions
    """
    try:
        # Import LLM
        from langchain_openai import ChatOpenAI
        
        # Initialize GPT requester
        llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)
        requester = GPTScenarioRequester(llm)
        
        # Get suggestions
        suggestions = await requester.get_scenario_suggestions(network_context or {})
        
        return {
            "success": True,
            "suggestions": suggestions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Scenario suggestions failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "suggestions": [
                "Network reconnaissance and service enumeration",
                "Privilege escalation simulation",
                "Data exfiltration testing",
                "Persistence mechanism installation",
                "Defense evasion techniques"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/execute")
async def execute_gpt_scenario(scenario: Dict[str, Any]):
    """
    Execute a GPT-generated scenario
    
    Args:
        scenario: GPT-generated scenario to execute
        
    Returns:
        Execution results
    """
    try:
        # Import attack agent
        from agents.attack_agent.langchain_attack_agent import LangChainAttackAgent
        
        # Initialize attack agent
        attack_agent = LangChainAttackAgent()
        
        # Execute scenario
        result = await attack_agent.execute_attack_scenario(scenario)
        
        return {
            "success": True,
            "execution_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"GPT scenario execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/examples")
async def get_example_requests():
    """
    Get example GPT scenario requests
    
    Returns:
        List of example requests
    """
    examples = [
        {
            "title": "Data Exfiltration Test",
            "request": "I want to test if I can steal data from the finance department without being detected",
            "description": "Tests stealthy data exfiltration capabilities"
        },
        {
            "title": "APT Simulation",
            "request": "Create an APT simulation that targets the CEO's computer and exfiltrates sensitive documents",
            "description": "Simulates advanced persistent threat attack"
        },
        {
            "title": "Network Penetration",
            "request": "I want to test network penetration from the DMZ to the internal network",
            "description": "Tests network segmentation and lateral movement"
        },
        {
            "title": "Privilege Escalation",
            "request": "Create a scenario to test privilege escalation from a regular user to domain admin",
            "description": "Tests privilege escalation techniques"
        },
        {
            "title": "Ransomware Simulation",
            "request": "Simulate a ransomware attack that encrypts files but doesn't actually damage them",
            "description": "Tests ransomware detection and response"
        },
        {
            "title": "Insider Threat",
            "request": "Create an insider threat scenario where a disgruntled employee steals company data",
            "description": "Tests insider threat detection capabilities"
        },
        {
            "title": "Supply Chain Attack",
            "request": "Simulate a supply chain attack through a compromised software update",
            "description": "Tests supply chain security measures"
        },
        {
            "title": "Zero-Day Exploit",
            "request": "Create a scenario that simulates a zero-day exploit against a web application",
            "description": "Tests zero-day detection and response"
        }
    ]
    
    return {
        "success": True,
        "examples": examples,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/history")
async def get_request_history():
    """
    Get history of GPT scenario requests
    
    Returns:
        Request history
    """
    try:
        # This would typically come from a database
        # For now, return a placeholder
        return {
            "success": True,
            "history": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "request": "Data exfiltration test",
                    "scenario_name": "Stealthy Data Theft",
                    "status": "completed"
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "history": [],
            "timestamp": datetime.utcnow().isoformat()
        }
