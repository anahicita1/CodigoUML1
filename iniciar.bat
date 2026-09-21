@echo off
call "%~dp0venv\Scripts\activate.bat"
cd /d "%~dp0CodigoUML1"
streamlit run app.py
pause