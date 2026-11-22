# PONTE EGT — status da fundação de domínio

Atualizado em 2026-11-22.

## Branch de trabalho

- Branch: feature/bridge-domain-foundation
- Base: rebuild/egt-foundation
- Branch main: preservada, sem alterações nesta entrega.
- Objetivo: introduzir contratos de domínio de pontes/OAEs e indicadores sem acoplar regras técnicas à interface ou à persistência.

## Entregue nesta etapa

- Modelos independentes para empreendimento, ponte/OAE, vão e quantitativo de material.
- Identificadores UUID.
- Medidas armazenadas como Decimal nos modelos de domínio.
- Validações de dimensões, coordenadas, sequência de vãos, unidade e escopo de quantitativos.
- Validação geométrica que gera aviso quando a soma dos vãos diverge do comprimento total; nenhum valor é corrigido automaticamente.
- Modelos para definição versionada de indicadores e resultados.
- Bloqueio de aprovação de indicador sem numerador, denominador, fórmula, agregação, arredondamento, fonte e responsável.
- Resultado indisponível não pode ser representado como zero.
- Catálogo inicial de Paf, Pap, Ecm, Af e aço total indicativo em kg/m² e kg/m³, todos em rascunho e sem fórmula inventada.
- Testes automatizados adicionados para os contratos e regras acima.
- Workflows de teste e pacote Windows configurados para executar também em branches feature/*.

## Não concluído / não validado

- Os testes desta branch ainda precisam ser executados em CI; não declarar aprovação até existir execução concluída.
- Não existe ainda API FastAPI nesta entrega.
- Não existe persistência PostgreSQL nesta entrega.
- Os modelos ainda não estão ligados à interface desktop.
- Não há autenticação corporativa nem identidade confiável para aprovações.
- Não há migração da base legada.
- Fórmulas e definições técnicas dos indicadores continuam pendentes de validação da engenharia.

## Próxima sequência recomendada

1. Executar CI e corrigir eventuais falhas.
2. Implementar persistência relacional e migrações, mantendo SQLite legado preservado.
3. Criar API FastAPI com health check, versão e CRUD inicial de empreendimentos e pontes.
4. Conectar a aplicação desktop à API por configuração, sem acesso direto ao PostgreSQL.
5. Implementar cadastro de vãos e quantitativos na interface.
6. Implementar importação assistida com rastreabilidade e revisão.
7. Integrar catálogo e resultados de indicadores após validação das definições técnicas.

## Regra permanente

Esta branch é uma etapa de desenvolvimento. Não mesclar na main nem utilizar como versão corporativa até testes, revisão, integração, migração e homologação apropriados.
