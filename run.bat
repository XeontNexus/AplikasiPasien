@echo off
title Sistem Informasi & Rekam Medis Pasien BPJS
cd /d "%~dp0"

echo ==========================================================
echo  Menjalankan Aplikasi Rekam Medis & Pasien BPJS...
echo ==========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python app.py
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        py app.py
    ) else (
        echo [ERROR] Python tidak ditemukan di sistem PATH Anda!
        echo Silakan instal Python atau tambahkan ke PATH.
        pause
        exit /b 1
    )
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Aplikasi tertutup dengan kode kesalahan %ERRORLEVEL%.
    pause
)
