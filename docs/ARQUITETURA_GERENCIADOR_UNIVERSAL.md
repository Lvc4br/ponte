# PONTE — Arquitetura do Gerenciador Universal de Dados e Documentos

## Objetivo do produto

O PONTE é um aplicativo desktop local-first para organizar dados e documentos de projetos de diferentes setores. Obras e pontes são apenas um domínio de dados já existente, não uma limitação do produto. Excel deve ser tratado como formato de intercâmbio, não como dependência operacional.

## Princípios

- Projetos independentes do setor de atuação.
- Dados tabulares genéricos, com tabelas e colunas configuráveis.
- Documentos originais preservados e analisados sem alteração.
- Extrações rastreáveis até arquivo, página, aba, slide ou elemento de origem.
- Processamento local por padrão; serviços externos são opcionais e explícitos.
- Falhas por arquivo não interrompem o processamento em lote.
- Nenhuma extração deve ser apresentada como validação técnica ou certificação.

## Camadas planejadas

1. **Interface desktop:** projetos, tabelas, biblioteca documental, fila de análise e revisão de extrações.
2. **Domínio genérico:** projetos, fontes, documentos, tabelas, colunas, registros, relacionamentos e histórico.
3. **Persistência:** SQLite com migrações versionadas, índices e transações; arquivos originais em armazenamento local gerenciado.
4. **Ingestão documental:** registro de arquivos, hash, detecção de formato, validação e fila de processamento.
5. **Adaptadores:** leitores isolados por formato, com capacidades e limitações declaradas.
6. **Extração e indexação:** texto, tabelas, metadados, OCR e elementos técnicos; cada resultado mantém sua proveniência.
7. **Motor tabular:** CRUD, filtros, ordenação, fórmulas, relacionamentos e importação/exportação.
8. **Segurança e recuperação:** backup, restauração, integridade, proteção contra arquivos malformados e limites de recursos.

## Matriz inicial de formatos

| Formato | Leitura inicial | Limites conhecidos |
|---|---|---|
| PDF | Texto por página e metadados | PDF digitalizado usa OCR opcional (Tesseract); formulários, vetores e anexos exigem leitores adicionais |
| DOCX | Parágrafos, tabelas, cabeçalhos e rodapés | Caixas de texto, comentários, revisões e objetos incorporados podem exigir adaptadores extras |
| XLSX/XLSM | Abas, células e expressões de fórmulas | Macros não são executadas; gráficos, imagens, conexões e objetos precisam de extração específica |
| XLS | Abas e valores de células | Fórmulas e recursos legados têm fidelidade limitada |
| PPTX | Texto e tabelas por slide | Gráficos, imagens e objetos incorporados precisam de adaptadores extras |
| CSV/TXT/JSON/XML/MD | Conteúdo textual e estrutura básica | Codificações e esquemas podem variar |
| PNG/JPEG/TIFF/BMP | OCR opcional | Requer Pillow, pytesseract e o mecanismo Tesseract instalado |
| DXF | Entidades do modelspace e camadas | Requer ezdxf; blocos, cotas e geometrias complexas terão extração progressiva |
| IFC | Produtos e propriedades básicas | Requer IfcOpenShell compatível; geometria BIM detalhada é etapa posterior |
| DWG/RVT | Não suportado diretamente nesta etapa | Formatos proprietários; avaliar conversores oficiais/compatíveis e importação IFC/DXF |

## Scanner implementado nesta etapa

app/documents/scanner.py introduz um resultado padronizado por arquivo, SHA-256, metadados, seções extraídas, avisos, erros e estados success, partial, error e unsupported. Um erro em um arquivo é isolado no resultado daquele arquivo. Há limite inicial de 512 MiB por arquivo.

Os leitores são carregados sob demanda. DXF e IFC usam adaptadores opcionais; OCR depende de componentes externos. O scanner não executa macros, não altera arquivos originais e não valida engenharia.

## Próximas etapas técnicas

1. Testar o scanner em CI e ajustar compatibilidade dos leitores.
2. Criar inventário documental persistente no SQLite, com hash, caminho, tamanho, formato, status e data de análise.
3. Adicionar processamento de pastas em lote, cancelamento e relatório consolidado.
4. Implementar OCR de PDF digitalizado e imagens, com coordenadas e confiança.
5. Extrair conteúdo de gráficos, imagens, cotas, blocos e geometrias técnicas.
6. Implementar conversão/integração para DWG e RVT, sem alegar suporte nativo antes de testes reais.
7. Construir modelo genérico de projetos, tabelas e colunas, migrando a base atual sem perda.
8. Integrar revisão humana e conversão de extrações em registros tabulares.

## Critério de conclusão

Um formato só será considerado suportado quando houver leitor, testes com arquivos de referência, tratamento de arquivos inválidos, documentação das limitações e verificação do empacotamento no executável Windows.
