# 设置 Node.js 环境变量
$nodePath = "C:\Program Files\nodejs"
$npmPath = "C:\Users\$env:USERNAME\AppData\Roaming\npm"

# 更新系统 PATH
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$nodePath*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$currentPath;$nodePath;$npmPath", "User")
    Write-Host "Node.js and npm added to PATH" -ForegroundColor Green
} else {
    Write-Host "Node.js already in PATH" -ForegroundColor Yellow
}

# 设置当前会话的环境变量
$env:Path = "$env:Path;$nodePath;$npmPath"

Write-Host "Environment setup complete!" -ForegroundColor Green
Write-Host "Node.js version: " -NoNewline
& "$nodePath\node.exe" --version
Write-Host "npm version: " -NoNewline
& "$nodePath\npm.cmd" --version
Write-Host "pnpm version: " -NoNewline
& "$npmPath\pnpm.cmd" --version
