[CmdletBinding()]
param(
    [string[]] $Skills,
    [string] $Destination,
    [switch] $Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$archiveUrl = if ([string]::IsNullOrWhiteSpace($env:COC7KPER_ARCHIVE_URL)) {
    'https://github.com/JWbo6/COC7Kper-skills/archive/refs/heads/main.zip'
} else {
    $env:COC7KPER_ARCHIVE_URL
}
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceRoot = Join-Path $scriptRoot 'skills'
$temporaryRoot = $null

try {
    if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
        $temporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("coc7kper-" + [guid]::NewGuid().ToString('N'))
        $archivePath = Join-Path $temporaryRoot 'bundle.zip'
        $extractRoot = Join-Path $temporaryRoot 'extract'
        New-Item -ItemType Directory -Path $temporaryRoot, $extractRoot | Out-Null
        Invoke-WebRequest -Uri $archiveUrl -OutFile $archivePath
        Expand-Archive -LiteralPath $archivePath -DestinationPath $extractRoot -Force
        $sourceRoot = Get-ChildItem -LiteralPath $extractRoot -Directory | Select-Object -First 1 | ForEach-Object { Join-Path $_.FullName 'skills' }
    }
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
} finally {
    if ($null -ne $temporaryRoot -and (Test-Path -LiteralPath $temporaryRoot)) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}
