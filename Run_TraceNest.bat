@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=py -3"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python 3 is required. Install Python from python.org first.
        pause
        exit /b 1
    )
    set "PYCMD=python"
)
%PYCMD% -c "import psutil; import watchdog" >nul 2>&1
if errorlevel 1 (
    echo Installing required Python packages...
    %PYCMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Package installation failed. Check your internet connection.
        pause
        exit /b 1
    )
)
echo Starting TraceNest...
%PYCMD% main.py
if errorlevel 1 (
    echo TraceNest stopped with an error. Read the message above.
    pause
)
endlocal
