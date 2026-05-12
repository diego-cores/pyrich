
@echo off
cd /d "%~dp0"
if exist "venv\scripts\activate.bat" (
    call venv\scripts\activate.bat
    start pythonw src\main.py
) else (
    start pythonw -m src\main.py
)
