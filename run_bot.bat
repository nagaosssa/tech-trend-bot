@echo off
cd /d "%~dp0"
call .venv\Scripts\activate 2>nul
if errorlevel 1 (
    echo Virtual environment not found or failed to activate. Trying global python...
    python bot.py
) else (
    python bot.py
)
pause
