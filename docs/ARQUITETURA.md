# Arquitetura

- `database/ponte.sql.example`: modelo versionado do script SQL.
- `database/ponte.sql`: script local com os dados temporários; ignorado pelo Git.
- `data/ponte.db`: banco SQLite reconstruído a partir do script SQL; ignorado pelo Git.
- `app/core`: modelos, validação e correspondência de intervalos.
- `app/data/sql_loader.py`: execução controlada do script e reconstrução do SQLite.
- `app/data/repository.py`: acesso à base ativa e operações de inclusão/exclusão.\n- `app/data/dataset_store.py`: persistência local dos registros e backups, independente do SQL original.\n- `app/data/excel_importer.py`: leitura de planilhas `.xlsx`, preservando cabeçalhos e valores de origem.
- `app/services`: serviços de pesquisa.
- `app/ui`: interface desktop PySide6.
- `tests`: testes automatizados.

O script deve criar a tabela `obras`. A interface filtra tipo de obra, largura, vão e comprimento total. Para vãos, use `vao_min_m` e `vao_max_m`. Campos ausentes são preservados e não são tratados como zero. O SQL inicial é copiado para `data/registros.sqlite3` somente quando a base gerenciada ainda está vazia. Inclusões do Excel e exclusões são persistidas nesse arquivo separado; o SQL original não é alterado. O aplicativo consulta referências; não dimensiona estruturas.
