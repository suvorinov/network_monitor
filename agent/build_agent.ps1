<#
.SYNOPSIS
    Build CyberAgent.exe with PyInstaller for Windows.
.DESCRIPTION
    For Windows 7 targets, build with Python 3.8 (last Win7-compatible version).
    Install dependencies: pip install pyinstaller psutil==5.9.8 requests loguru
.NOTES
    Author: Oleg Suvorinov
#>

$ErrorActionPreference = "Stop"
$AgentDir = Split-Path -Parent $PSCommandPath
$RootDir = Split-Path -Parent $AgentDir

Set-Location $AgentDir

pyinstaller --onefile `
    --noconsole `
    --name CyberAgent `
    --noupx `
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
