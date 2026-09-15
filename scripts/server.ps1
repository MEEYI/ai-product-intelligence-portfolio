param([ValidateSet('Start', 'Stop', 'Status')][string]$Action = 'Start')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$statePath = Join-Path $projectRoot '.run\server.json'
$baseUrl = 'http://127.0.0.1:8000'

function Get-TrackedServer {
    if (-not (Test-Path -LiteralPath $statePath)) { return $null }
    $saved = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$saved.pid)"
    if ($process -and $process.ExecutablePath -ieq $pythonPath -and
        $process.CommandLine -match 'uvicorn backend\.main:app' -and
        $process.CreationDate.ToUniversalTime().ToString('o') -eq $saved.created) {
        return $process
    }
    return $null
}

function Test-ServerHealth {
    try {
        $result = Invoke-RestMethod -Uri "$baseUrl/" -TimeoutSec 2
        return $result.system -eq 'AI Product Intelligence' -and $result.status -eq 'running'
    } catch { return $false }
}

function Stop-TrackedServer($process) {
    # Only terminate the process tree whose path, command and creation time match.
    & "$env:SystemRoot\System32\taskkill.exe" /PID $process.ProcessId /T /F
    if ($LASTEXITCODE -ne 0) { throw 'Could not stop the tracked backend process.' }
    Remove-Item -LiteralPath $statePath -ErrorAction SilentlyContinue
}

$existing = Get-TrackedServer
if ($Action -eq 'Status') {
    if ($existing -and (Test-ServerHealth)) {
        Write-Output "Running: $baseUrl/docs (PID $($existing.ProcessId))"
        exit 0
    }
    Write-Output 'Backend is not running or is not healthy.'
    exit 1
}
if ($Action -eq 'Stop') {
    if ($existing) { Stop-TrackedServer $existing; Write-Output 'Backend stopped.' }
    else { Write-Output 'No backend managed by this project is running.' }
    exit 0
}
if ($existing) {
    if (Test-ServerHealth) { Write-Output "Already running: $baseUrl/docs"; exit 0 }
    throw 'The tracked backend is not healthy. Run stop.cmd, then start.cmd.'
}
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run setup.cmd first to create the Python environment.' }
$portCheck = New-Object System.Net.Sockets.TcpClient
try {
    $connected = $portCheck.ConnectAsync('127.0.0.1', 8000)
    try { $null = $connected.Wait(500) } catch { }
    if ($portCheck.Connected) { throw 'Port 8000 is already in use. Stop that service before starting this project.' }
} finally { $portCheck.Dispose() }
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot 'logs'),(Join-Path $projectRoot '.run') | Out-Null
$process = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'logs\server.out.log') -RedirectStandardError (Join-Path $projectRoot 'logs\server.err.log') -PassThru
$identity = Get-CimInstance Win32_Process -Filter "ProcessId = $($process.Id)"
if (-not $identity) { throw 'Backend exited at startup. See logs/server.err.log.' }
@{pid=$process.Id;created=$identity.CreationDate.ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if (Test-ServerHealth) { Write-Output "Started: $baseUrl/docs"; exit 0 }
    if ($process.HasExited) { throw 'Backend exited at startup. See logs/server.err.log.' }
    Start-Sleep -Milliseconds 500
}
Stop-TrackedServer $identity
throw 'Backend did not become healthy. See logs/server.err.log.'
