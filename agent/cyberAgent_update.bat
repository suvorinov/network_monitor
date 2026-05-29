@echo off
setlocal

set SOURCE=\\zr.local\netlogon\CyberAgent
set TARGET=%ProgramData%\CyberAgent
set LOG="%SystemRoot%\Temp\CyberAgent_update.log"

echo [%DATE% %TIME%] Запуск обновления CyberAgent >> %LOG%

:: Проверка доступности источника
if not exist "%SOURCE%\version.txt" (
    echo [%DATE% %TIME%] Ошибка: источник %SOURCE% недоступен >> %LOG%
    exit /b 1
)

:: Сравнение версий
if not exist "%TARGET%\version.txt" goto :update
fc "%SOURCE%\version.txt" "%TARGET%\version.txt" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [%DATE% %TIME%] Версия актуальна, обновление не требуется >> %LOG%
    exit /b 0
)

:update
echo [%DATE% %TIME%] Обнаружена новая версия. Начало обновления... >> %LOG%

:: Создаём папку если её нет
if not exist "%TARGET%" mkdir "%TARGET%"

:: Копируем файлы
xcopy /d /y "%SOURCE%\*.*" "%TARGET%" >nul
if %ERRORLEVEL% neq 0 (
    echo [%DATE% %TIME%] Ошибка копирования >> %LOG%
    exit /b 1
)

:: Останавливаем старый процесс и запускаем новый
taskkill /f /im CyberAgent.exe >nul 2>&1
start "" "%TARGET%\CyberAgent.exe"

echo [%DATE% %TIME%] Обновление завершено. Запущен CyberAgent %SOURCE:\=/% >> %LOG%

endlocal
