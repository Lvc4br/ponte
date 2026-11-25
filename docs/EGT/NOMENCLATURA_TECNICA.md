# Nomenclatura técnica e equivalência de tipos

## Objetivo

Permitir que o EGT compare e reúna registros de planilhas que descrevem o mesmo
tipo de estrutura com nomenclaturas diferentes, sem alterar o texto original
importado.

## Modelo de três camadas

1. **Conceito canônico:** categoria técnica usada para comparação e agrupamento.
2. **Vetor de nomenclaturas:** lista explícita de termos aprovados como equivalentes.
3. **Valor de origem:** texto original da planilha, preservado no registro.

## Exemplo implementado

O conceito canônico **Ponte estaiada** reconhece, nesta versão, as variantes
explícitas:

- Ponte estaiada / Pontes estaiadas
- Ponte atirantada / Pontes atirantadas
- Ponte com estais / Ponte de estais
- Cable stayed bridge / Cable stayed bridges

A comparação ignora diferenças de caixa, acentos, espaços repetidos e
pontuação. Os filtros da base legada e do espaço de dados usam a mesma regra.

## Segurança da classificação

A lista é intencionalmente conservadora. Termos amplos como **estrutura
estaiada** não são automaticamente convertidos em ponte estaiada. Sistemas
diferentes, como ponte estaiada e ponte pênsil, permanecem separados.

Rótulos desconhecidos continuam disponíveis como texto original e podem ser
listados por `terminology_report` para revisão e inclusão manual futura. O
sistema não usa similaridade aproximada para inventar equivalências.

## Extração e análise

A normalização é aplicada somente durante a comparação. Ela não reescreve
células, não renomeia colunas e não altera registros existentes no SQLite.
Dessa forma, os dados originais continuam disponíveis para exportação,
auditoria e rastreabilidade.

## Limites desta atualização

O dicionário inicial cobre tipos de pontes estaiadas. Novas famílias de
estruturas e novos sinônimos devem ser adicionados após validação técnica.
Esta atualização de código precisa ser empacotada em um novo `EGT.exe` antes
de chegar à instalação Windows do usuário.
