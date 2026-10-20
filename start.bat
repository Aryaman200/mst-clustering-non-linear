@echo off
setlocal
title MST Clustering Dashboard
cd /d "%~dp0"

rem ---- 1. find Python ----
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo [ERROR] Python 3.10+ not found. Install it from https://www.python.org/downloads/ and tick "Add to PATH".
  pause & exit /b 1
)

rem ---- 2. use system Python if the libraries are already installed ----
%PY% -c "import numpy, scipy, sklearn" >nul 2>nul
if %errorlevel%==0 goto run

rem ---- 3. otherwise create a local virtual environment ----
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment ^(first run only^)...
  %PY% -m venv .venv || (echo [ERROR] could not create venv & pause & exit /b 1)
)
set "PY=.venv\Scripts\python.exe"
%PY% -c "import numpy, scipy, sklearn" >nul 2>nul
if %errorlevel% neq 0 (
  echo Installing dependencies ^(first run only, a few minutes^)...
  %PY% -m pip install --upgrade pip >nul
  %PY% -m pip install -r requirements.txt || (echo [ERROR] pip install failed & pause & exit /b 1)
)

:run
echo.
echo Starting dashboard... your browser will open automatically.
echo Close this window or press Ctrl+C to stop.
%PY% app\server.py %*
if %errorlevel% neq 0 pause
