@echo off
echo ====================================================
echo    BIOTRACK - Sistema de Analisis Biomecanico
echo ====================================================
echo.

REM Usar Python de Anaconda
set PYTHON_PATH=C:\Users\mariz\anaconda3\python.exe

REM Verificar que existe
if not exist "%PYTHON_PATH%" (
    echo ERROR: No se encontro Python de Anaconda en:
    echo %PYTHON_PATH%
    echo.
    echo Por favor, ajusta la ruta en este archivo.
    pause
    exit /b 1
)

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

REM Ejecutar la aplicacion
echo Iniciando servidor con: %PYTHON_PATH%
echo.
"%PYTHON_PATH%" run.py

pause
