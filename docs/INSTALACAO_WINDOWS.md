# Instalação no Windows

## Preparar o ambiente

No PowerShell, na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Preparar a base SQL

```powershell
Copy-Item .\database\ponte.sql.example .\database\ponte.sql
notepad .\database\ponte.sql
```

Edite o arquivo com os comandos SQL e os dados autorizados. Não publique `database/ponte.sql`.

## Executar

```powershell
.\.venv\Scripts\python.exe main.py
```

O aplicativo reconstrói `data/ponte.db` ao iniciar e ao usar o botão **Recarregar arquivo SQL**.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

A geração do executável ainda requer configuração adicional para empacotar o script SQL local.
