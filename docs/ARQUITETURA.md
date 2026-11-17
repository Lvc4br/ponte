# Arquitetura

- `database/ponte.sql.example`: modelo versionado do script SQL.
- `database/ponte.sql`: script local com os dados temporários; ignorado pelo Git.
- `data/ponte.db`: banco SQLite reconstruído a partir do script SQL; ignorado pelo Git.
- `app/core`: modelos, validação e correspondência de intervalos.
- `app/data/sql_loader.py`: execução controlada do script e reconstrução do SQLite.
- `app/data/repository.py`: acesso aos registros carregados.
- `app/services`: serviços de pesquisa.
- `app/ui`: interface desktop PySide6.
- `tests`: testes automatizados.

O script deve criar a tabela `obras`. A interface filtra tipo de obra, largura, vão e comprimento total. Para vãos, use `vao_min_m` e `vao_max_m`. Campos ausentes são preservados e não são tratados como zero. O aplicativo consulta referências históricas; não dimensiona estruturas.
