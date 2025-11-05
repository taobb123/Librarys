@echo off
chcp 65001 >nul
echo ========================================
echo    Library 后端启动脚本
echo ========================================
echo.

REM 检查Python是否安装
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [信息] 正在检查依赖...
echo.

REM 检查Python依赖
if not exist "requirements.txt" (
    echo [警告] 未找到 requirements.txt 文件
) else (
    echo [信息] 检测到 requirements.txt，请确保已运行: pip install -r requirements.txt
)

echo.
echo ========================================
echo    正在启动后端服务...
echo ========================================
echo.

REM 获取当前脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 启动后端
echo [信息] 正在启动后端服务 (端口 5000)...
echo [信息] 后端目录: %SCRIPT_DIR%
start "Library-Backend" cmd /k "cd /d \"%SCRIPT_DIR%\" && python run.py"
echo [信息] 后端窗口已打开
echo.

echo ========================================
echo    后端启动完成！
echo ========================================
echo.
echo 后端服务: http://localhost:5000
echo.
echo 提示：
echo - 后端已在新窗口中启动
echo - 关闭后端窗口即可停止服务
echo - 请确保MySQL服务已启动并配置正确
echo.
echo 按任意键关闭此窗口...
pause >nul

