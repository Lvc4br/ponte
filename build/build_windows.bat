@echo off
setlocal
cd /d "%~dp0.."

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

%PYTHON% -m PyInstaller --noconfirm --clean --windowed --onedir --name PONTE --collect-all pypdf --collect-all pdfplumber --collect-all pyxlsb --collect-all docx --collect-all pptx --collect-all openpyxl --collect-all xlrd --collect-all ezdxf --collect-all pypdfium2 --collect-all pypdfium2_raw --collect-all pytesseract --add-data "database\ponte.sql.example;database" main.py
if errorlevel 1 exit /b %errorlevel%

if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" (
    xcopy /E /I /Y "%ProgramFiles%\Tesseract-OCR" "dist\PONTE\Tesseract-OCR" >nul
)

if not exist "dist\PONTE\database" mkdir "dist\PONTE\database"
copy /Y "database\ponte.sql.example" "dist\PONTE\database\ponte.sql.example" >nul
copy /Y "README.md" "dist\PONTE\LEIA-ME.txt" >nul

echo.
echo Build concluido: PONTE - Gerenciador Universal de Dados e Documentos
echo Executavel: dist\PONTE\PONTE.exe
echo Copie database\ponte.sql para dist\PONTE\database\ponte.sql
