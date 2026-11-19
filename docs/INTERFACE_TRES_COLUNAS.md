# Especificação da interface em três colunas

## Objetivo

Reorganizar a janela principal sem substituir os serviços de persistência, importação/exportação, filtros, edição e catálogo documental.

## Regiões

1. **Cabeçalho:** marca, projeto, tabela, pesquisa e ações principais.
2. **Coluna esquerda (280 px):** filtros técnicos de tipo, largura, vão e comprimento.
3. **Coluna central (flexível):** planilha editável, barra de fórmula, ordenação, seleção e atalhos.
4. **Coluna direita (330 px):** quantidade filtrada, médias, medianas, mínimos, máximos e propriedades do registro selecionado.
5. **Painel inferior recolhível:** documentos vinculados, pré-visualização e ações de análise.

## Regras de interação

- A pesquisa global, filtros técnicos e filtros por coluna devem atualizar a planilha e os indicadores usando o mesmo conjunto de registros.
- A seleção de uma linha atualiza o painel de propriedades sem abrir outra janela.
- Campos ausentes e textos não numéricos não entram nas estatísticas; o total de valores válidos é mostrado.
- Ordenação, edição, copiar/colar, desfazer/refazer e edição em lote permanecem na grade.
- Ações destrutivas ficam no menu Ferramentas e continuam sujeitas às confirmações já existentes.
- O painel de documentos pode ser recolhido para ampliar a área de dados.

## Paleta

| Uso | Cor |
|---|---|
| Fundo principal | #151E28 |
| Painéis | #1D2936 |
| Superfícies e campos | #18232F |
| Cabeçalhos de tabela | #2B4053 |
| Bordas | #344657 |
| Texto principal | #E8EEF4 |
| Texto secundário | #A2B1C0 |
| Ação primária | #E69A43 |

## Limites desta entrega

O painel estatístico calcula média, mediana, mínimo e máximo para colunas tipadas como inteiro/decimal. Campos de intervalo armazenados como texto precisam de uma regra de normalização de domínio antes de serem incluídos como medidas. Os testes automatizados devem ser complementados com validação manual da interface em Windows e diferentes resoluções.
