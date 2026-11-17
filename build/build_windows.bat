@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado.
    echo Execute primeiro a instalacao descrita em docs\INSTALACAO_WINDOWS.md.
    exit /b 1
)

.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name ConsultaTaxasPontes --add-data "database\ponte.sql.example;database" main.py
if errorlevel 1 exit /b %errorlevel%

if not exist "dist\ConsultaTaxasPontes\database" mkdir "dist\ConsultaTaxasPontes\database"
copy /Y "database\ponte.sql.example" "dist\ConsultaTaxasPontes\database\ponte.sql.example" >nul
copy /Y "README.md" "dist\ConsultaTaxasPontes\LEIA-ME.txt" >nul

echo.
echo Build concluido: Consulta de Taxas de Pontes`r`necho Executavel: dist\ConsultaTaxasPontes\ConsultaTaxasPontes.exe
echo Copie database\ponte.sql para dist\ConsultaTaxasPontes\database\ponte.sql
