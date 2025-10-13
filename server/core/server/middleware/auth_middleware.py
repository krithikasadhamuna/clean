"""
Authentication middleware for CodeGrey API compatibility
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional


class CodeGreyAPIKeyAuth(HTTPBearer):
    """CodeGrey API Key authentication"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.default_api_key = "api_codegrey_2024"
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        # Check for X-API-Key header (CodeGrey format)
        api_key = request.headers.get("X-API-Key")
        
        if api_key:
            if api_key == self.default_api_key:
                return HTTPAuthorizationCredentials(scheme="ApiKey", credentials=api_key)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
        
        # Fallback to Bearer token
        return await super().__call__(request)


# Global auth instance
codegrey_auth = CodeGreyAPIKeyAuth(auto_error=False)
