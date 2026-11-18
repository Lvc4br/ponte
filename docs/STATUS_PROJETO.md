# Situação do projeto

**Produto:** PONTE — Gerenciador Universal de Dados e Documentos  
**Objetivo:** gerenciar dados e documentos de projetos de diferentes áreas, localmente e sem dependência operacional do Excel.  
**Branch:** main

## Implementado nesta etapa na branch main

- [x] Pacote inicial de scanner documental em `app/documents`.
- [x] SHA-256 calculado em fluxo, metadados básicos, tamanho e tipo MIME.
- [x] Resultado padronizado com seções, avisos, erros e estado por arquivo.
- [x] Leitura inicial de PDF textual, DOCX, XLSX/XLSM, XLS, PPTX, CSV, TXT, MD, JSON e XML.
- [x] Adaptadores opcionais para imagens/OCR, DXF e IFC.
- [x] Limite inicial de 512 MiB por arquivo.
- [x] Testes iniciais para TXT, CSV, JSON, extensão não suportada e arquivo inexistente.
- [x] Documentação de arquitetura e limitações.
- [x] Preservação do conjunto de dados de pontes existente; nenhuma migração destrutiva foi feita nesta etapa.

## Ainda não implementado

- [ ] Executar CI atualizado e corrigir falhas encontradas.
- [ ] Scanner integrado à interface gráfica.
- [ ] Processamento de pastas e lotes com progresso/cancelamento.
- [ ] OCR de PDF digitalizado com posição e confiança por trecho.
- [ ] Extração aprofundada de gráficos, imagens, cotas, blocos CAD e geometria BIM.
- [ ] Leitura direta de DWG e RVT ou conversão confiável desses formatos.
- [ ] Inventário documental persistente no SQLite, com histórico e deduplicação.
- [ ] Modelo universal de projetos, tabelas, colunas e registros.
- [ ] Motor tabular genérico e interface desvinculada do domínio de obras.
- [ ] Revisão humana das extrações e conversão para registros.
- [ ] Backup/restauração e build Windows validados com os novos componentes.

## Limitações conhecidas

A extração atual não equivale a leitura semântica completa de qualquer documento. PDFs digitalizados precisam de OCR; recursos avançados de Office podem exigir adaptadores específicos; OCR depende do Tesseract instalado; IFC depende de IfcOpenShell; DWG/RVT não estão diretamente suportados nesta etapa. Nenhuma saída deve ser considerada validação técnica automática.

## Preservação e segurança

- Não publicar SQL real, bancos locais, planilhas internas, documentos corporativos ou credenciais.
- Preservar a base de pontes durante a migração.
- Manter os arquivos originais sem alteração.
- Não executar macros ou conteúdo ativo de documentos.
- Validar compatibilidade e empacotamento antes de distribuir novo executável.
