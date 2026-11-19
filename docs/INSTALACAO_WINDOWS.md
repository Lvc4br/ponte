# Instalação — PONTE Windows (arquivo único)

## Entrega

A distribuição desta branch é **um único arquivo: PONTE.exe**. Não é necessário instalar Python, abrir scripts ou copiar uma pasta de bibliotecas. O workflow [Validação e executável Windows único](../.github/workflows/build-windows.yml) publica o artefato PONTE-Windows-OneFile.

Baixe somente o artefato gerado pelo workflow desta branch. Builds antigos no formato onedir não atendem ao requisito.

## Como usar

1. Salve PONTE.exe em uma pasta na qual seu usuário tenha permissão de gravação (por exemplo, Documentos\PONTE).
2. Execute o arquivo com duplo clique.
3. Na primeira execução, o aplicativo poderá criar a pasta data ao lado do executável para manter o banco SQLite local.
4. Não apague nem mova essa pasta enquanto quiser preservar os dados cadastrados. Para transferir a instalação, feche o PONTE e copie o executável e a pasta data juntos.
5. Antes de atualizar, feche o aplicativo e faça backup da pasta data.

**Importante:** o pacote distribuído contém apenas o executável. Os dados criados durante o uso são arquivos locais de trabalho e não fazem parte do binário. Esta versão local não é ainda o banco central multiusuário da EGT e não deve ser usada como compartilhamento simultâneo de um SQLite em pasta de rede.

## Recursos externos opcionais

Alguns formatos documentais dependem de ferramentas externas que não fazem parte do arquivo único:
- LibreOffice para conversão de DOC/PPT/RTF/ODT/ODP legados.
- ODA File Converter para conversão DWG para DXF.
- IfcOpenShell para extração IFC avançada.
- Tesseract OCR para reconhecimento de texto em imagens/PDFs digitalizados.

Sem essas ferramentas, os recursos associados podem ficar indisponíveis; o cadastro, a consulta e os fluxos que não dependem delas continuam sujeitos aos testes da versão.

## Dados legados

A aplicação pode procurar database/ponte.sql ao lado do executável para carregar uma fonte SQL legada. Esse arquivo não é incluído no executável e não deve ser distribuído sem autorização. Se a empresa precisar desse fluxo, a equipe deverá fornecer o arquivo aprovado separadamente.

## Compilação para desenvolvimento

No Windows, com Python 3.11+ e as dependências instaladas:

\`\`\`powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install --upgrade pip
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe -m compileall -q app tests main.py
.\\.venv\\Scripts\\python.exe -m pytest -v
.\\build\\build_windows.bat
\`\`\`

O resultado esperado é dist/PONTE.exe, sem diretório _internal ou DLLs distribuídas separadamente.

## Critérios obrigatórios antes de liberar para usuários

- Workflow Windows concluído com testes aprovados.
- Executável inicia em máquina Windows sem Python instalado.
- Teste de criação, edição, fechamento e reabertura dos dados locais.
- Teste de backup e restauração.
- Teste de atualização sem perda dos dados.
- Verificação de que o pacote contém somente PONTE.exe.
- Identificação da versão e registro dos problemas conhecidos.
- Teste em perfil de usuário sem privilégios administrativos.

O executável gerado por CI ainda precisa desses testes de aceitação em máquina Windows limpa antes de ser declarado pronto para produção.
