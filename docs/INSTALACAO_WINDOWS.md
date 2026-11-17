# Instalação — Consulta de Taxas de Pontes

## Versão portátil

1. Baixe o ZIP Windows x64 na página Releases e extraia-o em uma pasta com permissão de gravação.
2. Copie o SQL autorizado para database\ponte.sql.
3. Execute ConsultaTaxasPontes.exe.

O SQL real não é incluído no release. O modelo database\ponte.sql.example não contém a base corporativa. O aplicativo cria data\ponte.db na pasta da distribuição.

## Executar pelo código-fonte

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m pytest -v
    .\.venv\Scripts\python.exe main.py

## Gerar executável local

Execute build\build_windows.bat. O diretório final será dist\ConsultaTaxasPontes.

## Cuidados

- Não coloque o SQL real, SQLite com dados reais ou planilhas internas no GitHub.
- Mantenha a pasta extraída em local com permissão de gravação; o programa cria data\ponte.db ao lado do executável.
- Faça backup do arquivo SQL original antes de editar.
- O executável ainda não possui assinatura digital de código; o Windows pode exibir um aviso de segurança.
