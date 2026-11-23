# PONTE v2 — Roadmap de desenvolvimento

**Objetivo:** versão desktop profissional para a EGT Engenharia, inicialmente centrada em pontes e OAEs, com meta de avaliação mínima de 80/100 e maturidade intermediária em todas as áreas.

Plano mestre, requisitos completos, defeitos conhecidos e critérios de aceite: https://github.com/Lvc4br/ponte/issues/8

## Estratégia de consolidação
- Preservar A (main, 287bf7b) como baseline publicada e protegida.
- Usar B (396f7d1 e alterações locais ainda não commitadas) como principal referência funcional, após inventário e recuperação integral.
- Preservar C (4a5457e) como referência histórica independente; aproveitar apenas conceitos de cadastro e distribuição após correção e validação.
- Reaproveitar o domínio de pontes/indicadores da PR #7 e avaliar as PRs #3–#6 por dependências e testes.
- Não mesclar redesigns concorrentes #1 e #2 sem comparação visual e funcional.

## Fases e gates
| Fase | Entrega | Gate para avançar |
|---|---|---|
| 0 | Congelamento, inventário, hashes e backup A/B/C, branches, PRs e artefatos | Todas as fontes preservadas e identificadas |
| 1 | Arquitetura modular e domínio de projetos/OAEs | Modelo e migrações documentados |
| 2 | Integridade, transações, exclusão, backup/restauração | Zero P0; regressões aprovadas |
| 3 | Workspace e importação/exportação | CSV pt-BR e XLSX validados ponta a ponta |
| 4 | Cadastro OAE, quantitativos e catálogo de indicadores | Unidades e fórmulas revisadas tecnicamente |
| 5 | Análises comparáveis e relatórios rastreáveis | Critérios/amostras/limitações visíveis |
| 6 | Biblioteca documental, extração, OCR opcional e revisão | Originais, hashes, versões e busca testados |
| 7 | Autenticação, autorização e auditoria | Testes negativos e trilha íntegra |
| 8 | UX/UI, acessibilidade, desempenho e build | Testes em Windows limpo e CI verde |
| 9 | Validação com dados anonimizados da EGT e scorecard | >=80/100 e nenhuma área abaixo do nível 3 |

## Regras de segurança do repositório
1. Não fazer commits diretamente em main.
2. Não apagar branches, PRs, bancos ou backups antes de inventariar e provar preservação.
3. Não versionar dados reais, credenciais, executáveis, .venv, __pycache__, build ou dist.
4. Toda correção de defeito conhecido deve começar por teste de regressão.
5. Indicadores sem definição técnica aprovada permanecem pendentes e não podem alimentar conclusões decisórias.
6. Cada release deve ser reproduzível e vinculada a commit, versão, dependências e hash do artefato.

## Defeitos de regressão prioritários
- Órfãos em obras após exclusão de records.
- Escrita não atômica entre registro, projeção técnica e fingerprint.
- Restauração de SQLite sem schema completo obrigatório.
- CSV brasileiro com delimitador ; e decimal ,.
- Cadastro C que troca área e número de vãos.
- Importação C que não promove staging para registros e não trata XLSX inlineStr.
- Sobrescrita de documentos com nomes iguais.
- Ausência de autenticação/permissões efetivas e credencial padrão insegura.

## Indicadores que exigem aprovação técnica
Paf (kg/m²), Pap (kg/m²), Ecm (definição e unidade pendentes), Af (m²/m²), aço total indicativo (kg/m² e kg/m³). Nenhuma fórmula ou unidade será presumida como aprovada sem validação responsável.

## Estado
Esta branch foi criada a partir de rebuild/egt-foundation para iniciar a próxima versão sem alterar main. O conteúdo das alterações locais da versão B ainda precisa ser recuperado e inventariado antes de transplantar código.