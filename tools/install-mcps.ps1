#Requires -Version 5.1
[CmdletBinding()]
param(
    [string] $InstallRoot = (Join-Path $env:LOCALAPPDATA 'Bambu-X2D-MCP')
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Checked {
    param([string] $Program, [string[]] $Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Program failed with exit code $LASTEXITCODE."
    }
}

$servers = @(
    @{
        Name = 'freecad-mcp'
        Url = 'https://github.com/neka-nat/freecad-mcp.git'
        Revision = '246f608d5de49089aadc41d2d91cfce2ad8a44cd'
        Entry = '.venv\Scripts\freecad-mcp.exe'
    }
    @{
        Name = 'mcp-for-blender'
        Url = 'https://github.com/ahujasid/mcp-for-blender.git'
        Revision = 'a5a8acf2c6ae44a73670e0caf34663f16456d645'
        Entry = '.venv\Scripts\mcp-for-blender.exe'
    }
    @{
        Name = 'bambu-printer-mcp'
        Url = 'https://github.com/DMontgomery40/bambu-printer-mcp.git'
        Revision = '9a590fbd1e83e875ef093fc2093d9a021161ef95'
        Entry = 'dist\index.js'
    }
)

foreach ($program in 'git.exe', 'uv.exe', 'node.exe', 'npm.cmd') {
    Get-Command $program -CommandType Application -ErrorAction Stop | Out-Null
}
$InstallRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($InstallRoot)
[IO.Directory]::CreateDirectory($InstallRoot) | Out-Null

foreach ($server in $servers) {
    $checkout = Join-Path $InstallRoot $server.Name
    Write-Host "Preparing $($server.Name) at $($server.Revision)"
    if (-not (Test-Path -LiteralPath $checkout)) {
        Invoke-Checked git.exe @('init', '--quiet', $checkout)
        Invoke-Checked git.exe @('-C', $checkout, 'remote', 'add', 'origin', $server.Url)
    }
    if (-not (Test-Path -LiteralPath (Join-Path $checkout '.git') -PathType Container)) {
        throw "Choose another -InstallRoot. This directory already exists: $checkout"
    }
    $origin = Invoke-Checked git.exe @('-C', $checkout, 'remote', 'get-url', 'origin')
    if ($origin -cne $server.Url) {
        throw "The existing checkout at $checkout has a different origin. Choose another -InstallRoot."
    }
    $head = & git.exe -C $checkout rev-parse --verify --quiet HEAD
    if ($LASTEXITCODE -ne 0) {
        $existing = @(Get-ChildItem -LiteralPath $checkout -Force | Where-Object Name -ne '.git')
        if ($existing.Count) { throw "The checkout has no commit and contains other files: $checkout" }
        Invoke-Checked git.exe @('-C', $checkout, 'fetch', '--depth=1', 'origin', $server.Revision)
        Invoke-Checked git.exe @('-C', $checkout, 'checkout', '--quiet', '--detach', 'FETCH_HEAD')
        $head = Invoke-Checked git.exe @('-C', $checkout, 'rev-parse', 'HEAD')
    }
    # TypeScript writes LF output even when Git checks out the tracked dist files as CRLF.
    # Compare Git content and the index so a repeat build recognizes the same revision.
    & git.exe -C $checkout -c core.safecrlf=false diff --quiet HEAD --
    $worktreeChanged = $LASTEXITCODE -ne 0
    & git.exe -C $checkout diff --cached --quiet --
    $indexChanged = $LASTEXITCODE -ne 0
    $untracked = @(Invoke-Checked git.exe @('-C', $checkout, 'ls-files', '--others', '--exclude-standard'))
    if ($head -cne $server.Revision -or $worktreeChanged -or $indexChanged -or $untracked.Count) {
        throw "The checkout has a different revision or local changes: $checkout. Choose another -InstallRoot to keep it."
    }

    Push-Location -LiteralPath $checkout
    try {
        if ($server.Name -eq 'bambu-printer-mcp') {
            Invoke-Checked npm.cmd @('ci', '--include=dev', '--no-audit', '--no-fund')
            Invoke-Checked npm.cmd @('run', 'build')
        } else {
            Invoke-Checked uv.exe @('sync', '--locked', '--no-dev', '--python', '3.12', '--no-editable')
        }
        $entry = Join-Path $checkout $server.Entry
        if (-not (Test-Path -LiteralPath $entry -PathType Leaf)) { throw "Missing built entry point: $entry" }
        Write-Host "Built $entry"
    } finally {
        Pop-Location
    }
}
Write-Host 'Continue with the Windows setup guide to enable the GUI add-ons and register the servers in your MCP client.'
