Leia o repositório (começando por app/application.py) e faça, em uma branch
`correcoes-interface`, rodando `pytest` antes e depois:

1. Copie tools/checar_acentos.py e app/formatters.py deste pacote, rode
   `python tools/checar_acentos.py --corrigir` e corrija à mão o que sobrar.
   Garanta open(..., encoding="utf-8") em toda leitura de texto.
2. Use fmt_celula/fmt_numero/fmt_percentual na tabela (datas dd/mm/aaaa,
   sem "T00:00:00") e no painel de indicadores (pt-BR em todas as colunas).
3. Painel "Resumo estatístico": coluna direita ~340px, cabeçalhos Média/Mín/Máx
   sempre visíveis, só a 1ª coluna estica.
4. Um único botão primário (laranja) por tela; botões secundários
   (Desfazer, Refazer, Excluir linhas, Coluna calculada) em menu "Mais".
   Estilizar a aba "Planilha" para o tema escuro.
5. Layout em 3 colunas: filtros (~280px) | tabela | indicadores (~320px) com
   "Propriedades da obra selecionada" abaixo; documentos do projeto recolhível.
6. Novo botão "Exportar Projeto Pronto": modal com opções (gráficos, tabela
   completa/filtrada, documentos) gerando ZIP com relatório PDF/HTML, Excel,
   CSV, JSON do projeto e metadados (filtros ativos, data, versão).
Não altere a base legada de pontes nem commite data/*.sqlite3.
Abra um pull request descrevendo cada mudança.
