# 抖音短视频批量下载工具 - PowerShell 启动脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   抖音短视频批量下载工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 激活 conda 环境
conda activate data_env
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 无法激活 conda 环境 data_env" -ForegroundColor Red
    Write-Host "请先运行: conda init powershell" -ForegroundColor Yellow
    Read-Host "按回车退出"
    exit 1
}

# 检查并安装依赖
Write-Host "[检查] 验证依赖..." -ForegroundColor Blue
$missing = python -c "import httpx, rich, browser_cookie3; print('OK')" 2>&1
if ($missing -ne "OK") {
    Write-Host "[提示] 正在安装依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# 启动主程序
Set-Location $PSScriptRoot
python main.py

Read-Host "按回车退出"
