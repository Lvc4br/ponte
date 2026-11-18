# PONTE — Gerenciador Universal de Dados e Documentos

Aplicativo desktop Windows, local-first, para organizar dados e documentos de projetos de diferentes áreas. O produto não é limitado a pontes ou engenharia: a base atual de pontes é um conjunto de dados legado que deve continuar acessível dentro do gerenciador universal.

O objetivo de longo prazo é oferecer uma alternativa independente para parte relevante dos fluxos de planilhas, com tabelas configuráveis, documentos rastreáveis, pesquisa, análise, importação e exportação. Excel será um formato de intercâmbio, não uma dependência obrigatória.

## Estado real da implementação

### Já existente na branch main

- Aplicativo desktop Python/PySide6.
- Persistência local SQLite e manutenção da base existente de obras/pontes.
- Importação atual de planilhas .xlsx com seleção de aba, prévia e proteção contra reimportação.
- Navegação entre base principal e planilhas importadas na interface antiga de Gestão de Obras.
- Filtros e indicadores específicos do conjunto de dados legado.
- Scanner documental em `app/documents/scanner.py`, com resultado padronizado, SHA-256, metadados, seções, avisos, erros e varredura recursiva em lote.
- Ação **Analisar documentos** integrada à interface, com execução em thread separada e visualização do conteúdo extraído.
- Leitura inicial de PDF, DOCX, XLSX/XLSM, XLS, PPTX, CSV, TXT, Markdown, JSON, XML, imagens com OCR opcional, DXF e IFC opcional.
- Testes unitários iniciais do scanner para texto, CSV, JSON, formatos ainda não suportados e arquivo inexistente.

### Limitações importantes do scanner

- PDF digitalizado pode precisar de OCR; a leitura atual de PDF extrai texto acessível, não interpreta integralmente desenhos ou anexos.
- OCR de imagens e páginas PDF digitalizadas exige Pillow, pytesseract, pypdfium2 e o executável Tesseract instalado e configurado.
- DXF e IFC dependem de leitores específicos; IFC requer IfcOpenShell compatível com a versão de Python.
- DWG e RVT ainda não têm leitor integrado. Conversão e integração devem ser avaliadas separadamente.
- A leitura inicial de DOCX/PPTX/XLSX não extrai todos os objetos incorporados, gráficos, caixas de texto, comentários, macros ou conexões externas.
- O scanner extrai conteúdo; não certifica documentos, não valida cálculos nem substitui análise profissional de engenharia.
- A interface ainda não oferece uma biblioteca documental integrada nem processamento em lote. A implementação do scanner é uma fundação de backend.

## Arquitetura e escopo

Consulte [docs/ARQUITETURA_GERENCIADOR_UNIVERSAL.md](docs/ARQUITETURA_GERENCIADOR_UNIVERSAL.md) para princípios, matriz de formatos, limites e etapas técnicas.

O desenvolvimento seguirá estas frentes:

1. Scanner e adaptadores documentais testáveis.
2. Inventário documental local, hash, histórico e rastreabilidade da origem.
3. Processamento de arquivos e pastas em lote, relatório e revisão.
4. OCR e extração avançada de conteúdo visual.
5. Modelo genérico de projetos, tabelas, colunas e registros.
6. Motor tabular, filtros, fórmulas, relações e visualizações.
7. Importação/exportação, backup, restauração e distribuição Windows.

## Dados privados e preservação

- Não publicar SQL real, bancos SQLite, planilhas internas, documentos corporativos ou credenciais.
- A base de pontes existente deve ser preservada durante a migração para o modelo genérico.
- Os arquivos originais importados não devem ser alterados pelo scanner.
- Releases públicos devem conter somente dados de exemplo autorizados.

## Instalação e execução

Requisitos: Python 3.11 ou superior.

```powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install --upgrade pip
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe -m pytest -v
.\\.venv\\Scripts\\python.exe main.py
```

Para gerar o executável Windows, execute `build/build_windows.bat`. O empacotamento dos novos leitores e eventuais dependências externas (como Tesseract e IfcOpenShell) ainda precisa ser validado.

## Segurança e limites

- O scanner não executa macros de Office.
- Arquivos acima de 512 MiB são recusados pelo limite inicial do scanner.
- Um erro de leitura é registrado no resultado daquele arquivo, sem interromper o chamador.
- Resultados devem ser revisados antes de serem convertidos em dados oficiais.
- Extração automática não equivale a validação técnica, estrutural, jurídica ou contábil.

## Repositório

[Código-fonte](https://github.com/Lvc4br/ponte) · [Releases](https://github.com/Lvc4br/ponte/releases) · [Testes automatizados](https://github.com/Lvc4br/ponte/actions/workflows/tests.yml)
