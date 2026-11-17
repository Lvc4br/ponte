# Base SQL temporária

O aplicativo espera encontrar o arquivo local `database/ponte.sql`.

1. Copie `ponte.sql.example` para `ponte.sql`.
2. Edite `ponte.sql` e substitua o exemplo comentado pelos INSERTs dos dados autorizados.
3. Execute o aplicativo. A base SQLite local será reconstruída em `data/ponte.db` a cada inicialização a partir do script SQL.

O arquivo `ponte.sql` é ignorado pelo Git e não deve ser enviado ao repositório público. O arquivo `ponte.sql.example` contém somente a estrutura e um exemplo fictício comentado.

## Colunas

Use os nomes definidos no CREATE TABLE. Vãos podem ser informados em duas colunas numéricas (`vao_min_m` e `vao_max_m`). Preserve campos desconhecidos sem atribuir significados não confirmados.
