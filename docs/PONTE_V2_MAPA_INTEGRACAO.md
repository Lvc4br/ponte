# PONTE v2 — mapa de integração e consolidação

**Branch:** `rebuild/ponte-v2`  
**Estado:** plano técnico executável; não equivale a integração de código concluída.

## 1. Base confirmada no GitHub

- `rebuild/ponte-v2` deriva de `rebuild/egt-foundation`.
- Comparação consultada: `rebuild/ponte-v2` está 6 commits à frente e 0 atrás de `rebuild/egt-foundation`.
- A branch contém os documentos de auditoria, roadmap, design, preservação e base oficial.
- `main` permanece fora desta linha de trabalho.

## 2. Decisão de arquitetura

A aplicação principal será desktop PySide6. Não criar uma segunda aplicação para o domínio EGT nem migrar o produto para Tkinter.

Fluxo obrigatório:

`UI PySide6 → serviços de aplicação → domínio → repositórios → SQLite (primeira entrega local)`

O domínio não deve importar widgets Qt. A UI não deve conter fórmulas de engenharia nem SQL de negócio. Os serviços coordenam transações e casos de uso.

## 3. Matriz de reaproveitamento das contribuições existentes

| Fonte | Reaproveitar | Integração pretendida | Condição |
|---|---|---|---|
| Versão B (PySide6, commit local 396f7d1 + alterações locais) | Workspace, planilha, documentos, persistência, importação/exportação, fórmulas, filtros e undo/redo | Base funcional principal | Recuperar integralmente alterações locais; comparar arquivo a arquivo; preservar cópia original |
| PR #7 / PR #10 | Entidades de projeto, ponte/OAE, vãos, quantitativos e catálogo de indicadores | Camada de domínio independente da UI | Revisar invariantes, unidades, migrações e testes; manter indicadores não confirmados como draft |
| PR #4 | Auditoria, revisão documental, edição em lote transacional e colagem TSV | Serviços transversais de governança | Não tratar perfis locais sem autenticação como segurança multiusuário |
| PR #5 | Workspace visual de três colunas e resumo analítico | Referência de UX para a área de trabalho | Confirmar dependência da PR #4 e executar testes integrados |
| PR #3 | Fluxo unificado de planilha, pesquisa, filtros, importação/exportação e prévia documental | Referência funcional complementar à versão B | Evitar duplicar recursos já existentes na versão B |
| PR #6 | Reorganização da navegação e separação da área documental | Ajuste de UX | Validar compatibilidade com o Design System |
| PRs #1 e #2 | Ideias visuais | Apenas referência visual | Não mesclar redesigns concorrentes diretamente |
| Versão C (Tkinter) | Ideias de cadastro e empacotamento | Referência histórica | Não incorporar sua camada de persistência nem trocar PySide6 por Tkinter |

## 4. Ordem de integração

### Lote 0 — congelamento
- [ ] Preservar ZIP original e hash.
- [ ] Manter uma cópia imutável da pasta B.
- [ ] Separar arquivos versionados, modificados, não rastreados e artefatos locais.
- [ ] Não versionar banco de dados real, documentos privados, EXE, DLL, .venv, dist ou build.

### Lote 1 — domínio
- [ ] Revisar PR #10 e PR #7.
- [ ] Conferir modelos de Projeto, OAE, vão e quantitativo.
- [ ] Definir identificadores, invariantes e unidades.
- [ ] Criar adaptadores/serviços para conectar domínio ao WorkspaceStore da versão B.
- [ ] Rodar testes de domínio e da aplicação.

### Lote 2 — persistência e integridade (P0)
- [ ] Corrigir exclusão de registros e garantir integridade referencial.
- [ ] Gravar registro, projeção técnica e fingerprint em uma transação única.
- [ ] Validar schema completo antes de restaurar backup.
- [ ] Restaurar para arquivo temporário, validar integridade e só então substituir banco ativo.
- [ ] Adicionar testes que reproduzam cada falha conhecida.

### Lote 3 — importação
- [ ] Importação em staging com prévia e mapeamento explícito.
- [ ] CSV com detecção/seleção de delimitador e parsing explícito de decimal pt-BR.
- [ ] Preservar valor original, unidade e localização no arquivo de origem.
- [ ] Confirmação transacional; relatório de rejeições e duplicidades.

### Lote 4 — produto integrado
- [ ] Cadastro OAE ligado ao projeto e ao workspace.
- [ ] Indicadores ligados a dados rastreáveis e a uma versão de metodologia.
- [ ] Análise comparativa com critérios, amostra, exclusões e dados ausentes.
- [ ] Documentos vinculados à OAE e ao projeto, com hash e versionamento.
- [ ] Relatórios com filtros, fontes, fórmulas e metodologia.

### Lote 5 — interface e release
- [ ] Implementar navegação do Design System sem duplicar janelas e serviços.
- [ ] Estados vazio, carregando, erro, incompleto e sem permissão.
- [ ] Testes Windows e build reproduzível.
- [ ] Só então avaliar executável one-file.

## 5. Contratos mínimos de dados

Toda grandeza física deve guardar valor, unidade e origem. Dados importados devem preservar arquivo, aba, linha/célula, valor original, autor, instante e regra de conversão. Valores derivados devem guardar fórmula e versão da metodologia. Dados fictícios de demonstração devem ser identificados como fictícios.

## 6. Indicadores — pendências explícitas

Catálogo solicitado:
- Paf (kg/m²)
- Pap (kg/m²)
- Ecm (definição e unidade a confirmar)
- Af (m²/m²)
- Aço total indicativo (kg/m² e kg/m³)

Não inventar fórmula, significado ou unidade. Não exibir como validado nem usar para decisão até aprovação formal da EGT.

## 7. Critérios de conclusão de cada lote

Um lote só é concluído quando:
1. O código está na branch `rebuild/ponte-v2`.
2. Há testes de regressão correspondentes.
3. A suíte aplicável está verde no CI e, quando necessário, em Windows.
4. Não há perda de dados ou regressão funcional conhecida.
5. A documentação descreve o que foi realmente entregue e suas limitações.

## 8. Limites da primeira versão

A primeira entrega é desktop local/offline. Não anunciar sincronização, autenticação corporativa, concorrência de 30+ usuários ou suporte nativo completo a DWG/RVT/RFA sem implementação e validação específica.
