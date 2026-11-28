# Contexto compartilhado: GED e PONTE (EGT Engenharia)

## Empresa e domínio
Os dois projetos são ferramentas internas da EGT Engenharia, para
engenharia civil (obras de arte especiais / pontes). Trabalham com os
MESMOS projetos, identificados pelo código do projeto (ex.: AB20A),
mas em etapas diferentes do ciclo de vida. Atendem a processos de
qualidade (NBR ISO 9001): rastreabilidade, revisão controlada, evidência.

## Ciclo de vida de um projeto
1. Durante o projeto: plantas, documentos e revisões -> GED
2. Obra finalizada: quantitativos e taxas de materiais -> PONTE

## GED (Lvc4br/Gerenciador-de-dados)
- Propósito: organizar, indexar, comparar e rastrear plantas e documentos.
- Entrada: pastas e arquivos (DWG, PDF, DOCX, XLSX, CSV).
- Saída: catálogo, hash SHA-256, revisões, divergências, manifesto.
- Nunca altera originais. Revisões são imutáveis.
- Estado: apenas especificação; sem código ainda.

## PONTE (Lvc4br/ponte)
- Propósito principal: estimativa preliminar de quantitativos a partir
  da base histórica (largura, vão, comprimento -> taxas de aço frouxo,
  aço protendido e cimento) e gestão dos dados do projeto finalizado.
- Entrada: planilha histórica (preservada), dados de projetos finalizados.
- Saída: taxas, tabela de materiais, relatórios Excel/PDF.
- Não extrapola automaticamente. É só estimativa preliminar.
- Estado: funcional, mas nunca testado num Windows real.

## Fronteira e vínculo
- Cada app é dono dos seus dados. Nenhum grava no banco do outro.
- Chave comum: código do projeto, normalizado (maiúsculas, sem espaços).
- Troca por manifesto CSV/JSON: projeto, arquivo, hash, revisão, caminho.
- O PONTE só LÊ referências de documentos; o GED só guarda referência
  à tabela de materiais.

## Regras para qualquer alteração
1. Nada de dados reais da empresa no repositório (público).
2. Não ampliar escopo: só o que a etapa do projeto exige.
3. Cada afirmação do README precisa de teste ou evidência.
4. Dependências externas (Tesseract, LibreOffice, ODA) são opcionais
   e devem avisar claramente quando faltarem.
5. Um problema por PR, sempre com teste. Nunca inventar dados ou unidades.
6. Em dúvida sobre regra de engenharia, perguntar; não presumir.
