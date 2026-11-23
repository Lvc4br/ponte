# PONTE v2 — Especificação funcional e visual baseada no Design System

Fonte: arquivo enviado `Ponte — Design System e Interface.pdf` (7 páginas). Esta especificação preserva a organização e os fluxos apresentados no PDF. Números, nomes de obras, amostras e status exibidos nas telas são dados demonstrativos e NÃO devem ser tratados como dados reais ou validados.

## Direção visual comum
- Aplicação desktop com navegação lateral persistente e área principal de trabalho.
- Identidade: PONTE / Engenharia • Inteligência; contexto EGT Engenharia.
- Menu principal: Visão geral; Projetos e obras; Pontes e OAEs; Importar dados; Análise de engenharia; Documentos; Relatórios.
- Rodapé da navegação informa o modo de armazenamento. A primeira entrega é workspace local; não comunicar sincronização multiusuário enquanto ela não existir.
- Interface clara, fundo cinza muito claro, cartões brancos, sidebar azul-marinho, ações primárias azuis e estados de validação discretos.
- Layout deve ser responsivo ao tamanho da janela, acessível por teclado e consistente em tabelas, filtros, formulários e estados vazios.

## Tela 1 — Visão geral / Painel operacional
Objetivo: resumir o estado dos dados locais e conduzir às tarefas frequentes.
- Indicadores: projetos cadastrados, pontes e OAEs, dados pendentes e conjuntos analisáveis.
- Atividade recente com evento, entidade, data/hora e situação.
- Painel de pendências de validação: unidades não identificadas, campos geométricos ausentes, quantitativos duplicados e origem não informada.
- Acesso rápido: importar planilha, analisar dados, consultar OAEs e gerar relatório.
- Todos os indicadores devem ser calculados a partir do banco e refletir filtros/escopo; nunca fixar os números demonstrativos do protótipo.

## Tela 2 — Análise de engenharia / Filtros e indicadores
Objetivo: selecionar amostras tecnicamente comparáveis, não apenas filtrar números isolados.
- Seleção do conjunto de dados e escopo (todas as OAEs ou subconjunto).
- Filtros por intervalo: comprimento total (m), largura do tabuleiro (m), área do tabuleiro (m²) e volume de concreto (m³).
- Resultados: quantidade de registros encontrados e filtros ativos.
- Cartões de indicadores com valor, unidade, tamanho da amostra e estado de validação.
- Tabela de amostras com identificação, tipologia, vão total, concreto, aço e status.
- Ações aplicar filtros, limpar e exportar.
- A tela deve expor critérios de compatibilidade técnica adicionais: tipologia, sistema estrutural, material, configuração de vãos e contexto, conforme taxonomia validada.
- Exibir n, exclusões, dados ausentes, outliers, origem e avisos de amostra insuficiente. Não comparar automaticamente obras apenas por proximidade geométrica.
- Os valores ilustrativos do PDF (por exemplo 112,4 kg/m³, 0,38 m³/m² e 42,7 kg/m²) não são fórmulas ou resultados aprovados.

## Tela 3 — Importar dados / Entrada e validação de planilhas
Fluxo obrigatório em cinco etapas:
1. Selecionar arquivo e abas.
2. Conferir prévia de cabeçalhos, linhas, tipos e valores originais.
3. Mapear colunas a campos, unidades e escopo com confirmação explícita.
4. Validar ausências, duplicidades, incompatibilidades e inconsistências.
5. Importar transacionalmente e abrir a análise do conjunto importado.
- Formatos prioritários: XLSX, XLS e CSV, conforme dependências suportadas e documentadas.
- Preservar arquivo original e registrar hash, nome, tamanho, aba, linha/célula, mapeamento, usuário, data e versão do importador.
- Nenhuma unidade, fórmula ou valor pode ser corrigido silenciosamente.
- Relatório de importação deve permitir revisar erros e rejeições antes e depois da confirmação.

