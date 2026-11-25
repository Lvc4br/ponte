@echo off
setlocal
cd /d "%~dp0.."

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

%PYTHON% -m PyInstaller --noconfirm --clean --windowed --onefile --name EGT --collect-all pypdf --collect-all pdfplumber --collect-all pyxlsb --collect-all docx --collect-all pptx --collect-all openpyxl --collect-all xlrd --collect-all ezdxf --collect-all pypdfium2 --collect-all pypdfium2_raw --collect-all pytesseract main.py
if errorlevel 1 exit /b %errorlevel%

if not exist "dist\EGT.exe" (
    echo ERRO: EGT.exe nao foi gerado.
    exit /b 1
)

echo.
echo Build concluido.
echo Arquivo unico: dist\EGT.exe
