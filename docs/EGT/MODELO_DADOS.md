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

## Próximas entidades
bridge_spans; bridge_elements; materials; inspections; inspection_findings; interventions; documents; document_revisions; audit_events.

## Relações conceituais
Um empreendimento pode conter várias pontes. Uma ponte pode conter vários vãos, elementos, inspeções e intervenções. Documentos podem se relacionar a empreendimento, ponte, elemento, inspeção ou intervenção. Revisões pertencem a um documento lógico e não devem ser sobrescritas.

## Regras a validar com engenharia
Definição corporativa de OAE; se ponte pode pertencer a mais de um contrato; regra de código único; tipologias; materiais e sistemas estruturais; unidades; coordenadas; campos obrigatórios por tipologia; regras de arquivamento e duplicidade.

## Auditoria
Registrar identidade do usuário, instante UTC, operação, entidade, identificador, valores anteriores/posteriores ou diff seguro, origem da operação e correlação da requisição. Não copiar conteúdo sensível ou binário indiscriminadamente para logs.