# Instalação — PONTE Gerenciador Universal de Dados e Documentos

## Versão portátil

1. Baixe o ZIP Windows x64 na página Releases e extraia-o em uma pasta com permissão de gravação.
2. Para inicializar a base a partir do SQL, copie o arquivo autorizado para database/ponte.sql.
3. Execute PONTE.exe.

O SQL real não é incluído no release. O modelo database/ponte.sql.example não contém dados corporativos.

## Arquivos locais de dados

- data/ponte.db: cópia SQLite intermediária criada ao validar e executar o SQL.
- data/registros.sqlite3: base ativa gerenciada pelo aplicativo, usada nos dados legados e no catálogo documental.
- data/registros.backup.sqlite3: backup criado antes da exclusão de registros.

Na primeira inicialização, os registros SQL são copiados para a base ativa se ela ainda estiver vazia. Depois disso, alterações feitas diretamente no SQL não são mescladas automaticamente. Faça backup de data/registros.sqlite3 antes de mover, reinstalar ou editar manualmente os arquivos.

## Importação e manutenção

A branch principal atual contém importação aditiva de planilhas .xlsx. O usuário seleciona a aba, confere uma prévia e confirma a inclusão. Também pode selecionar registros na tabela e excluí-los após confirmação.

O pacote publicado em v0.1.0 é anterior a essas funcionalidades. Consulte Releases para identificar o pacote mais recente.

## Executar pelo código-fonte

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe main.py
```

## Gerar executável local

Execute build/build_windows.bat. O diretório final será dist/PONTE, com o executável dist/PONTE/PONTE.exe.

## Scanner documental\n\nA interface permite analisar arquivos selecionados ou uma pasta inteira, consultar o conteúdo extraído e reabrir a biblioteca documental local. A leitura de PDF digitalizado e imagens usa OCR quando o Tesseract está instalado e configurado. DWG e RVT ainda não possuem leitor direto integrado.\n\n## Cuidados

- Não coloque SQL real, SQLite com dados reais ou planilhas internas no GitHub.
- Mantenha a pasta extraída em local com permissão de gravação.
- Faça backup dos dados locais antes de atualizar ou reinstalar o aplicativo.
- O executável ainda não possui assinatura digital de código; o Windows pode exibir um aviso de segurança.
