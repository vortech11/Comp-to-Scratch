# WARNING THIS BASH FILE WAS CREATED USING CHATGPT
# I DO NOT KNOW HOW TO WRITE BASH
# I DO NOT KNOW IF THIS WILL DO DAMAGE TO YOUR COMPUTER
# ok 🥰

$binary = "scratch.exe"
$installDir = "$env:LOCALAPPDATA\Programs\mycompiler"
$binPath = "$installDir\$binary"

Write-Host "Uninstalling mycompiler..."

if (Test-Path $binPath) {
    Remove-Item $binPath -Force
    Write-Host "Removed $binPath"
} else {
    Write-Host "Binary not found."
}

if (Test-Path $installDir) {
    Remove-Item $installDir -Force -Recurse
    Write-Host "Removed install directory."
}

# Remove from PATH
$path = [Environment]::GetEnvironmentVariable("PATH","User")

if ($path -like "*$installDir*") {
    $newPath = ($path -split ";") | Where-Object {$_ -ne $installDir}
    [Environment]::SetEnvironmentVariable(
        "PATH",
        ($newPath -join ";"),
        "User"
    )
}

Write-Host "Uninstall complete."
Write-Host "Restart your terminal."