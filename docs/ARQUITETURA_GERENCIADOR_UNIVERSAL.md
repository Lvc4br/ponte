# PONTE — Arquitetura do Gerenciador Universal de Dados e Documentos

## Objetivo

Aplicativo desktop local-first para organizar dados e documentos de projetos de diferentes áreas. Pontes/obras são apenas um domínio legado. Excel é um formato de intercâmbio, não uma dependência.

## Princípios

- Projetos independentes do setor.
- Tabelas e colunas configuráveis e tipadas.
- Arquivos originais preservados; extrações com rastreabilidade.
- Processamento local por padrão.
- Falhas isoladas por arquivo.
- Macros e conteúdo ativo nunca são executados.
- Extração não equivale a validação técnica ou certificação.
- Alterações de banco devem ser aditivas, versionadas e testadas.

## Camadas atuais

1. **Interface PySide6:** janela legada de obras, biblioteca documental e diálogo de espaço de dados genérico.
2. **Domínio:** projetos, tabelas, colunas, registros, relacionamentos e fórmulas.
3. **Persistência:** SQLite compartilhado com o legado, usando tabelas novas com prefixo `workspace_` e migração de esquema versionada.
4. **Scanner:** adaptadores por extensão, hash SHA-256, limites de tamanho, validação de containers e resultados por arquivo.
5. **Catálogo documental:** documentos e seções extraídas persistidos em SQLite.
6. **Intercâmbio:** adaptadores CSV e Excel para tabelas genéricas.
7. **Motor de fórmulas:** AST com lista explícita de operações/funções permitidas; não usa `eval` nem executa código arbitrário.

## Modelo de dados

- `workspace_projects`: projetos.
- `workspace_tables`: tabelas pertencentes a projetos.
- `workspace_columns`: colunas tipadas, posição, padrão, obrigatoriedade e fórmula opcional.
- `workspace_records`: registros em JSON validado segundo o esquema de colunas.
- `workspace_relations`: relacionamentos entre colunas de tabelas do mesmo projeto.
- `workspace_document_links`: associação entre projeto e documentos do catálogo.
- `documents` e `document_sections`: catálogo documental preexistente.

A versão de esquema do workspace é controlada por `ponte_schema_version`. A migração da versão 1 para 2 adiciona a coluna de fórmula sem apagar dados existentes.

## Fórmulas

O motor inicial aceita aritmética, comparações, operadores booleanos, condicionais e funções SUM, AVERAGE, MIN, MAX, COUNT, IF, ABS, ROUND, AND, OR e NOT. Referências a colunas com espaço ou acento usam colchetes, por exemplo `[Preço unitário] * [Quantidade]`. Colunas calculadas são somente leitura e são calculadas ao consultar os registros. Ciclos e referências inexistentes devem ser rejeitados.

Não há equivalência total com Excel: sem VBA, macros, funções financeiras/estatísticas extensas, referências A1, matrizes dinâmicas, tabelas dinâmicas ou conexões externas.

## Formatos documentais

| Formato | Leitura inicial | Dependência/limite |
|---|---|---|
| PDF | Texto por página, metadados, campos, anexos listados e tabelas | OCR opcional via Tesseract; extração de tabelas via pdfplumber |
| DOCX | Parágrafos, tabelas, cabeçalhos e rodapés | Comentários, revisões e objetos incorporados não são completos |
| DOC/PPT/RTF/ODT/ODP | Conversão para texto | LibreOffice instalado; layout pode ser perdido |
| XLSX/XLSM | Abas, células e fórmulas como expressões | Macros não executadas; objetos avançados não extraídos |
| XLS | Abas e valores | Recursos legados/fórmulas com fidelidade limitada |
| XLSB | Abas e valores | pyxlsb; não executa macros |
| PPTX | Texto e tabelas por slide | Gráficos e objetos incorporados limitados |
| CSV/TXT/MD/JSON/XML | Conteúdo textual/estruturado | Codificação e esquema variam |
| PNG/JPEG/TIFF/BMP/WEBP/GIF | Metadados e OCR opcional | Pillow, pytesseract e Tesseract |
| DXF | Entidades, camadas, polilinhas e blocos básicos | ezdxf; geometria/cotas avançadas pendentes |
| DWG | Conversão para DXF | ODA File Converter externo e verificação de fidelidade |
| IFC | Produtos e conjuntos de propriedades | IfcOpenShell opcional; geometria detalhada pendente |
| RVT/RFA | Reconhecimento e orientação de exportação | Sem leitor direto; exportar IFC/PDF pelo Revit |

## Segurança e limites

- Arquivos maiores que 512 MiB são recusados.
- Containers Office/OpenDocument têm limites de quantidade de entradas, tamanho expandido e taxa de compressão.
- Não executar macros, scripts ou conteúdo ativo.
- OCR e conversores externos são chamados localmente, com timeout.
- Arquivos originais não são regravados.
- Resultados precisam de revisão humana antes de se tornarem dados oficiais.

## Próximas etapas

1. CI verde em Windows e Linux para Python 3.11, 3.12 e 3.13.
2. Build Windows e execução de smoke test do executável empacotado.
3. Backup/restauração do SQLite, incluindo testes de integridade e preservação do legado.
4. Melhorar a interface tabular: edição em lote, copiar/colar, desfazer/refazer, filtros visuais, ordenação e atalhos.
5. Importação mais robusta, prévia, mapeamento de colunas e relatório de erros.
6. Revisão humana das extrações e vinculação de trechos documentais aos registros.
7. Melhorar OCR, extração CAD/BIM e suporte a arquivos reais de referência.
8. Testes de usuário, desempenho, acessibilidade e distribuição.

## Critério de conclusão

Um formato só será considerado estável quando houver arquivos de referência autorizados, testes automatizados, tratamento de arquivos inválidos, documentação das limitações e validação no executável Windows.
