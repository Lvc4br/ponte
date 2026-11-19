# PONTE EGT — visão do produto

## Propósito
O PONTE será o banco central de dados técnicos de engenharia da EGT. O primeiro domínio será pontes e obras de arte especiais (OAE). O produto permitirá cadastrar, relacionar, consultar e rastrear informações técnicas ao longo do ciclo de vida das estruturas.

Não deve ser tratado como planilha compartilhada, ERP genérico ou repositório de arquivos sem metadados.

## Objetivos
1. Manter uma fonte central e controlada de dados de pontes.
2. Relacionar empreendimentos, estruturas, componentes, inspeções, intervenções e documentos.
3. Reduzir duplicidade e divergência de cadastros.
4. Registrar autoria, data e conteúdo das alterações relevantes.
5. Oferecer pesquisa e relatórios consistentes.
6. Permitir expansão futura para outros domínios sem comprometer o núcleo.
7. Disponibilizar desde as primeiras entregas um executável desktop utilizável, evoluindo continuamente até a plataforma corporativa.

## Escopo da primeira versão
Incluído: empreendimentos; cadastro e identificação única de pontes/OAE; localização e características gerais; vãos e elementos estruturais em nível cadastral; documentos vinculados; pesquisa paginada no servidor; importação assistida; usuários, perfis e permissões básicas; auditoria; indicadores técnicos calculados por taxas, com unidades e bases de referência explícitas.

O executável inicial deverá ser utilizável antes da conclusão do rebuild completo. A entrega será incremental: cada versão deverá iniciar, permitir executar fluxos reais já implementados, preservar os dados e oferecer atualização controlada. Não será aceita uma sequência de protótipos descartáveis ou apenas telas sem operações funcionais.

Fora do primeiro corte: cálculo ou dimensionamento estrutural; substituição de softwares especializados; aprovação técnica automática; interpretação garantida de todos os formatos CAD/BIM; IA generativa como requisito do núcleo; expansão simultânea para todas as disciplinas.

## Indicadores técnicos obrigatórios
Os indicadores por taxas fazem parte do produto desde a fundação e devem permanecer no escopo durante todas as etapas. A lista inicial solicitada é:
- Paf (kg/m²)
- Pap (kg/m²)
- Ecm (m³/²) — notação recebida; confirmar com a engenharia se a unidade pretendida é m³/m² ou outra antes de fixar a fórmula.
- Af (m²/m²)
- Aço total indicativo (kg/m²) e (kg/m³)

As siglas Paf, Pap, Ecm e Af, seus numeradores, denominadores e critérios de agregação precisam ser formalmente definidos e validados pela engenharia da EGT. Não inferir o significado das siglas nem preencher valores ausentes. Cada indicador deve exibir valor, unidade, base de cálculo, período/versão dos dados de origem e estado de validação. Os cálculos devem usar dados rastreáveis e unidades coerentes; indicadores sem dados suficientes devem aparecer como indisponíveis, nunca como zero fictício.

## Princípios
- Entidades técnicas possuem identificador estável.
- Dados desconhecidos permanecem não informados; não inventar valores.
- Documentos são vinculados por metadados, revisão e relação com a estrutura.
- Alterações importantes são rastreáveis.
- Regras críticas ficam no servidor, não apenas na interface.
- Importações não sobrescrevem dados oficiais sem validação e confirmação.
- A base legada é preservada até a validação formal da migração.
- Indicadores são calculados de forma consistente, testável e reproduzível.
- O executável funcional é uma entrega contínua, não uma etapa final.

## Perfis iniciais
Administrador do sistema; gestor de projeto; engenheiro; consulta; auditor. A matriz definitiva deve ser aprovada pela EGT.

## Indicadores de sucesso
Completude dos cadastros; duplicidades resolvidas; tempo de pesquisa; alterações rastreáveis; taxa de sucesso de importação; disponibilidade; restauração testada; adoção pelos usuários-piloto; consistência e rastreabilidade dos indicadores técnicos; disponibilidade de um executável funcional em cada marco de entrega.