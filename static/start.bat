@echo off
chcp 65001 > nul
color 0B
title MANIweb Server
echo ========================================
echo          Запуск MANIweb Server...
echo ========================================
echo Локальный адрес: http://127.0.0.1:5000
echo.
python server.py
pause