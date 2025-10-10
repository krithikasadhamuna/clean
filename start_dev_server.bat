@echo off
REM Start local development server with AI scoring

echo ==========================================
echo Starting Local Development Server
echo ==========================================
echo.

REM Set environment variables
set OPENAI_API_KEY=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
set USE_AI_SCORING=true

echo Environment configured:
echo   USE_AI_SCORING: %USE_AI_SCORING%
echo   OPENAI_API_KEY: Set (hidden)
echo.

echo Starting server on 127.0.0.1:8000...
echo.

REM Start server
python main.py server --host 127.0.0.1 --port 8000


