# Changelog

## Em desenvolvimento — PONTE Gerenciador Universal

- Consolidado o objetivo de gerenciador universal de dados e documentos para projetos de qualquer setor.
- Criado workspace SQLite com projetos, tabelas, colunas tipadas, registros e relacionamentos.
- Criadas operações CRUD, validação, filtros, ordenação e paginação para tabelas genéricas.
- Adicionado motor de fórmulas seguro baseado em AST, com colunas calculadas e referências a nomes de colunas entre colchetes.
- Criada interface inicial para projetos e tabelas, com edição de células e colunas calculadas.
- Criados adaptadores de importação/exportação CSV e XLSX/XLSM.
- Adicionada migração aditiva versionada do esquema do workspace.
- Ampliado scanner para DOC/PPT/RTF/ODT/ODP via LibreOffice, XLSB, PDF com tabelas, DWG via ODA opcional, IFC com propriedades e reconhecimento de RVT/RFA.
- Adicionadas verificações de segurança para containers Office/OpenDocument.
- Atualizados testes automatizados, dependências e workflows de CI e pacote Windows.

As alterações ainda precisam passar pelo GitHub Actions, build Windows e smoke test do executável antes de qualquer atualização do PC.
