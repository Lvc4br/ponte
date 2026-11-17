# Contribuindo

## Fluxo de trabalho

1. Abra uma issue descrevendo o problema ou a melhoria.
2. Crie uma branch para a alteração.
3. Mantenha mudanças pequenas e com objetivo único.
4. Adicione ou atualize testes automatizados.
5. Execute python -m compileall -q app tests main.py e python -m pytest -v.
6. Abra um pull request com resumo, motivação, riscos e evidências dos testes.

## Regras de dados e engenharia

- Nunca inclua SQL real, dados corporativos, planilhas, credenciais ou dados pessoais.
- Preserve os valores originais; transformações devem ser explicitadas e testadas.
- Não interprete colunas sem documentação confiável.
- Não impute dados ausentes nem trate estatísticas como validação estrutural.
- Não deduplique segmentos sem uma chave e regra de negócio documentadas.

## Compatibilidade

O CI cobre Windows e Ubuntu com Python 3.11, 3.12 e 3.13. Mudanças no empacotamento devem manter a execução portátil no Windows.
