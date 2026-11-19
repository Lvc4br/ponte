# PONTE EGT — plano de desenvolvimento

## Estratégia
Rebuild em arquitetura e branch próprios. O sistema legado permanece disponível como referência e fonte até a validação formal da migração. Não substituir nem apagar o legado durante o desenvolvimento.

## Etapa 0 — Preparação e governança
- Nomear responsáveis técnicos e usuários de engenharia.
- Confirmar definições de ponte/OAE e vocabulário corporativo.
- Inventariar planilhas, bancos, documentos e cadastros.
- Classificar dados oficiais, duplicados, incompletos e obsoletos.
- Definir matriz de permissões, RPO/RTO e ambientes com TI.

Saída: inventário de fontes, glossário, decisões e critérios de aceite.

## Etapa 1 — Fundação do rebuild
Objetivo: criar base executável, testável e implantável.

Entregas:
1. Estrutura separando desktop, API, domínio, persistência e testes.
2. API FastAPI com health check e versão.
3. Cliente PySide6 conectado à API por configuração.
4. PostgreSQL para desenvolvimento, sem credenciais no Git.
5. SQLAlchemy e Alembic com primeira migração.
6. Modelo inicial de empreendimento, ponte e localização.
7. Identificadores, chaves estrangeiras, restrições e índices.
8. Logs estruturados e erros padronizados.
9. Testes unitários e de integração.
10. CI para análise estática, compilação e testes.
11. Documentação de ambiente e configuração de exemplo sem segredos.

Critérios de aceite:
- API inicia e responde ao health check.
- Desktop conecta à API e não acessa o banco diretamente.
- Migrações criam o banco limpo e são aplicáveis em sequência.
- CRUD inicial funciona pela API.
- Relações inválidas são recusadas no servidor.
- Testes cobrem sucesso, validação e falhas.
- Nenhum segredo ou dado real da EGT está no Git.
- Ambiente pode ser recriado pela documentação.

## Etapa 2 — Cadastro técnico de pontes
Identificação, localização, classificação, geometria, vãos, elementos, validações, pesquisa paginada e exportação controlada.

## Etapa 3 — Importação e qualidade
Mapeamento de colunas, prévia, validação, relatório de rejeições, detecção de duplicidade e reconciliação entre origem e destino.

## Etapa 4 — Documentos e auditoria
Metadados, hash, revisões, vínculos, storage corporativo, histórico e pesquisa documental.

## Etapa 5 — Multiusuário e homologação
Identidade corporativa, perfis, permissões, teste de carga 30+, concorrência, recuperação, segurança e homologação com engenharia.

## Etapa 6 — Piloto e expansão
Migração piloto controlada, conferência de contagens e vínculos, treinamento, feedback, plano de produção/rollback e priorização de inspeções, patologias e intervenções.

## Definition of Done
Critérios de aceite testados; testes automatizados aprovados; migrações e recuperação documentadas; logs e erros tratados; documentação atualizada; nenhum segredo/dado corporativo no commit; revisão de código concluída.

## Não fazer na primeira etapa
Não migrar toda a base sem inventário; não implementar IA antes de estabilizar dados e permissões; não conectar desktops diretamente ao PostgreSQL; não usar JSON dinâmico como substituto do modelo relacional oficial; não expandir para todas as disciplinas simultaneamente.