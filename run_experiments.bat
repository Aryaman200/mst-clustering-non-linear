@echo off
cd /d "%~dp0research"
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
echo Re-running all experiments (about 30 s)...
%PY% experiments.py && %PY% diagrams.py
echo Done: research\figures and research\results.json updated.
pause
