# Arquitetura

- app/core: modelos, validação e correspondência de intervalos.
- app/data: leitura e mapeamento de colunas Excel.
- app/services: pesquisa e exportação.
- app/ui: interface desktop PySide6.
- tests: testes automatizados.

A planilha padrão é a aba Base_limpa, com cabeçalho na segunda linha (índice 1). Os valores originais são preservados. Vãos textuais como 41,25 - 41,80 são comparados por sobreposição. Campos ausentes não eliminam automaticamente registros. O aplicativo consulta referências históricas; não dimensiona estruturas.
