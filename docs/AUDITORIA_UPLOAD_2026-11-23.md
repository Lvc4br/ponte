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
2. **Versão B (subpasta `ponte-repo/`):** aplicação modular PySide6; branch `fix/estimativa-taxas-engenharia`, HEAD `396f7d1`; quatro commits próprios após a base `287bf7b`: `c758f04`, `64674b2`, `4f1c41d`, `396f7d1`.
3. O working tree da B reporta 61 arquivos modificados, mas a comparação `git diff --ignore-space-at-eol` ficou vazia: são alterações de fim de linha (CRLF/LF), não diferenças semânticas de conteúdo. Portanto, os 61 arquivos não devem ser interpretados como 61 funcionalidades pendentes.
4. Em relação ao branch de fundação EGT, os quatro commits da B acrescentam 15 arquivos com aproximadamente 446 inserções e 23 remoções. A integração exige combinar os dois conjuntos de commits, pois ambos partem da base `main`.
5. O pacote também contém builds e executáveis redundantes, além de artefatos de runtime.

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
- O ZIP original tem 123,67 MiB; excede o limite normal de 100 MB por arquivo no GitHub. Não há ferramenta de upload de release asset disponível nesta sessão. Este repositório registra a auditoria e o hash, mas não recebe o pacote binário integral.

## Decisão técnica para PONTE v2
- **Base principal recomendada: versão B**, por sua arquitetura modular, workspace genérico, persistência SQLite, importação, scanner documental e cobertura de testes.
- **Versão C:** manter como referência histórica independente; aproveitar ideias ou funcionalidades apenas após comparação e testes.
- **Versão A/main:** manter como baseline estável; não substituir nem reescrever `main` nesta etapa.
- Os quatro commits B contêm a evolução funcional a avaliar; as mudanças de fim de linha no working tree não precisam ser integradas.
- Os 97 testes aprovados não eliminam os defeitos P0/P1 registrados na Issue #8. A auditoria inicial confirma riscos no armazenamento: `delete()` remove linhas de `records`, mas não remove/arquiva os correspondentes em `obras`; `append_imported_file()` grava o fingerprint e registros em uma transação, mas grava os dados tipados em outra. Uma falha na segunda etapa pode deixar dados divergentes. Esses pontos precisam de testes de regressão e correção.
- A comparabilidade atual considera sobreposição de largura, comprimento, vão e seção opcional; ainda não aplica de forma completa tipologia, sistema estrutural, materiais e contexto. Isso é insuficiente para apresentar amostras como tecnicamente equivalentes.
- Indicadores Paf, Pap, Ecm e Af não devem ser tratados como aprovados sem definição formal de fórmula, unidade, escopo e validação técnica pela EGT. A implementação atual chama o campo de concreto `em_m3_m2`; não o renomear para Ecm sem decisão formal.

## Próxima sequência
1. Publicar o branch local `fix/estimativa-taxas-engenharia` no GitHub, sem incluir alterações de fim de linha do working tree.
2. Comparar os quatro commits B com a fundação EGT e preparar integração em `rebuild/ponte-v2`.
3. Corrigir atomicidade e consistência de exclusão com testes de regressão.
4. Evoluir critérios de comparabilidade com taxonomia técnica aprovada.
5. Atualizar scorecard somente com evidências reproduzíveis.
