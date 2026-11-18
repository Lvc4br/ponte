# Changelog

## Em desenvolvimento — PONTE Gerenciador Universal de Dados e Documentos

- Reposicionamento do produto: projetos de qualquer setor; pontes/obras passam a ser apenas um conjunto de dados existente.
- Criado pacote `app/documents` com scanner de arquivos, SHA-256, metadados, conteúdo extraído, avisos e erros.
- Integrada a análise assíncrona de múltiplos documentos à interface e criada visualização das extrações.
- Criado catálogo documental SQLite persistente, com deduplicação por SHA-256 e armazenamento das seções extraídas.
- Atualizado o build Windows para coletar dependências dos leitores documentais.
- Adicionados leitores iniciais para PDF, DOCX, XLSX/XLSM, XLS, PPTX, CSV, TXT, MD, JSON, XML, imagens com OCR opcional, DXF e IFC opcional.
- Adicionados testes iniciais do scanner e documentação da arquitetura universal.
- Incluídas dependências para PDF, Word, PowerPoint, XLS e DXF.
- DWG/RVT, OCR completo, processamento em lote, inventário documental persistente e integração com a interface continuam pendentes.

## Histórico anterior

As funcionalidades antigas de Gestão de Obras, importação Excel, navegação por planilhas, persistência SQLite e filtros dimensionais permanecem no código como legado funcional. A migração para o modelo genérico ainda não foi concluída.