## Tela 4 — Projetos e obras
Objetivo: visão consolidada dos empreendimentos e contratos aos quais OAEs pertencem.
- Pesquisa por projeto, contrato ou responsável; filtros por status e responsável.
- Indicadores de projetos ativos, OAEs vinculadas, empreendimentos em execução e pendências.
- Tabela: projeto/contrato, local, quantidade de OAEs, etapa, responsável e status.
- Cada OAE deve manter vínculo obrigatório ou explicitamente pendente com projeto, contrato, localização, documentos e origem dos quantitativos.
- Não preencher dados ausentes por inferência; permitir estado 'não informado' e fila de validação.

## Tela 5 — Relatórios e exportações
Objetivo: transformar conjuntos filtrados em entregáveis rastreáveis.
- Modelos: resumo executivo; comparativo de OAEs; relatório de importação; mapa de quantitativos.
- Histórico: relatório, escopo, formato, data, versão metodológica e status.
- Cada relatório registra filtros, tamanho e critérios da amostra, exclusões, unidades, origem, fórmulas, versões de dados e metodologia.
- Formatos previstos: PDF, XLSX e CSV, com validação de conteúdo e proteção contra formula injection.
- Estimativas históricas devem ser rotuladas como estimativas e nunca como quantitativos executivos.

## Tela 6 — Pontes e OAEs / Cadastro técnico
Objetivo: ficha técnica única e rastreável por OAE.
- Abas: Identificação; Geometria; Materiais e quantitativos; Inspeções; Documentos; Histórico.
- Identificação: código, nome, projeto, tipologia, município/UF, rodovia/km, latitude e longitude.
- Geometria: comprimento total, largura do tabuleiro, área, número de vãos, comprimento individual dos vãos e altura estrutural.
- Materiais e quantitativos: itens, quantidades, unidades, método/origem e estado de validação.
- Cada valor preserva unidade, fonte, arquivo/aba/linha/célula, autor, data, valor original e histórico de alterações.
- A área derivada deve ser calculada e identificada como derivada, com regra explícita; não trocar área por número de vãos nem preencher ausência silenciosamente.
- Valores da OAE-014 e demais campos exemplificados no PDF são fictícios para composição visual.

## Tela 7 — Documentos
Objetivo: repositório documental do empreendimento vinculado às entidades do PONTE.
- Pesquisa por nome, código ou OAE; filtros por tipo e versão.
- Ações adicionar documento e abrir/consultar versão.
- Indicadores: arquivos vinculados, documentos técnicos, aguardando revisão e versões recentes.
- Tabela: documento, categoria, vínculo, versão, atualização e situação.
- Metadados obrigatórios: nome original, hash SHA-256, tamanho, formato, origem, autor, data/hora, versão, entidade vinculada, permissões e trilha de auditoria.
- Preservar arquivo original; impedir sobrescrita por colisão de nome; suportar versionamento, exclusão lógica, confirmação explícita e recuperação conforme retenção.
- Busca textual sobre conteúdo extraído, com indicação de página/trecho e revisão humana para OCR.
- Formatos CAD/BIM: declarar claramente o nível de suporte por formato e dependência. Não prometer leitura nativa RVT/RFA ou DWG sem conversor validado.

## Critérios transversais de aceite
- Nenhum número de tela demonstrativa é hardcoded como dado real.
- Todas as telas têm estados carregando, vazio, erro, sem permissão e dados incompletos.
- Todas as ações críticas geram feedback e trilha de auditoria.
- Navegação, formulários e tabelas operáveis por teclado; foco visível e contraste suficiente.
- Testes automatizados cobrem os fluxos de ponta a ponta: cadastrar OAE, importar planilha, validar, analisar, anexar documento e gerar relatório.
- A interface deve consumir serviços de domínio; regras de negócio não ficam presas aos widgets.
- A primeira versão pode ser local/offline, mas deve deixar explícita a limitação. Multiusuário central para 30+ usuários exige arquitetura de servidor e banco apropriado antes de ser declarado suportado.