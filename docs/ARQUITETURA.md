# Arquitetura

## Componentes

- database/ponte.sql.example: modelo de script SQL, sem dados corporativos.
- database/ponte.sql: fonte SQL local, ignorada pelo Git.
- data/ponte.db: cópia SQLite intermediária produzida ao executar a fonte SQL.
- data/registros.sqlite3: base local gerenciada pelo aplicativo, com inclusões e exclusões persistentes.
- app/core: modelos, validação, correspondência de intervalos e estatísticas.
- app/data/sql_loader.py: valida e executa o SQL local, produzindo registros e a cópia SQLite intermediária.
- app/data/excel_importer.py: lê planilhas .xlsx, preservando os cabeçalhos e valores encontrados.
- app/data/dataset_store.py: armazena registros em SQLite local e cria backup.
- app/data/repository.py: coordena a carga inicial, inclusão e exclusão na base ativa.
- app/services: serviços de pesquisa.
- app/ui: interface desktop PySide6.
- tests: testes automatizados.

## Fluxo de dados

1. Na primeira inicialização, o aplicativo valida e executa o SQL local.
2. Se a base gerenciada ainda estiver vazia, copia os registros SQL para data/registros.sqlite3.
3. A pesquisa, a importação Excel e a exclusão trabalham sobre a base gerenciada.
4. A importação Excel adiciona registros; não substitui a base e não deduplica automaticamente.
5. A exclusão cria backup antes de remover os IDs selecionados.
6. A fonte SQL permanece intacta.

Alterações posteriores no SQL não são mescladas automaticamente com uma base gerenciada já preenchida. O usuário deve preservar backups antes de qualquer intervenção manual.

## Limites

A camada Excel atual aceita apenas .xlsx e não possui mapeamento manual de colunas. O sistema ainda não armazena arquivos PDF/Word ou anexos, nem oferece versionamento documental, aprovação, permissões por usuário ou trilha de auditoria.

O aplicativo organiza e consulta registros técnicos; não executa dimensionamento ou validação estrutural.
