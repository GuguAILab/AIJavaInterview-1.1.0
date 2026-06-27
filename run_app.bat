@echo off
title AI Java Mock Interview - Running
cd /d "D:\Gugu\AIJavaInterview-1.2.0-Setup\"
echo.
echo  Starting AI Mock Interview Assistant...
echo  URL: http://localhost:8501/JavaAIMockInterview/
echo.
start "" "C:\Users\prati\anaconda3\python.exe" -m streamlit run ai_assistant.py --server.port 8501 --server.baseUrlPath "/JavaAIMockInterview" --browser.gatherUsageStats false
timeout /t 6 /nobreak >nul
start "" "http://localhost:8501/JavaAIMockInterview/"
pause
