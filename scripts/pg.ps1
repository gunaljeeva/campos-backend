# Start/stop the embedded CampOS dev Postgres (port 5433).
# Usage: .\scripts\pg.ps1 start   |   .\scripts\pg.ps1 stop   |   .\scripts\pg.ps1 status
param([Parameter(Mandatory = $true)][ValidateSet("start", "stop", "status")][string]$Action)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pgCtl = Join-Path $root ".pgdev\pgsql\bin\pg_ctl.exe"
$data  = Join-Path $root ".pgdev\data"
$log   = Join-Path $root ".pgdev\pg.log"

switch ($Action) {
    "start"  { & $pgCtl -D $data -l $log -o "-p 5433" start }
    "stop"   { & $pgCtl -D $data stop -m fast }
    "status" { & $pgCtl -D $data status }
}
