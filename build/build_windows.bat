@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale Python 3.11+ ou crie .venv.
    exit /b 1
)

echo [1/4] Verificando dependencias de build...
%PYTHON% -m pip install --upgrade pyinstaller
if errorlevel 1 exit /b %errorlevel%

echo [2/4] Executando testes...
%PYTHON% -m pytest -q
if errorlevel 1 (
    echo ERRO: os testes falharam. O executavel nao sera gerado.
    exit /b %errorlevel%
)

echo [3/4] Limpando builds anteriores...
if exist build\EGT rmdir /s /q build\EGT
if exist dist\EGT.exe del /q dist\EGT.exe
if not exist dist mkdir dist

echo [4/4] Gerando EGT.exe em arquivo unico...
set "TESSERACT_ARGS="
if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" (
    set TESSERACT_ARGS=--add-data "%ProgramFiles%\Tesseract-OCR;Tesseract-OCR"
)

%PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --name EGT ^
    --collect-all pypdf --collect-all pdfplumber --collect-all pyxlsb ^
    --collect-all docx --collect-all pptx --collect-all openpyxl ^
    --collect-all xlrd --collect-all ezdxf --collect-all pypdfium2 ^
    --collect-all pypdfium2_raw --collect-all pytesseract --collect-all matplotlib --collect-all reportlab ^
    --collect-submodules app ^
    --add-data "database\ponte.sql.example;database" ^
    %TESSERACT_ARGS% ^
    main.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo BUILD CONCLUIDO.
echo Executavel: dist\EGT.exe
echo.
echo O banco de dados local sera criado na pasta data ao lado do EGT.exe.
echo Para usar OCR em PDFs digitalizados e imagens, o Tesseract deve estar
echo instalado no computador ou ter sido incluido durante este build.
endlocal
