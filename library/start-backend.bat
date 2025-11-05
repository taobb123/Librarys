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
REM 移除末尾的反斜杠（如果存在）
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

REM 设置聚合数据API密钥
set JUHE_API_KEY=d309075150e27978571dcb7d8c48bacc

REM 可选：启用第三方API聚合平台
REM set USE_THIRD_PARTY_API=true

REM 启动后端
echo [信息] 正在启动后端服务 - 端口 5000
echo [信息] 项目根目录: %SCRIPT_DIR%
echo [信息] 后端目录: %SCRIPT_DIR%\backend
echo [信息] 已配置聚合数据API密钥: JUHE_API_KEY
echo.

REM 启动后端（使用run.py从项目根目录启动，这样可以正确设置环境变量）
REM 构建启动命令，确保路径正确转义
start "Library-Backend" cmd /k "cd /d \"%SCRIPT_DIR%\" && set JUHE_API_KEY=d309075150e27978571dcb7d8c48bacc && python run.py"
echo [信息] 后端窗口已打开
echo.

echo ========================================
echo    后端启动完成！
echo ========================================
echo.
echo 后端服务: http://localhost:5000
echo.
echo 提示:
echo - 后端已在新窗口中启动
echo - 关闭后端窗口即可停止服务
echo - 请确保MySQL服务已启动并配置正确
echo.
echo 按任意键关闭此窗口...
pause >nul

