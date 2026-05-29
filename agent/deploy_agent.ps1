<#
.SYNOPSIS
    Deploy CyberAgent to domain computers via AD group or computer name.
.DESCRIPTION
    Copies agent files from \\zr.local\netlogon\CyberAgent to
    C:\ProgramData\CyberAgent on target machines and starts CyberAgent.exe.
.PARAMETER GroupName
    AD group name (e.g. "Computers_IT", "Workstations_Finance").
.PARAMETER ComputerName
    Single computer name or array (e.g. "zr-115").
.PARAMETER Source
    Source path. Default: \\zr.local\netlogon\CyberAgent.
.EXAMPLE
    .\deploy_agent.ps1 -GroupName "Workstations_Finance"
.EXAMPLE
    .\deploy_agent.ps1 -ComputerName "zr-115"
.EXAMPLE
    .\deploy_agent.ps1 -ComputerName "zr-115","zr-116"
#>

param(
    [Parameter(ParameterSetName="Group")]
    [string]$GroupName,

    [Parameter(ParameterSetName="Computer", ValueFromPipeline=$true)]
    [string[]]$ComputerName,

    [string]$Source = "\\zr.local\netlogon\CyberAgent"
)

$Target = "C:\ProgramData\CyberAgent"
$Log = Join-Path $env:TEMP "CyberAgent_deploy.log"

function Write-Log {
    param([string]$Msg, [string]$Level="INFO", [string]$Computer)
    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Prefix = if ($Computer) { "[$Time] [$Level] [$Computer]" } else { "[$Time] [$Level]" }
    "$Prefix $Msg"
    "$Prefix $Msg" | Out-File -FilePath $Log -Append -Encoding UTF8
}

function Deploy-Computer {
    param([string]$Computer)

    Write-Log "Starting deployment..." -Computer $Computer

    if (-not (Test-Connection -ComputerName $Computer -Count 1 -Quiet)) {
        Write-Log "Computer offline (no ping)" -Level "WARN" -Computer $Computer
        return
    }

    $AdminShare = "\\$Computer\C$"
    $RemoteTarget = "$AdminShare\ProgramData\CyberAgent"

    try {
        Get-WmiObject -ComputerName $Computer -Query "SELECT * FROM Win32_Process WHERE Name='CyberAgent.exe'" |
            ForEach-Object { $_.Terminate() }
        Start-Sleep 1
    } catch {
        Write-Log "Process terminate warning: $_" -Level "WARN" -Computer $Computer
    }

    try {
        if (-not (Test-Path $RemoteTarget)) {
            New-Item -ItemType Directory -Path $RemoteTarget -Force | Out-Null
        }
        Copy-Item -Path "$Source\*" -Destination $RemoteTarget -Recurse -Force -ErrorAction Stop
        Write-Log "Files copied" -Computer $Computer
    } catch {
        Write-Log "Copy failed: $_" -Level "ERROR" -Computer $Computer
        return
    }

    try {
        $Result = ([wmiclass]"\\$Computer\root\cimv2:Win32_Process").Create(
            "$Target\CyberAgent.exe"
        )
        if ($Result.ReturnValue -eq 0) {
            Write-Log "CyberAgent.exe started" -Computer $Computer
        } else {
            Write-Log "Process start failed (code: $($Result.ReturnValue))" -Level "ERROR" -Computer $Computer
        }
    } catch {
        Write-Log "WMI start error: $_" -Level "ERROR" -Computer $Computer
    }
}

# === MAIN ===
Write-Log "=== CyberAgent Deploy ==="

if ($PSCmdlet.ParameterSetName -eq "Group") {
    Write-Log "Getting computers from group: $GroupName"
    try {
        $Computers = Get-ADGroupMember -Identity $GroupName |
            Where-Object { $_.objectClass -eq "computer" } |
            Select-Object -ExpandProperty Name

        if (-not $Computers) {
            Write-Log "No computers found in group: $GroupName" -Level "WARN"
            exit 1
        }
        Write-Log "Found $($Computers.Count) computer(s)"
    } catch {
        Write-Log "AD group lookup failed: $_" -Level "ERROR"
        exit 1
    }
} else {
    $Computers = $ComputerName
    Write-Log "Target computers: $($Computers -join ', ')"
}

foreach ($Computer in $Computers) {
    Deploy-Computer -Computer $Computer
}

Write-Log "=== Deploy Complete ==="
