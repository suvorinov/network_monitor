@echo off
setlocal

:: Startup Script (GPO: Computer Configuration → Windows Settings → Scripts → Startup)
set SOURCE=\\zr.local\netlogon\CyberAgent
set TARGET=%ProgramData%\CyberAgent
set LOG="%SystemRoot%\Temp\CyberAgent_install.log"

echo [%DATE% %TIME%] Запуск установки CyberAgent >> %LOG%

:: Ожидание сети (до 60 сек, шаг 5 сек)
for /l %%i in (1,1,12) do (
    if exist "\\zr.local\netlogon" (
        echo [%DATE% %TIME%] Сеть доступна (попытка %%i) >> %LOG%
        goto :net_ok
    )
    echo [%DATE% %TIME%] Ожидание сети... (%%i/12) >> %LOG%
    timeout /t 5 /nobreak >nul
)
echo [%DATE% %TIME%] Ошибка: сеть недоступна после 60 сек >> %LOG%
exit /b 1

:net_ok
:: Копируем файлы
if not exist "%TARGET%" (
    mkdir "%TARGET%"
    echo [%DATE% %TIME%] Создана папка %TARGET% >> %LOG%
)

:: Даём пользователям доступ на чтение (для логов)
icacls "%TARGET%" /grant "Users:(RX)" /q >nul 2>&1

xcopy /d /y "%SOURCE%\*.*" "%TARGET%" >nul
if %ERRORLEVEL% neq 0 (
    echo [%DATE% %TIME%] Ошибка копирования из %SOURCE% >> %LOG%
    exit /b 1
)
echo [%DATE% %TIME%] Файлы скопированы в %TARGET% >> %LOG%

:: Останавливаем старый процесс перед запуском
taskkill /f /im CyberAgent.exe >nul 2>&1

:: Запускаем от имени SYSTEM
cd /d "%TARGET%"
start "" "CyberAgent.exe"
echo [%DATE% %TIME%] CyberAgent запущен >> %LOG%

endlocal
