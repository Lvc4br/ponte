# Correções para o PONTE (pacote de apoio)

Este pacote NÃO contém o projeto inteiro. Contém as peças independentes do
código de `app/` (testadas), para você aplicar no repositório Lvc4br/ponte.

## Conteúdo
- `tools/checar_acentos.py` – acha e corrige acentos virados "?" e arquivos fora de UTF-8.
- `app/formatters.py` – datas dd/mm/aaaa e números pt-BR (1.308,50 / 97,4%).
- `tests/` – testes das duas peças.
- `PROMPT_CLAUDE_CODE.md` – pedido completo para o Claude Code integrar tudo e abrir o PR.

## Como aplicar
1. Copie `tools/`, `app/formatters.py` e `tests/*` para a raiz do repositório.
2. Rode `python tools/checar_acentos.py` (só relata). Depois
   `python tools/checar_acentos.py --corrigir` (corrige e cria `.bak`).
3. Na tabela e no painel de indicadores, passe cada valor por
   `fmt_celula(valor, tipo_da_coluna)`, `fmt_numero(...)` ou `fmt_percentual(...)`.
4. Rode `python -m pytest -v` e `python main.py`; confira a tela.

## Ainda depende do código de app/ (use o PROMPT_CLAUDE_CODE.md)
- Painel "Resumo estatístico" cortado (alargar coluna direita, esticar só a 1ª coluna).
- Um único botão primário por tela; aba "Planilha" no tema escuro.
- Layout em 3 colunas com "Propriedades da obra" e documentos recolhível.
- "Exportar Projeto Pronto" (relatório + Excel + JSON + ZIP).
