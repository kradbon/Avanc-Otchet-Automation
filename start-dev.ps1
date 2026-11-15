$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$backendPython = Join-Path $backendDir ".venv\Scripts\python.exe"
$frontendDir = Join-Path $root "frontend"

function Stop-PortListener([int]$Port) {
  $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

  foreach ($pid in $connections) {
    if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
      Stop-Process -Id $pid -Force
    }
  }
}

Stop-PortListener 8000
Stop-PortListener 5173

if (-not (Test-Path $backendPython)) {
  Write-Error "Backend virtual environment not found at $backendPython. Run: cd backend; python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
  exit 1
}

Write-Host "Starting backend on http://127.0.0.1:8000 ..."
$backend = Start-Process $backendPython `
  -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' `
  -WorkingDirectory $backendDir `
  -WindowStyle Hidden `
  -PassThru

Start-Sleep -Seconds 2

try {
  Write-Host "Starting frontend on http://127.0.0.1:5173 ..."
  Set-Location $frontendDir
  & npm.cmd run dev -- --host 127.0.0.1
}
finally {
  if ($backend -and -not $backend.HasExited) {
    Stop-Process -Id $backend.Id -Force
  }
}
