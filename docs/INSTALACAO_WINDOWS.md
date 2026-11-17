# Instalação — Consulta de Taxas de Pontes

## Versão portátil

1. Baixe o ZIP Windows x64 na página Releases e extraia-o em uma pasta com permissão de gravação.
2. Para inicializar a base a partir do SQL, copie o arquivo autorizado para database/ponte.sql.
3. Execute ConsultaTaxasPontes.exe.

O SQL real não é incluído no release. O modelo database/ponte.sql.example não contém dados corporativos.

## Arquivos locais de dados

- data/ponte.db: cópia SQLite intermediária criada ao validar e executar o SQL.
- data/registros.sqlite3: base ativa gerenciada pelo aplicativo, usada nas consultas, inclusões do Excel e exclusões.
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

Execute build/build_windows.bat. O diretório final será dist/ConsultaTaxasPontes.

## Cuidados

- Não coloque SQL real, SQLite com dados reais ou planilhas internas no GitHub.
- Mantenha a pasta extraída em local com permissão de gravação.
- Faça backup dos dados locais antes de atualizar ou reinstalar o aplicativo.
- O executável ainda não possui assinatura digital de código; o Windows pode exibir um aviso de segurança.
