# Auditoria do pacote recebido — 2026-11-23

## Integridade e composição
- Arquivo recebido: `gerenciamento de dados(1).zip`.
- Tamanho comprimido: 129.682.407 bytes (123,67 MiB).
- Entradas: 2.710.
- Conteúdo descompactado: aproximadamente 241,0 MiB.
- Teste de integridade ZIP: aprovado (nenhum membro corrompido).
- SHA-256 do ZIP original: `e6ad4b96364bd2aa60c6f2fd0f67977cb3ee4eb86226db9d7e3ababb2805905f`.

## Conteúdo identificado
1. **Versão C independente (raiz do pacote):** aplicação Tkinter, `app.py` e `ponte_core.py`; branch local `feature/ponte-plataforma-engenharia`, HEAD `4a5457e`; branch histórica `desenvolvimento/ponte-v1` em `2b0e1e2`. A cópia da raiz contém alterações locais em `Ponte.spec` e diretórios não rastreados `Ponte-final/` e `ponte-repo/`.
2. **Versão B (subpasta `ponte-repo/`):** aplicação modular PySide6; branch `fix/estimativa-taxas-engenharia`, HEAD `396f7d1`; histórico inclui `4f1c41d`, `64674b2`, `c758f04` e a base `287bf7b`. O working tree contém 61 arquivos modificados/não rastreados. Essas mudanças locais são importantes e não devem ser descartadas nem substituídas por um merge cego.
3. O pacote também contém builds e executáveis redundantes, além de artefatos de runtime.

## Testes executados nesta auditoria
- Versão B isolada (`ponte-repo/`): **97 testes passaram**.
- Testes específicos da versão C (`test_app.py`): **9 testes passaram**.
- Execução conjunta a partir da raiz: **106 testes passaram**.
- O processo Python também emitiu um aviso de warmup do ambiente de planilhas (`Element ordering requires an owning element collection`); esse aviso não alterou o resultado do pytest. A execução não substitui CI Windows nem teste manual do executável.

## Preservação
- Foi criado um snapshot de código-fonte com 188 arquivos, aproximadamente 0,65 MiB, preservando documentação, testes e metadados Git das duas implementações.
- Foram excluídos do snapshot: builds, executáveis, DLLs, extensões binárias, caches, bancos locais, logs, exports e pastas de documentos/dados de runtime.
- Snapshot: `/PONTE/Recebidos/ponte-source-snapshot-2026-11-23.zip` na Library do ChatGPT.
- O upload do ZIP original para a Library falhou por limite de armazenamento. O original permanece disponível como anexo desta conversa.
- O ZIP original tem 123,67 MiB; não é adequado como arquivo único no GitHub (limite normal de 100 MB por arquivo). Este repositório registra a auditoria e o hash, mas não recebe o pacote binário integral.

## Decisão técnica para PONTE v2
- **Base principal recomendada: versão B**, por sua arquitetura modular, workspace genérico, persistência SQLite, importação, scanner documental e cobertura de testes.
- **Versão C:** manter como referência histórica independente; aproveitar ideias ou funcionalidades apenas após comparação e testes.
- **Versão A/main:** manter como baseline estável; não substituir nem reescrever `main` nesta etapa.
- O snapshot preserva as alterações locais da versão B para inspeção. Antes de integrá-las ao branch `rebuild/ponte-v2`, comparar os 61 arquivos modificados com o código já presente no GitHub e executar testes de regressão.
- Os 97 testes aprovados não eliminam os defeitos P0/P1 registrados na Issue #8. Integridade de exclusão, atomicidade, restauração de backup e comparabilidade de engenharia continuam como bloqueios a validar/corrigir.
- Indicadores Paf, Pap, Ecm e Af não devem ser tratados como aprovados sem definição formal de fórmula, unidade, escopo e validação técnica pela EGT.

## Próxima sequência
1. Comparar a versão B local do snapshot com as branches e PRs existentes.
2. Produzir inventário de diferenças por arquivo e separar mudanças úteis, duplicadas e perigosas.
3. Integrar em `rebuild/ponte-v2` em etapas pequenas, preservando `main`.
4. Corrigir e testar os bloqueios de integridade antes de ampliar funcionalidades.
5. Atualizar scorecard somente com evidências reproduzíveis.
