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
%PYCMD% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo Package installation failed.
    pause
    exit /b 1
)
%PYCMD% -m PyInstaller --noconfirm --clean --onefile --windowed --name TraceNest main.py
if errorlevel 1 (
    echo EXE build failed; see output above.
    pause
    exit /b 1
)
echo Built: dist\TraceNest.exe
pause
endlocal
