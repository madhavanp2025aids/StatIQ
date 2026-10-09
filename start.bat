@echo off
echo ============================================
echo   StatGPT - MoSPI Statistics AI Assistant
echo ============================================
echo.
echo Starting StatGPT backend server...
echo Open your browser at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server.
echo.
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause
