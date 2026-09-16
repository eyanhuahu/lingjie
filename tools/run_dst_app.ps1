# 用 DST Mod Tool（dst-app）跑一段 Lua 脚本，并把它的 JSON 报告打印出来。
#
# 为什么需要这个封装：
#   1) dst-app 每次启动都会联网检查更新 —— 这里把更新清单和代理全部指到 9 号 discard
#      端口，保证它发不出任何外部请求（本地地址走 NO_PROXY，不影响它自己的 IPC）。
#   2) dst-app 打完报告**不会自己退出**，主实例会常驻并保留文档（下次运行还会带着
#      上次导入的资源，导致符号跨包串图）。所以这里收尾时统一清掉进程。
#
# 用法：
#   pwsh -File tools/run_dst_app.ps1 -LuaFile .work/batch_export.lua
#   pwsh -File tools/run_dst_app.ps1 -LuaFile x.lua -DstApp "D:\path\dst-app.exe"
#
# 参数：
#   -LuaFile   要执行的 Lua 脚本（绝对路径或相对当前目录）
#   -DstApp    dst-app.exe 的路径，默认 C:\Users\huan\Downloads\dst-app.exe
#   -Timeout   等待报告的最长秒数，默认 300
#   -RawJson   只打印原始 JSON，不解析
param(
    [Parameter(Mandatory = $true)][string]$LuaFile,
    [string]$DstApp = "C:\Users\huan\Downloads\dst-app.exe",
    [int]$Timeout = 300,
    [switch]$RawJson
)

if (-not (Test-Path $LuaFile)) { Write-Error "找不到 Lua 脚本：$LuaFile"; exit 2 }
if (-not (Test-Path $DstApp)) { Write-Error "找不到 dst-app：$DstApp"; exit 2 }

$luaFull = (Resolve-Path $LuaFile).Path
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("dstapp-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$out = Join-Path $tmp "stdout.json"
$err = Join-Path $tmp "stderr.txt"

$env:DST_UPDATE_MANIFEST_URL = "http://127.0.0.1:9/none.json"
$env:HTTP_PROXY = "http://127.0.0.1:9"
$env:HTTPS_PROXY = "http://127.0.0.1:9"
$env:ALL_PROXY = "http://127.0.0.1:9"
$env:NO_PROXY = "127.0.0.1,localhost"

Start-Process -FilePath $DstApp -ArgumentList @("script", "--bypass", "--file", $luaFull) `
    -RedirectStandardOutput $out -RedirectStandardError $err | Out-Null

$deadline = (Get-Date).AddSeconds($Timeout)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 400
    if ((Test-Path $out) -and (Get-Item $out).Length -gt 0) { break }
}
Start-Sleep -Milliseconds 1000

# 收尾：dst-app 常驻不退，必须清掉（顺带清掉它残留的文档状态）
Get-Process dst-app -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

$raw = if (Test-Path $out) { (Get-Content $out -Raw) } else { "" }
if (-not $raw) { Write-Host "(没有拿到报告)"; if (Test-Path $err) { Get-Content $err -Raw }; exit 1 }

if ($RawJson) {
    Write-Output $raw
} else {
    try {
        $report = ($raw | ConvertFrom-Json).response.report
        if ($report.output) { $report.output | ForEach-Object { $_ } }
        if ($report.error) { Write-Host "!! error:" ($report.error | ConvertTo-Json -Compress) }
        $tr = $report.tool_results
        if ($tr) {
            $bad = @($tr | Where-Object { -not $_.ok })
            if ($bad.Count -gt 0) { Write-Host ("!! 有 {0} 个导出/工具命令失败" -f $bad.Count) }
        }
    } catch {
        Write-Host "JSON 解析失败，原样输出："
        Write-Output $raw
    }
}

if ((Test-Path $err) -and (Get-Item $err).Length -gt 0) {
    $errText = Get-Content $err -Raw
    if ($errText -notmatch "INFO \[dst_app::logging\]") {
        Write-Host "--- stderr ---"
        Write-Host $errText
    }
}

Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
