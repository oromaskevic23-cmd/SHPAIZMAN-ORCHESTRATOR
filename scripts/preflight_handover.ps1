#requires -Version 5.1
<#
.SYNOPSIS
  Read-only Enterprise admission: validate separately received SHPAIZMAN ZIP.
.DESCRIPTION
  Does NOT unpack, run, install or connect code. Requires explicit ZIP input.
  The external SHA256 pin must be obtained from an authorized independent channel.
.EXAMPLE
  powershell -NoProfile -File .\scripts\preflight_handover.ps1 -ArchivePath "$env:USERPROFILE\Downloads\SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip"
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [string]$ArchivePath,
  [Parameter(Mandatory=$false)]
  [ValidatePattern('^[a-fA-F0-9]{64}$')]
  [string]$ExpectedSha256='9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
try {
  if (-not [Environment]::Is64BitOperatingSystem) { throw 'WINDOWS_X64_REQUIRED' }
  if ($PSVersionTable.PSEdition -eq 'Core' -and -not $IsWindows) {
    throw 'WINDOWS_REQUIRED'
  }
  $archive = (Resolve-Path -LiteralPath $ArchivePath -ErrorAction Stop).ProviderPath
  if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {
    throw 'ARCHIVE_NOT_FOUND'
  }
  $computed = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($computed -cne $ExpectedSha256.ToLowerInvariant()) { throw 'ZIP_SHA256_MISMATCH' }
  $repoRoot = Split-Path -Parent $PSScriptRoot
  if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'enterprise\verify_release.py'))) {
    throw 'GITHUB_SOURCE_VERIFIER_NOT_FOUND'
  }
  & py -3.12 -c 'import sys,sqlite3,tkinter; assert sys.version_info[:2] == (3,12)'
  if ($LASTEXITCODE -ne 0) { throw 'PYTHON_312_TKINTER_REQUIRED' }
  Push-Location $repoRoot
  try {
    & py -3.12 -m enterprise.verify_release --zip-path $archive --expected-sha256 $computed
    if ($LASTEXITCODE -ne 0) { throw 'SOURCE_ZIP_INTERNAL_VERIFICATION_FAILED' }
  }
  finally { Pop-Location }
  Write-Host '[PASS] ZIP hash, archive manifest, 10 agent source files and Windows Python prerequisites.'
  Write-Host '[NEXT] Review docs\WINDOWS_DEVELOPER_SETUP_RU.md and obtain brother approval before unpack/install.'
  Write-Host '[DENIED] No program execution, third-party account access or MetaMask transfer has occurred.'
  exit 0
} catch {
  Write-Error ('[BLOCKED] ' + $_.Exception.Message)
  exit 1
}
