"""
GPT Interaction Logger
Centralized logging utility for all GPT API calls across the SOC platform
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class GPTInteractionLogger:
    """Centralized logger for all GPT interactions"""
    
    @staticmethod
    async def log_interaction(
        interaction_type: str,
        prompt: str,
        response: str,
        model: str = "gpt-3.5-turbo",
        tokens_used: int = 0,
        response_time_ms: int = 0,
        success: bool = True,
        error_message: str = None,
        user_request: str = None,
        result_summary: str = None,
        component: str = "unknown",
        metadata_dict: dict = None
    ):
        """
        Log a GPT interaction to the database
        
        Args:
            interaction_type: Type of interaction (scenario_generation, command_generation, threat_analysis, etc.)
            prompt: The prompt sent to GPT
            response: The response from GPT
            model: Model name
            tokens_used: Total tokens consumed
            response_time_ms: Response time in milliseconds
            success: Whether the call succeeded
            error_message: Error message if failed
            user_request: Original user request
            result_summary: Brief summary of the result
            component: Which component made the call
            metadata_dict: Additional metadata as dict
        """
        try:
            from core.server.storage.database_manager import DatabaseManager
            
            db_manager = DatabaseManager(db_path="soc_database.db")
            
            # Build metadata
            metadata = metadata_dict or {}
            metadata.update({
                "model": model,
                "component": component,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Truncate long strings to prevent database bloat
            prompt_truncated = prompt[:5000] if prompt else ""
            response_truncated = response[:10000] if response else ""
            user_request_truncated = user_request[:1000] if user_request else None
            result_summary_truncated = result_summary[:500] if result_summary else None
            
            # Log to database
            interaction_id = str(uuid.uuid4())
            await db_manager.log_gpt_interaction(
                interaction_type=interaction_type,
                prompt=prompt_truncated,
                response=response_truncated,
                model=model,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                metadata=json.dumps(metadata),
                user_request=user_request_truncated,
                result_summary=result_summary_truncated
            )
            
            logger.debug(f"✅ Logged GPT interaction [{interaction_type}]: {interaction_id}")
            return interaction_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log GPT interaction: {e}")
            return None
    
    @staticmethod
    async def log_success(
        interaction_type: str,
        prompt: str,
        response: str,
        response_time_ms: int,
        user_request: str = None,
        result_summary: str = None,
        component: str = "unknown",
        tokens_used: int = 1500
    ):
        """Quick method to log a successful GPT interaction"""
        return await GPTInteractionLogger.log_interaction(
            interaction_type=interaction_type,
            prompt=prompt,
            response=response,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            success=True,
            user_request=user_request,
            result_summary=result_summary,
            component=component
        )
    
    @staticmethod
    async def log_failure(
        interaction_type: str,
        prompt: str,
        error_message: str,
        response_time_ms: int = 0,
        user_request: str = None,
        component: str = "unknown"
    ):
        """Quick method to log a failed GPT interaction"""
        return await GPTInteractionLogger.log_interaction(
            interaction_type=interaction_type,
            prompt=prompt,
            response="",
            tokens_used=0,
            response_time_ms=response_time_ms,
            success=False,
            error_message=error_message,
            user_request=user_request,
            result_summary=f"Failed: {error_message[:100]}",
            component=component
        )


# Singleton instance for easy import
gpt_logger = GPTInteractionLogger()

