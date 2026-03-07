# WARNING THIS BASH FILE WAS CREATED USING CHATGPT
# I DO NOT KNOW HOW TO WRITE BASH
# I DO NOT KNOW IF THIS WILL DO DAMAGE TO YOUR COMPUTER
# ok 🥰

$repo = "vortech11/Comp-to-Scratch"
$binary = "scratch.exe"

$installDir = "$env:LOCALAPPDATA\Programs\mycompiler"
$binPath = "$installDir\$binary"

Write-Host "Installing $binary..."

# Create directory
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# Get latest release
$release = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest"

$asset = $release.assets | Where-Object { $_.name -like "*windows-x86_64.exe" }

if (!$asset) {
    Write-Error "Windows binary not found in latest release."
    exit 1
}

$temp = "$env:TEMP\$binary"

Write-Host "Downloading..."
Invoke-WebRequest $asset.browser_download_url -OutFile $temp

Move-Item $temp $binPath -Force

# Add to PATH
$path = [Environment]::GetEnvironmentVariable("PATH", "User")

if ($path -notlike "*$installDir*") {
    [Environment]::SetEnvironmentVariable(
        "PATH",
        "$path;$installDir",
        "User"
    )
}

Write-Host "Installed to $binPath"
Write-Host "Restart your terminal to use the compiler."