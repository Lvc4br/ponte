# PONTE v2 — Base oficial do produto e arquitetura inicial

**Status:** baseline de trabalho aprovada para desenvolvimento; não representa release validada.
**Branch de referência:** `rebuild/ponte-v2`
**Público-alvo:** EGT Engenharia
**Primeiro domínio:** pontes e Obras de Arte Especiais (OAEs)
**Plataforma inicial:** desktop Windows, operação local/offline.

## 1. Decisões de produto já definidas

| Tema | Decisão |
|---|---|
| Produto | PONTE — Engenharia • Inteligência |
| Objetivo central | Centralizar dados técnicos e apoiar gestão/análise de engenharia |
| Escopo inicial | Pontes e OAEs |
| Plataforma inicial | Aplicativo desktop |
| Estratégia | Reconstrução organizada, reaproveitando código existente |
| Interface | Design System PONTE enviado: navegação lateral, workspace claro, cards, tabelas, filtros e estados de validação |
| Dados | Banco local na primeira entrega; arquitetura central/multiusuário é etapa futura |
| Meta de qualidade | Alvo >=80/100 e maturidade intermediária em todas as áreas, sujeito a evidências de aceite |

## 2. Fontes de código e regra de reaproveitamento

- **A — `main` / baseline publicada:** referência estável e preservada; não desenvolver diretamente nela.
- **B — versão PySide6 / commit local `396f7d1`:** principal referência funcional. O pacote indica 61 arquivos com alterações locais não commitadas; essas alterações devem ser preservadas e comparadas antes de qualquer transplante. A execução registrada para esta versão foi de 97 testes aprovados.
- **Domínio EGT — PR #7:** código versionado de pontes, indicadores e testes. Está proposto para integração nesta branch pela PR #10.
- **C — implementação Tkinter independente:** referência histórica para ideias de cadastro/empacotamento. Não substituirá a arquitetura principal PySide6.
- **Design System PDF:** fonte da organização visual e dos sete módulos descritos em `PONTE_V2_DESIGN_SPEC.md`.

Não copiar pastas inteiras de uma versão sobre outra. Reutilizar por módulos, com testes e revisão de dependências.

## 3. Módulos que compõem o produto

1. **Visão geral:** KPIs calculados do banco, atividade e pendências de validação.
2. **Projetos e obras:** contratos, responsáveis, localização, fases e vínculos com OAEs.
3. **Pontes e OAEs:** cadastro técnico, geometria, materiais/quantitativos, inspeções, documentos e histórico.
4. **Importação de dados:** XLSX, XLS e CSV; prévia, mapeamento, validação e confirmação transacional.
5. **Análise de engenharia:** filtros e comparação técnica, amostra, exclusões, ausências, outliers e procedência.
6. **Documentos:** originais preservados, hash, metadados, vínculo, versões e revisão.
7. **Relatórios:** resumo executivo, comparativo OAE, relatório de importação e mapa de quantitativos.

## 4. Arquitetura de referência

A interface não deve conter regras de negócio. Fluxo esperado:

`UI (PySide6) → Serviços de aplicação → Domínio → Repositórios → Persistência`

- **UI:** janelas, navegação, formulários, tabelas e feedback.
- **Aplicação/serviços:** casos de uso, coordenação de importação, análise, documentos e relatórios.
- **Domínio:** entidades e regras de pontes/OAEs, unidades, validação e indicadores.
- **Dados:** repositórios, migrações, transações e consultas.
- **Documentos:** armazenamento, hash, metadados, versões e extração.
- **Infraestrutura:** logging, configuração, backup, empacotamento e integrações.

A estrutura final de diretórios será adaptada ao que já existe na versão B após recuperar e inspecionar suas alterações locais; não criar uma segunda arquitetura paralela sem necessidade.

## 5. Entidades mínimas do domínio

- Projeto/Contrato
- OAE
- Geometria da OAE
- Vão (coleção de vãos individuais)
- Material
- Quantitativo (valor, unidade, método, origem e validação)
- Inspeção
- Documento e versão documental
- Conjunto importado / lote de importação
- Evento de auditoria

Cada dado técnico deve manter unidade, origem e estado de validação. Quando aplicável, registrar arquivo, aba, linha/célula, autor, data, valor original e histórico de alterações.

## 6. Indicadores

O catálogo deve prever os indicadores solicitados:
- Paf (kg/m²)
- Pap (kg/m²)
- Ecm (definição e unidade ainda pendentes de confirmação)
- Af (m²/m²)
- Aço total indicativo (kg/m² e kg/m³)

**Regra:** nenhuma fórmula, significado ou unidade pendente pode ser apresentada como aprovada ou usada para conclusão decisória até validação técnica da EGT. O código do catálogo é um ponto de partida, não validação de engenharia.

## 7. Requisitos não funcionais e integridade

- Transações atômicas para gravações relacionadas.
- Integridade referencial; exclusões não podem deixar registros órfãos.
- Backup e restauração com validação integral do schema e teste real de restauração.
- Importação sem correções silenciosas; preservar original e hash.
- CSV deve tratar delimitadores e decimais brasileiros de forma explícita.
- Exportações protegidas contra formula injection.
- Logs e trilha de auditoria para ações críticas.
- Estados de carregamento, vazio, erro, permissão negada e dados incompletos.
- Teclado, foco visível e contraste adequado.
- Sem credenciais padrão inseguras, segredos ou dados reais versionados.

## 8. Limites da primeira entrega

A primeira versão é local/offline. Não declarar sincronização, autenticação corporativa, autorização multiusuário, concorrência de 30+ usuários, leitura nativa de RVT/RFA ou suporte completo a DWG sem implementação e testes específicos.

## 9. Gates de desenvolvimento

1. **Base congelada:** inventário e preservação de A/B/C e alterações locais.
2. **Domínio:** modelo de projeto/OAE e catálogo de unidades/regras.
3. **Integridade:** exclusão, transações, backup/restauração e testes P0.
4. **Dados:** importação/exportação e CSV pt-BR ponta a ponta.
5. **Operação:** UI desktop integrada aos serviços de domínio.
6. **Engenharia:** análise comparável e indicadores tecnicamente aprovados.
7. **Documentos/relatórios:** rastreabilidade, versionamento e exportação.
8. **Release:** CI, testes em Windows limpo, instalador/executável reproduzível.
9. **Aceite EGT:** dados anonimizados, scorecard >=80/100 e nenhuma área abaixo do nível intermediário.

## 10. Próximas entregas imediatas

- Revisar a PR #10 e executar testes na branch de destino antes do merge.
- Recuperar as 61 alterações locais da versão B e separar código, testes, documentação e artefatos.
- Integrar primeiro os módulos de domínio e persistência, depois importação/workspace, por commits pequenos.
- Corrigir os defeitos P0 documentados na Issue #9 antes de ampliar funcionalidades.

## 11. Critério para considerar a base definida

A base de produto está definida neste documento. A base de código só será considerada consolidada quando os módulos escolhidos estiverem integrados na branch de reconstrução, os testes de regressão estiverem verdes e as decisões técnicas pendentes estiverem registradas. A meta 80/100 só pode ser declarada após avaliação com evidências.
