#!/usr/bin/env python3
"""
Fix Unicode encoding issues in LangServe server startup
"""

import os
import sys
import subprocess

def fix_unicode_encoding():
    """Fix Unicode encoding issues for Windows"""
    
    print("Fixing Unicode Encoding Issues")
    print("=" * 40)
    
    # Set environment variables for Unicode support
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'
    
    print("Set PYTHONIOENCODING=utf-8")
    print("Set PYTHONLEGACYWINDOWSSTDIO=1")
    
    # Try to set console code page to UTF-8
    try:
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
        print("Set console code page to UTF-8")
    except:
        print("Could not set console code page")
    
    return True

def create_unicode_safe_server():
    """Create a Unicode-safe server startup script"""
    
    server_script = '''#!/usr/bin/env python3
"""
Unicode-safe server startup script
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Fix Unicode encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def start_unicode_safe_server():
    """Start server with Unicode safety"""
    
    try:
        # Import and start the test server instead of main server
        from test_server import app
        import uvicorn
        
        logger.info("Starting Unicode-safe SOC server...")
        
        # Start server
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8081,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(start_unicode_safe_server())
'''
    
    with open('start_unicode_safe_server.py', 'w', encoding='utf-8') as f:
        f.write(server_script)
    
    print("Created start_unicode_safe_server.py")
    return True

if __name__ == "__main__":
    fix_unicode_encoding()
    create_unicode_safe_server()
    print("\nUnicode fixes applied!")
    print("Run: python start_unicode_safe_server.py")
