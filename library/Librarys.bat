@echo off

:: 切换到前端目录并启动前端
start "Frontend" cmd /k "cd /d frontend && npm run dev"

:: 启动后端（假设 run.py 与本脚本在同级）
start "Backend" cmd /k "python run.py"

pause
