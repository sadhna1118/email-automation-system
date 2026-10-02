@echo off
title Email Automation System - Control Center
echo ========================================================
echo   Launching Email Automation Streamlit Web Dashboard
echo   URL: http://localhost:8501
echo ========================================================
echo.
.venv\Scripts\python.exe -m streamlit run app.py
pause
