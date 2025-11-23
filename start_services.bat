@echo off

REM --- 请根据您的实际路径设置虚拟环境目录 ---
set "VENV_PATH=D:\Python\tiktok_pm\venv"

REM --- 1. 激活虚拟环境 (可选，如果您的命令行窗口已在 venv 中可注释掉) ---
echo 1. Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"

REM --- 2. 启动 QCluster Worker (在新的窗口中) ---
echo 2. Starting Django QCluster Worker...
start "QCluster Worker" cmd /k "python manage.py qcluster"

REM --- 3. 启动 Web Server (在新的窗口中) ---
echo 3. Starting Django Web Server...
start "Web Server" cmd /k "python manage.py runserver"

echo.
echo =========================================================
echo Both services are now running in two separate new windows.
echo Please monitor the log output in those windows.
echo =========================================================
pause