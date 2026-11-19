# PONTE EGT — plano de desenvolvimento

## Estratégia
Rebuild em arquitetura e branch próprios, com entregas incrementais utilizáveis. O sistema legado permanece disponível como referência e fonte até a validação formal da migração. Não substituir nem apagar o legado durante o desenvolvimento.

## Requisito permanente: executável funcional
O projeto deverá produzir e manter um executável desktop utilizável desde as primeiras etapas, antes da conclusão de todo o rebuild. Isso é uma linha de entrega contínua e obrigatória, não uma atividade deixada para o final.
- Cada marco deverá resultar em uma versão que inicia e executa os fluxos já entregues.
- A primeira versão utilizável deve cobrir ao menos conexão/configuração com a API, consulta e cadastro inicial de empreendimentos e pontes, validações e tratamento de erros.
- A interface deverá consumir a API; nunca conectar diretamente ao PostgreSQL.
- Cada versão deverá ter processo reproduzível de build, identificação de versão, configuração externa, instruções de instalação/execução e testes de fumaça.
- Dados do usuário e configurações não podem ser perdidos durante atualização; manter compatibilidade/migração documentada.
- O executável será aprimorado etapa a etapa, sem bloquear o uso das funcionalidades estáveis já entregues.
- Distribuição corporativa, assinatura, atualização automática e instalador final serão definidos com a TI; não presumir privilégios de administrador.

## Requisito permanente: indicadores por taxas
Os indicadores Paf (kg/m²), Pap (kg/m²), Ecm (m³/² — unidade a confirmar), Af (m²/m²) e Aço total indicativo (kg/m² e kg/m³) são requisitos obrigatórios e deverão estar presentes no produto durante toda a evolução. A primeira versão poderá implementar o conjunto progressivamente, mas cada indicador já especificado deverá permanecer rastreado no backlog, modelo de dados, interface, documentação e testes. Antes de codificar fórmulas, engenharia deverá aprovar definição, numerador, denominador, unidade, regra de agregação e arredondamento.
- Exibir valor e unidade claramente.
- Identificar a estrutura/escopo e a base de referência usada no denominador.
- Calcular a partir de dados de origem identificáveis e versionados.
- Não converter ausência de dados em zero.
- Cobrir fórmulas com testes unitários, inclusive casos sem dados e limites.
- Permitir conferência/reprodução do cálculo e registrar a versão da regra aplicada.

## Etapa 0 — Preparação e governança
- Nomear responsáveis técnicos e usuários de engenharia.
- Confirmar definições de ponte/OAE e vocabulário corporativo.
- Validar formalmente definições e fórmulas dos indicadores Paf, Pap, Ecm, Af e aço total indicativo.
- Inventariar planilhas, bancos, documentos e cadastros.
- Classificar dados oficiais, duplicados, incompletos e obsoletos.
- Definir matriz de permissões, RPO/RTO e ambientes com TI.

Saída: inventário de fontes, glossário, catálogo de indicadores, decisões e critérios de aceite.

## Etapa 1 — Fundação do rebuild
Objetivo: criar base executável, testável e implantável, com uma primeira versão desktop funcional.

Entregas:
1. Estrutura separando desktop, API, domínio, persistência e testes.
2. API FastAPI com health check e versão.
3. Cliente PySide6 conectado à API por configuração.
4. Primeiro executável desktop empacotado e testado em máquina limpa/perfil de usuário padrão, sem depender do ambiente de desenvolvimento.
5. PostgreSQL para desenvolvimento, sem credenciais no Git.
6. SQLAlchemy e Alembic com primeira migração.
7. Modelo inicial de empreendimento, ponte e localização, com campos necessários para as bases dos indicadores.
8. Identificadores, chaves estrangeiras, restrições e índices.
9. Logs estruturados e erros padronizados.
10. Testes unitários, de integração e fumaça do executável.
11. CI para análise estática, compilação e testes.
12. Documentação de ambiente, build, instalação, configuração e exemplo sem segredos.

Critérios de aceite:
- API inicia e responde ao health check.
- Desktop conecta à API e não acessa o banco diretamente.
- Executável instala/inicia e executa os fluxos liberados em ambiente limpo.
- Migrações criam o banco limpo e são aplicáveis em sequência.
- CRUD inicial funciona pela API e pela interface empacotada.
- Relações inválidas são recusadas no servidor.
- Testes cobrem sucesso, validação, falhas e cálculos implementados.
- Nenhum segredo ou dado real da EGT está no Git.
- Ambiente e build podem ser recriados pela documentação.

## Etapa 2 — Cadastro técnico de pontes
Identificação, localização, classificação, geometria, vãos, elementos, dados-base dos indicadores, fórmulas aprovadas, apresentação das taxas, validações, pesquisa paginada e exportação controlada. O executável continua sendo gerado e testado a cada entrega.

## Etapa 3 — Importação e qualidade
Mapeamento de colunas, prévia, validação, relatório de rejeições, detecção de duplicidade e reconciliação entre origem e destino. Importações devem preservar a origem dos dados usados nos indicadores.

## Etapa 4 — Documentos e auditoria
Metadados, hash, revisões, vínculos, storage corporativo, histórico e pesquisa documental. O executável continua evoluindo.

## Etapa 5 — Multiusuário e homologação
Identidade corporativa, perfis, permissões, teste de carga 30+, concorrência, recuperação, segurança e homologação com engenharia, incluindo validação dos indicadores e do executável em estações representativas.

## Etapa 6 — Piloto e expansão
Migração piloto controlada, conferência de contagens e vínculos, treinamento, feedback, plano de produção/rollback e priorização de inspeções, patologias e intervenções.

## Definition of Done
Critérios de aceite testados; testes automatizados aprovados; migrações e recuperação documentadas; logs e erros tratados; documentação atualizada; nenhum segredo/dado corporativo no commit; revisão de código concluída; executável da versão gerado e testado quando aplicável; indicadores e fórmulas implementados/testados conforme o marco, sem retirar requisitos pendentes do backlog.

## Não fazer na primeira etapa
Não migrar toda a base sem inventário; não implementar IA antes de estabilizar dados e permissões; não conectar desktops diretamente ao PostgreSQL; não usar JSON dinâmico como substituto do modelo relacional oficial; não expandir para todas as disciplinas simultaneamente; não deixar a geração do executável para o fim do projeto.