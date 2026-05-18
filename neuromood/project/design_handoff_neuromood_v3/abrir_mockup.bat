@echo off
cd /d "%~dp0"
start chrome --new-window --window-size=1440,900 http://localhost:8000/NeuroMood%%20Redesign.html
python -m http.server 8000
pause