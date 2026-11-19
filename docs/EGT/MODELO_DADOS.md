# PONTE EGT — modelo de dados inicial

## Princípios
Modelo relacional explícito; UUID recomendado para entidades expostas pela API; chaves estrangeiras e restrições no banco; datas em UTC; unidades físicas explícitas; desconhecido como NULL quando apropriado; auditoria separada dos dados correntes.

## Entidades da primeira etapa

### projects — empreendimentos
- id
- code (unicidade a definir)
- name
- client reference (opcional)
- contract_reference (opcional)
- status
- created_at, updated_at

### bridges — pontes/OAE
- id
- project_id (FK)
- code (regra de unicidade a validar)
- name
- bridge_type
- purpose
- status
- construction_year (opcional)
- length_m, width_m (opcionais)
- road_reference (opcional)
- municipality, state
- latitude, longitude (opcionais)
- created_at, updated_at

## Estrutura de indicadores técnicos
Os indicadores por taxas devem ser dados derivados de informações de origem, não números digitados sem rastreabilidade. O modelo definitivo deverá permitir:
- catálogo de indicadores com código, nome, unidade de exibição, definição, fórmula/versão e situação de aprovação;
- valores-base e quantitativos com unidade, origem, entidade/escopo relacionado e revisão;
- denominadores de referência (área, volume ou outra base aprovada) identificados explicitamente;
- resultados calculados vinculados à ponte/OAE, escopo, versão da regra, data de cálculo e dados de origem;
- estado do resultado: calculado, indisponível por falta de dados, pendente de validação ou aprovado;
- histórico para reproduzir resultados após alterações dos dados ou das fórmulas.

Catálogo inicial obrigatório:
| Código/indicador | Unidade solicitada | Definição/fórmula |
|---|---|---|
| Paf | kg/m² | A validar com engenharia |
| Pap | kg/m² | A validar com engenharia |
| Ecm | m³/² (notação recebida; confirmar se é m³/m²) | A validar com engenharia |
| Af | m²/m² | A validar com engenharia |
| Aço total indicativo | kg/m² e kg/m³ | A validar com engenharia |

Não inferir o significado das siglas nem assumir a base de cálculo. A engenharia deve aprovar numerador, denominador, escopo de agregação, unidade, arredondamento e regras para dados ausentes antes da implementação definitiva.

## Próximas entidades
bridge_spans; bridge_elements; materials; quantities; indicator_definitions; indicator_results; inspections; inspection_findings; interventions; documents; document_revisions; audit_events.

## Relações conceituais
Um empreendimento pode conter várias pontes. Uma ponte pode conter vários vãos, elementos, inspeções e intervenções. Documentos podem se relacionar a empreendimento, ponte, elemento, inspeção ou intervenção. Revisões pertencem a um documento lógico e não devem ser sobrescritas. Quantitativos e resultados de indicadores devem apontar para suas fontes e versões.

## Regras a validar com engenharia
Definição corporativa de OAE; se ponte pode pertencer a mais de um contrato; regra de código único; tipologias; materiais e sistemas estruturais; unidades; coordenadas; campos obrigatórios por tipologia; regras de arquivamento e duplicidade; fórmulas e bases dos indicadores.

## Auditoria
Registrar identidade do usuário, instante UTC, operação, entidade, identificador, valores anteriores/posteriores ou diff seguro, origem da operação e correlação da requisição. Não copiar conteúdo sensível ou binário indiscriminadamente para logs.