@echo off
chcp 65001 >nul
echo ========================================
echo    Library 前端启动脚本
echo ========================================
echo.

REM 检查Node.js是否安装
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Node.js，请先安装Node.js 20.19+ 或 22.12+
    pause
    exit /b 1
)

REM 检查npm是否安装
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到npm，请确保Node.js已正确安装
    pause
    exit /b 1
)

echo [信息] 正在检查依赖...
echo.

REM 检查前端依赖
set "FRONTEND_DIR=%~dp0frontend"
if not exist "%FRONTEND_DIR%\package.json" (
    echo [错误] 前端目录中未找到 package.json 文件: %FRONTEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo [警告] 前端依赖未安装，正在安装...
    cd /d "%FRONTEND_DIR%"
    call npm install
    if %errorlevel% neq 0 (
        echo [错误] 前端依赖安装失败
        pause
        exit /b 1
    )
    echo [信息] 前端依赖安装完成
) else (
    echo [信息] 前端依赖已安装
)

echo.
echo ========================================
echo    正在启动前端服务...
echo ========================================
echo.

REM 启动前端
echo [信息] 正在启动前端服务 - 端口 5173
echo [信息] 前端目录: %FRONTEND_DIR%
start "Library-Frontend" cmd /k "cd /d \"%FRONTEND_DIR%\" && npm run dev"
echo [信息] 前端窗口已打开
echo.

echo ========================================
echo    前端启动完成！
echo ========================================
echo.
echo 前端服务: http://localhost:5173
echo.
echo 提示:
echo - 前端已在新窗口中启动
echo - 关闭前端窗口即可停止服务
echo - 确保后端服务已启动 - http://localhost:5000
echo.
echo 按任意键关闭此窗口...
pause >nul

