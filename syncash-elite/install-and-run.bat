@echo off
echo Installing SynCash Elite dependencies...
echo.

cd /d "%~dp0"

echo Installing npm packages...
npm install

if %errorlevel% neq 0 (
    echo.
    echo Error installing packages. Trying alternative method...
    echo.
    npm install clsx@^2.0.0 tailwind-merge@^2.0.0
)

echo.
echo Starting development server...
echo.
echo SynCash Elite will be available at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev

pause
