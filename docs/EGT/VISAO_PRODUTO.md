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

## Escopo da primeira versão
Incluído: empreendimentos; cadastro e identificação única de pontes/OAE; localização e características gerais; vãos e elementos estruturais em nível cadastral; documentos vinculados; pesquisa paginada no servidor; importação assistida; usuários, perfis e permissões básicas; auditoria.

Fora do primeiro corte: cálculo ou dimensionamento estrutural; substituição de softwares especializados; aprovação técnica automática; interpretação garantida de todos os formatos CAD/BIM; IA generativa como requisito do núcleo; expansão simultânea para todas as disciplinas.

## Princípios
- Entidades técnicas possuem identificador estável.
- Dados desconhecidos permanecem não informados; não inventar valores.
- Documentos são vinculados por metadados, revisão e relação com a estrutura.
- Alterações importantes são rastreáveis.
- Regras críticas ficam no servidor, não apenas na interface.
- Importações não sobrescrevem dados oficiais sem validação e confirmação.
- A base legada é preservada até a validação formal da migração.

## Perfis iniciais
Administrador do sistema; gestor de projeto; engenheiro; consulta; auditor. A matriz definitiva deve ser aprovada pela EGT.

## Indicadores de sucesso
Completude dos cadastros; duplicidades resolvidas; tempo de pesquisa; alterações rastreáveis; taxa de sucesso de importação; disponibilidade; restauração testada; adoção pelos usuários-piloto.