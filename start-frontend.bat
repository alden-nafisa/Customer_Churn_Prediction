@echo off
REM ============================================
REM Frontend Setup & Start Script
REM Windows Batch File
REM ============================================

echo.
echo  ========================================
echo  Frontend Setup Script
echo  ========================================
echo.

REM Get the directory where this script is located
cd /d "%~dp0"

echo [Step 1] Cleaning up old files...
if exist "frontend\src\components\MockData.js" (
    del "frontend\src\components\MockData.js"
    echo   ✓ Deleted MockData.js
)
if exist "frontend\src\components\PredictionView_New.jsx" (
    del "frontend\src\components\PredictionView_New.jsx"
    echo   ✓ Deleted PredictionView_New.jsx
)
if exist "frontend\src\components\SentimentView_New.jsx" (
    del "frontend\src\components\SentimentView_New.jsx"
    echo   ✓ Deleted SentimentView_New.jsx
)

echo.
echo [Step 2] Verifying component files...
if exist "frontend\src\components\MockData.jsx" (
    echo   ✓ MockData.jsx
) else (
    echo   ✗ MockData.jsx NOT FOUND
    goto error
)
if exist "frontend\src\components\PredictionView.jsx" (
    echo   ✓ PredictionView.jsx
) else (
    echo   ✗ PredictionView.jsx NOT FOUND
    goto error
)
if exist "frontend\src\components\SentimentView.jsx" (
    echo   ✓ SentimentView.jsx
) else (
    echo   ✗ SentimentView.jsx NOT FOUND
    goto error
)

echo.
echo [Step 3] Starting development server...
echo.
cd frontend
npm run dev

goto end

:error
echo.
echo ✗ Setup failed - some files are missing!
pause
exit /b 1

:end
