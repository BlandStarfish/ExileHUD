@echo off
echo ============================================
echo   ExileHUD Installer Builder
echo ============================================
echo.

:: Inject current password hash from installer_password.json into installer_gui.py
python inject_password.py
if errorlevel 1 (
    echo [ERROR] Password injection failed. Run set_password.py first.
    pause & exit /b 1
)

:: Check / install PyInstaller
where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller --quiet
)

:: Build
python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name "ExileHUD-Setup" ^
    --icon "assets\icon.ico" ^
    installer_gui.py

echo.
if exist "dist\ExileHUD-Setup.exe" (
    :: Zip it
    python -c "import zipfile,os; z=zipfile.ZipFile('ExileHUD-Setup.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9); z.write('dist/ExileHUD-Setup.exe','ExileHUD-Setup.exe'); z.close(); print(f'ZIP: {os.path.getsize(chr(34)+\"ExileHUD-Setup.zip\"+chr(34))/1024/1024:.1f} MB')"
    echo.
    echo SUCCESS: ExileHUD-Setup.zip is ready to share.
) else (
    echo FAILED: check output above for errors.
)
pause
