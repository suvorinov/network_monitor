<#
.SYNOPSIS
    Remove CyberAgent from domain computers via AD group or computer name.
.DESCRIPTION
    Terminates CyberAgent.exe and deletes C:\ProgramData\CyberAgent
    from target machines.
.PARAMETER GroupName
    AD group name (e.g. "Workstations_Finance").
.PARAMETER ComputerName
    Single computer name or array (e.g. "zr-115").
.EXAMPLE
    .\remove_agent.ps1 -GroupName "Workstations_Finance"
.EXAMPLE
    .\remove_agent.ps1 -ComputerName "zr-115"
.EXAMPLE
    .\remove_agent.ps1 -ComputerName "zr-115","zr-116"
#>

param(
    [Parameter(ParameterSetName="Group")]
    [string]$GroupName,

    [Parameter(ParameterSetName="Computer", ValueFromPipeline=$true)]
    [string[]]$ComputerName
)

$Target = "C:\ProgramData\CyberAgent"
$Log = Join-Path $env:TEMP "CyberAgent_remove.log"

function Write-Log {
    param([string]$Msg, [string]$Level="INFO", [string]$Computer)
    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Prefix = if ($Computer) { "[$Time] [$Level] [$Computer]" } else { "[$Time] [$Level]" }
    "$Prefix $Msg"
    "$Prefix $Msg" | Out-File -FilePath $Log -Append -Encoding UTF8
}

function Remove-Computer {
    param([string]$Computer)

    Write-Log "Starting removal..." -Computer $Computer

    if (-not (Test-Connection -ComputerName $Computer -Count 1 -Quiet)) {
        Write-Log "Computer offline (no ping)" -Level "WARN" -Computer $Computer
        return
    }

    $AdminShare = "\\$Computer\C$"
    $RemoteTarget = "$AdminShare\ProgramData\CyberAgent"

    try {
        Get-WmiObject -ComputerName $Computer -Query "SELECT * FROM Win32_Process WHERE Name='CyberAgent.exe'" |
            ForEach-Object { $_.Terminate() }
        Write-Log "Process terminated" -Computer $Computer
    } catch {
        Write-Log "Process terminate warning (maybe not running): $_" -Level "WARN" -Computer $Computer
    }

    Start-Sleep 1

    try {
        if (Test-Path $RemoteTarget) {
            Remove-Item -Path $RemoteTarget -Recurse -Force -ErrorAction Stop
            Write-Log "Folder removed: $RemoteTarget" -Computer $Computer
        } else {
            Write-Log "Folder not found, nothing to remove" -Computer $Computer
        }
    } catch {
        Write-Log "Remove failed: $_" -Level "ERROR" -Computer $Computer
    }
}

# === MAIN ===
Write-Log "=== CyberAgent Remove ==="

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
    Remove-Computer -Computer $Computer
}

Write-Log "=== Remove Complete ==="
