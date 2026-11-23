# Revisão técnica inicial — domínio de pontes e indicadores

**Fonte revisada:** branch `feature/bridge-domain-foundation`, arquivos `app/domain/bridges.py`, `app/domain/indicator_catalog.py` e `app/domain/indicators.py`.  
**Uso:** revisão de código antes de integrar a PR #10 à `rebuild/ponte-v2`.

## Pontos positivos observados

1. O domínio é independente de PySide6 e da persistência.
2. Usa `Decimal` para grandezas e rejeita valores não finitos.
3. Mantém campos desconhecidos como `None`, sem preencher dados ausentes.
4. A validação de divergência entre comprimento total e soma dos vãos gera alerta, não altera medidas.
5. A definição de indicador exige numerador, denominador, fórmula, agregação, arredondamento, fonte e aprovador para assumir estado aprovado.
6. Resultados guardam versão da definição, unidade e referências de origem.

## Ajustes/revisões necessários antes do merge

- [ ] Validar limites geográficos: latitude e longitude estão limitadas, mas a regra de presença conjunta (ambas ou nenhuma) deve ser decidida.
- [ ] Definir unicidade de código de OAE por projeto e regra de normalização (maiúsculas, espaços, acentos).
- [ ] Confirmar se `BridgeSpan.length_m` deve ser sempre estritamente positivo e como representar vãos ainda não medidos.
- [ ] Rever campos de tipologia, sistema estrutural, material e contexto: hoje `bridge_type` é texto livre e não há catálogo controlado.
- [ ] Definir se o quantitativo aceita valor zero em todos os escopos e se deve carregar precisão/estado da unidade.
- [ ] Verificar se `MaterialQuantity` deve guardar método de medição, documento/aba/linha/célula, autor, timestamp e valor original; hoje as referências de origem são apenas strings opcionais.
- [ ] Validar se `IndicatorResult` deve impedir valor numérico quando o estado é `PENDING_VALIDATION`; hoje a regra não está explícita.
- [ ] Validar compatibilidade do identificador UUID com os IDs/chaves usados pelo WorkspaceStore legado.
- [ ] Acrescentar testes de serialização, persistência, round-trip e migração; modelos de domínio isolados não demonstram integração com SQLite.
- [ ] Executar CI e suíte de regressão na branch de destino antes do merge.

## Observação sobre Ecm

O catálogo da contribuição registra `m³/m²` como referência citada no material legado, mas a descrição deixa a confirmação técnica pendente. Manter como `draft`; não tratar como definição validada.

## Decisão

**Aprovação técnica parcial do desenho, não aprovação para merge imediato.** A fundação é adequada como domínio isolado inicial. O próximo passo é conectar esses modelos a serviços e repositórios, definir contratos de persistência e validar a suíte integrada. Nenhuma fórmula de indicador deve ser implementada nesta etapa.
