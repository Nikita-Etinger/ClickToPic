@echo off
python --version >nul 2>&1 || (
    echo Python не найден. Установите Python 3.10+ и добавьте его в PATH.
    pause
    exit /b
)

echo Установка библиотек...
pip install -r requirements.txt
echo Готово.
pause
