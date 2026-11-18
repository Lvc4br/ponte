# Instalação — PONTE Gerenciador Universal de Dados e Documentos

## Pacote Windows

O pacote de validação será produzido pelo workflow [Validação e pacote Windows](../.github/workflows/build-windows.yml). Ele deve gerar o artefato `PONTE-Windows-Python313`. Não use artefatos antigos para atualizar a instalação.

O executável é `PONTE.exe`. Extraia o pacote em uma pasta com permissão de gravação.

## Dependências externas opcionais do scanner

- **Tesseract OCR:** necessário para OCR de páginas PDF digitalizadas e imagens. Instale o Tesseract no Windows e inclua os idiomas português e inglês.
- **LibreOffice:** necessário para ler DOC/PPT/RTF/ODT/ODP legados por conversão local.
- **ODA File Converter:** necessário para conversão DWG para DXF.
- **IfcOpenShell:** necessário para extração IFC avançada; depende de versão compatível com o Python usado no ambiente.

Sem essas ferramentas, os arquivos correspondentes são identificados e o scanner registra avisos; não significa que o conteúdo foi integralmente lido.

## Backup e restauração\n\nUse as opções **Criar backup do banco**, **Verificar backup** e **Restaurar backup** no menu principal. O backup gera um arquivo SQLite e um manifesto JSON. A restauração verifica o arquivo e cria uma cópia de segurança do banco atual antes de substituí-lo. Feche e reabra o aplicativo após restaurar.\n\nConsulte [Plano de testes de usuário](PLANO_TESTES_USUARIO.md) antes de validar a versão atualizada.\n\n## Dados locais

- `data/registros.sqlite3`: banco ativo do aplicativo, incluindo dados legados, catálogo documental e workspace genérico.
- `data/ponte.db`: base SQLite intermediária criada ao executar o SQL legado.
- `database/ponte.sql`: SQL real privado; não é distribuído no repositório.
- `database/ponte.sql.example`: modelo sem dados corporativos.

Antes de atualizar, feche o aplicativo e faça cópia de segurança do diretório `data` e de `database/ponte.sql`. Nunca substitua os dados locais pelo conteúdo do pacote.

## Instalação pelo código-fonte

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m compileall -q app tests main.py
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe main.py
```

## Gerar executável

Execute `build/build_windows.bat`. O resultado esperado é `dist/PONTE/PONTE.exe`. O build coleta os módulos Python; ferramentas externas como Tesseract, LibreOffice e ODA File Converter não são incorporadas automaticamente.

## Cuidados

- Não coloque SQL real, SQLite com dados reais ou planilhas internas no GitHub.
- Faça backup antes de mover, atualizar ou reinstalar o aplicativo.
- O executável ainda precisa de smoke test em Windows limpo e não possui assinatura digital.
