@echo off
cd /d "%~dp0"
chcp 65001 > nul
title MANIPanel — Панель управления веб-сервером

set PYTHONUNBUFFERED=1

cls
echo ========================================================
echo   [+] Инициализация и запуск MANIPanel...
echo ========================================================
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

py server.py 2>nul || python server.py

if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Сервер завершил работу с ошибкой (Код: %errorlevel%)!
)

echo.
echo [!] Сервер остановлен.
pause