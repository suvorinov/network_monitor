# Сборка CyberAgent.exe под Windows
# Запускать из корня репозитория или из папки agent/
# Требуется: pyinstaller (pip install pyinstaller)

$ErrorActionPreference = "Stop"
$AgentDir = Split-Path -Parent $PSCommandPath
$RootDir = Split-Path -Parent $AgentDir

Set-Location $AgentDir

pyinstaller --onefile `
    --noconsole `
    --name CyberAgent `
    --hidden-import psutil `
    --hidden-import loguru `
    --distpath . `
    agent.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: dist/CyberAgent.exe собран" -ForegroundColor Green
} else {
    Write-Host "FAIL: сборка не удалась" -ForegroundColor Red
    exit 1
}
