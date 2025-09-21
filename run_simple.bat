@echo off
echo 正在启动Python自动考试系统（简化版）...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 安装基础依赖
echo 正在安装基础依赖包...
pip install streamlit opencv-python numpy Pillow

if errorlevel 1 (
    echo.
    echo 警告：依赖包安装失败，尝试使用国内镜像源...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple streamlit opencv-python numpy Pillow
)

echo.
echo 依赖安装完成，正在启动考试系统（简化版）...
echo.
echo 系统将在浏览器中打开，请使用学号格式：20241315XXX
echo 密码与学号相同
echo.
echo 注意：此版本使用简化的人脸检测功能
echo.

REM 启动Streamlit应用（简化版）
streamlit run app_simple.py --server.port 8501 --server.address localhost

pause