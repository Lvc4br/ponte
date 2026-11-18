# PONTE — Gerenciador Universal de Dados e Documentos

Aplicativo desktop Windows, local-first, para organizar dados e documentos de projetos de diferentes áreas. O produto não é limitado a pontes ou engenharia: a base de pontes existente permanece como um conjunto de dados legado.

O objetivo é substituir uma parcela relevante dos fluxos de planilhas com tabelas próprias, tipos de dados, fórmulas, filtros, relacionamentos, documentos rastreáveis e intercâmbio com formatos comuns. Excel é formato de entrada/saída, não dependência operacional. Não há promessa de compatibilidade integral com todos os recursos do Excel.

## Implementado na branch main

### Espaço de dados genérico
- Projetos independentes com descrição e metadados.
- Várias tabelas por projeto.
- Colunas dinâmicas com tipos texto, inteiro, decimal, booleano, data, data/hora e JSON.
- CRUD de registros e tabelas, validação de tipos, campos obrigatórios e valores padrão.
- Filtros por igualdade, diferença, contém, comparações e lista; ordenação e paginação.
- Relacionamentos entre colunas de tabelas do mesmo projeto, com validação de tipos.
- Colunas calculadas com fórmulas seguras, sem executar Python: operações aritméticas, comparações e funções SUM, AVERAGE, MIN, MAX, COUNT, IF, ABS, ROUND, AND, OR e NOT.
- Referências de fórmulas com nomes compostos entre colchetes, por exemplo `=[Quantidade] * [Preço unitário]`.
- Interface desktop para criar projetos/tabelas/colunas/registros, editar células e importar/exportar CSV e Excel.
- Persistência SQLite com migração aditiva versionada, sem reescrever a tabela legada de pontes.

### Backup e recuperação\n- Backup SQLite consistente por API nativa, manifesto JSON com SHA-256 e verificação de integridade.\n- Restauração validada com criação automática de backup de segurança antes de substituir o banco ativo.\n- Ações de backup, verificação e restauração disponíveis no menu principal.\n\n### Scanner e biblioteca documental
- SHA-256, tamanho, MIME, metadados, seções extraídas, avisos e erros por arquivo.
- Seleção de vários arquivos ou varredura recursiva de pasta.
- Processamento em thread separada e visualização dos resultados.
- Catálogo SQLite persistente e biblioteca para consultar análises anteriores.
- PDF: texto por página, campos de formulário, nomes de anexos e extração inicial de tabelas; OCR de páginas digitalizadas quando Tesseract está disponível.
- DOCX: parágrafos, tabelas, cabeçalhos e rodapés.
- DOC, PPT, RTF, ODT e ODP: conversão local para texto quando LibreOffice está instalado.
- XLSX/XLSM: abas, células e expressões de fórmulas; XLS: abas e valores; XLSB: abas e valores.
- PPTX: texto e tabelas por slide.
- CSV, TXT, Markdown, JSON e XML.
- PNG, JPEG, TIFF, BMP, WEBP e GIF: metadados de imagem e OCR opcional.
- DXF: entidades, camadas, vértices de polilinhas e dados básicos de blocos.
- DWG: conversão opcional para DXF por ODA File Converter instalado.
- IFC: produtos e conjuntos de propriedades quando IfcOpenShell está instalado.
- RVT/RFA: reconhecidos com orientação para exportar pelo Revit para IFC/PDF; sem leitor direto integrado.
- Limite de 512 MiB por arquivo e proteções iniciais contra arquivos Office compactados suspeitos.

## Limitações que precisam ficar claras

- O scanner não interpreta semanticamente qualquer arquivo nem certifica documentos.
- OCR requer Tesseract; o pipeline Windows tenta incluir o mecanismo e o idioma português no pacote. Builds locais podem usar Tesseract instalado no computador. O código tenta português+inglês e recua para inglês.
- DOC/PPT/RTF/ODT/ODP dependem de LibreOffice instalado.
- DWG depende do ODA File Converter instalado; a fidelidade de conversão deve ser conferida.
- IFC depende de IfcOpenShell compatível com a versão de Python.
- RVT/RFA não são lidos diretamente. Exportar pelo Revit para IFC é o fluxo recomendado.
- Recursos avançados de Office (macros, gráficos, comentários, revisões, conexões, objetos incorporados) não são executados e nem todos são extraídos.
- PDF vetorial, cotas CAD, geometria BIM e imagens incorporadas ainda exigem leitores e testes específicos.
- Fórmulas cobrem um subconjunto inicial; não há compatibilidade integral com Excel, referências A1, macros, tabelas dinâmicas ou VBA.
- A interface genérica é uma primeira versão funcional; ainda faltam recursos de produtividade e revisão visual antes de substituir planilhas complexas.

## Arquitetura

Consulte [docs/ARQUITETURA_GERENCIADOR_UNIVERSAL.md](docs/ARQUITETURA_GERENCIADOR_UNIVERSAL.md), [docs/STATUS_PROJETO.md](docs/STATUS_PROJETO.md) e o [plano de testes de usuário](docs/PLANO_TESTES_USUARIO.md).

## Instalação e execução

Requisitos: Python 3.11 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m compileall -q app tests main.py
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe main.py
```

Para gerar o executável no Windows, execute `build/build_windows.bat`. O GitHub Actions também possui pipeline para testar e gerar um artefato Windows. O pacote ainda precisa ser executado em uma máquina Windows real antes da atualização do PC e dos testes de usuário.

## Dados privados e preservação

- Não publicar SQL real, bancos SQLite, planilhas internas, documentos corporativos ou credenciais.
- A base legada de pontes deve permanecer intacta durante a evolução.
- Os documentos originais não são modificados pelo scanner.
- Macros e conteúdo ativo não são executados.
- Faça backup de `data/registros.sqlite3` antes de qualquer atualização local.

## Repositório

[Código-fonte](https://github.com/Lvc4br/ponte) · [Releases](https://github.com/Lvc4br/ponte/releases) · [Testes automatizados](https://github.com/Lvc4br/ponte/actions/workflows/tests.yml) · [Pacote Windows](https://github.com/Lvc4br/ponte/actions/workflows/build-windows.yml)
