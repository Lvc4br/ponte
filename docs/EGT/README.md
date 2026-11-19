# PONTE EGT — documentação do rebuild

Esta pasta define a direção do novo produto corporativo PONTE.

- [Visão e escopo](VISAO_PRODUTO.md)
- [Arquitetura de implantação](ARQUITETURA_IMPLANTACAO.md)
- [Plano de desenvolvimento](PLANO_DESENVOLVIMENTO.md)
- [Modelo de dados inicial](MODELO_DADOS.md)
- [Política de inventário e limpeza](LIMPEZA_REPOSITORIO.md)

## Decisões estabelecidas

| Tema | Decisão |
|---|---|
| Objetivo | Banco central de dados de engenharia |
| Domínio inicial | Pontes e OAE |
| Cliente | Aplicação desktop |
| Estratégia | Rebuild |
| Concorrência | 30+ usuários |
| Banco de produção | PostgreSQL |
| Acesso ao banco | Exclusivamente pela API central |
| Legado | Preservado durante a transição |

Status: documentação inicial. Validar decisões operacionais com TI, engenharia e responsáveis pelos dados da EGT.