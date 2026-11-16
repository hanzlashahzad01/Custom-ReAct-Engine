@echo off
REM Shortcut launcher for Custom ReAct Engine
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" "%~dp0main.py" %*
) else (
    "C:\Users\Boss\AppData\Local\Programs\Python\Python312\python.exe" "%~dp0main.py" %*
)
