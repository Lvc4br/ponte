# Situação do projeto

**Produto:** PONTE — Gerenciador Universal de Dados e Documentos  
**Branch:** main  
**Escopo:** gerenciador local-first para projetos de qualquer área; pontes/obras são um conjunto legado.

## Implementado no código

- [x] Workspace genérico com projetos, tabelas, colunas e registros.
- [x] Tipos texto, inteiro, decimal, booleano, data, data/hora e JSON.
- [x] CRUD de projetos, tabelas, colunas e registros no backend.
- [x] Validação de tipos, campos obrigatórios, padrões e nomes únicos.
- [x] Filtros, ordenação e paginação no backend.
- [x] Relacionamentos entre colunas de tabelas do mesmo projeto.
- [x] Fórmulas seguras por AST, com colunas calculadas e referências entre colunas.
- [x] Interface inicial para projetos, tabelas, edição de células e colunas calculadas.
- [x] Importação/exportação inicial de CSV e XLSX/XLSM.
- [x] Migração aditiva do workspace SQLite v1 para v2.
- [x] Associação de documentos do catálogo a projetos no backend.
- [x] Scanner recursivo, catálogo documental e biblioteca integrada à interface.
- [x] Leitores iniciais de PDF, DOC/DOCX, PPT/PPTX, RTF, ODT/ODP, XLS/XLSX/XLSM/XLSB, CSV/TXT/MD/JSON/XML, imagens, DXF, DWG opcional, IFC opcional e reconhecimento RVT/RFA.
- [x] Proteção inicial contra arquivos Office compactados suspeitos.
- [x] Testes automatizados adicionados para workspace, fórmulas, importação/exportação, scanner e catálogo.

## Ainda precisa ser verificado

- [ ] Resultado real do GitHub Actions após os últimos commits.
- [ ] Build Windows e smoke test do executável.
- [ ] Compatibilidade do PyInstaller com todos os leitores e plugins Qt.
- [ ] Execução em Windows limpo sem Python instalado.
- [ ] Backup/restauração do banco completo e validação de integridade.
- [ ] Testes com arquivos reais de DOC/DOCX/PDF/XLS/XLSX/PPT/PPTX/DWG/IFC/RVT autorizados.
- [ ] OCR com Tesseract e idiomas português/inglês.
- [ ] Conversão DOC/PPT/RTF/ODT/ODP com LibreOffice.
- [ ] Conversão DWG com ODA File Converter.
- [ ] Leitura IFC com IfcOpenShell.
- [ ] Progresso por arquivo, cancelamento seguro e relatório exportável.
- [ ] UX de edição em lote, copiar/colar, desfazer/refazer e filtros visuais.
- [ ] Revisão de segurança, desempenho, acessibilidade e usabilidade.
- [ ] Testes de usuário antes de considerar substituição de planilhas complexas.

## Limitações conhecidas

Não existe leitura integral de qualquer formato. RVT/RFA não têm leitor direto. DWG depende de conversor externo. OCR, LibreOffice e IfcOpenShell dependem de instalações adicionais. Office avançado, geometria CAD/BIM, macros, objetos incorporados e funções avançadas do Excel não são integralmente suportados.

## Preservação

- Não publicar SQL real, bancos locais, planilhas internas, documentos corporativos ou credenciais.
- A migração genérica usa tabelas novas e não deve apagar registros legados.
- Fazer backup de `data/registros.sqlite3` antes da atualização do PC.
- Não atualizar o PC até o CI e o pacote Windows serem verificados.
