# PONTE EGT — núcleo de domínio de pontes e OAEs

## Objetivo

Este documento descreve o primeiro núcleo de domínio independente da interface e do banco de dados. Ele não substitui o modelo relacional de produção; estabelece contratos que poderão ser persistidos pela futura API.

## Entidades iniciais

- Project: empreendimento que agrupa estruturas.
- Bridge: ponte/OAE identificada dentro de um empreendimento.
- BridgeSpan: vão numerado e associado à estrutura.
- MaterialQuantity: quantitativo de material com unidade, escopo e vínculo à ponte.
- IndicatorDefinition: definição versionada de um indicador.
- IndicatorResult: resultado associado à estrutura, versão da definição, unidade e referências de origem.

Todas as entidades usam identificadores UUID para facilitar futura exposição por API. Medidas decimais usam Decimal para evitar imprecisão binária desnecessária.

## Regras de integridade

- Código e nome da ponte são obrigatórios.
- Dimensões informadas precisam ser positivas.
- Latitude e longitude precisam respeitar seus intervalos geográficos.
- A sequência dos vãos não pode se repetir.
- Quantitativos exigem material, unidade e escopo.
- Valores desconhecidos permanecem ausentes; não são convertidos em zero.
- Diferença entre comprimento total e soma dos vãos gera aviso, não correção automática. Os escopos podem incluir elementos diferentes, como encontros, juntas ou acessos.

## Indicadores legados

Paf, Pap, Ecm e Af podem ser cadastrados sem fórmula, como definições em rascunho. A aprovação exige numerador, denominador, fórmula, agregação, arredondamento, fonte, responsável e data de aprovação.

A unidade Ecm deve permanecer sujeita à confirmação técnica; a notação m³/m² não deve ser tratada como definitiva sem validação.

## Limites desta entrega

Este núcleo é composto por modelos e validações em memória. Ainda não representa:
- API FastAPI;
- persistência PostgreSQL;
- autenticação corporativa;
- workflow de aprovação com identidade autenticada;
- motor de fórmulas de indicadores;
- migração de dados legados.

Essas capacidades serão adicionadas em etapas separadas e testadas.
