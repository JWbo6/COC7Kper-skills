[CmdletBinding()]
param(
    [string[]] $Skills,
    [string] $Destination,
    [switch] $Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceRoot = Join-Path $scriptRoot 'skills'
if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    throw "skills directory not found: $sourceRoot"
}

if ([string]::IsNullOrWhiteSpace($Destination)) {
    if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        $Destination = Join-Path $env:CODEX_HOME 'skills'
    } else {
        $Destination = Join-Path $HOME '.codex\skills'
    }
}

$available = @(Get-ChildItem -LiteralPath $sourceRoot -Directory | Sort-Object Name)
if ($null -eq $Skills -or $Skills.Count -eq 0) {
    $Skills = @($available.Name)
}

New-Item -ItemType Directory -Path $Destination -Force | Out-Null
foreach ($skill in $Skills) {
    $source = Join-Path $sourceRoot $skill
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "unknown skill: $skill"
    }
    $manifest = Join-Path $source 'SKILL.md'
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf) -and $skill -ne 'coc-shared') {
        throw "missing SKILL.md: $source"
    }

    $target = Join-Path $Destination $skill
    if ((Test-Path -LiteralPath $target) -and -not $Force) {
        Write-Host "skip existing: $target"
        continue
    }
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    Copy-Item -LiteralPath $source -Destination $Destination -Recurse -Force
    Write-Host "installed: $target"
}

Write-Host ""
Write-Host "Installed into: $Destination"
Write-Host "Restart Codex/ZCode to discover the skills."
