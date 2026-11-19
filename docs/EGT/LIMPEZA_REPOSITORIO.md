# PONTE EGT — política de limpeza do repositório

## Situação verificada
- Repositório: Lvc4br/ponte.
- Branch criada: rebuild/egt-foundation.
- Base: correcoes-interface.
- correcoes-interface estava 42 commits à frente de main no momento da criação.
- O README da main descreve o produto como gerenciador genérico local-first.
- O .gitignore já exclui ambientes virtuais, caches, arquivos compilados, alguns bancos e planilhas.

## Removíveis após inventário
Caches (__pycache__, .pytest_cache), arquivos .pyc/.pyo, ambientes virtuais, distribuições geradas, logs temporários, arquivos de editor e duplicatas comprovadas sem referências.

## Não remover automaticamente
Código, testes, migrações, documentação, workflows, configuração, scripts de build, fixtures autorizadas, histórico Git, bancos SQLite/SQL, planilhas, documentos, anexos e backups.

## Atenção à configuração existente
O .gitignore contém a regra build/, mas o README aponta para build/build_windows.bat. Antes de alterar essa regra, verificar se o script está versionado e se o pipeline depende dele. A regra global *.xlsx/*.xls pode ocultar fixtures legítimas; preferir excluir dados privados por diretório e permitir fixtures sintéticas/autorizadas.

## Procedimento obrigatório
1. Listar todos os caminhos versionados da branch.
2. Classificar fonte, teste, documentação, configuração, dado, backup e artefato.
3. Pesquisar referências em código, workflows e documentação.
4. Confirmar que o item não é necessário para build, teste, execução ou recuperação.
5. Criar commit isolado de limpeza, separado da documentação.
6. Executar testes e build após a limpeza.
7. Revisar o diff completo antes de PR.

## Limite desta alteração
Esta etapa adiciona documentação. Nenhum arquivo de aplicação, banco, documento de engenharia ou backup foi apagado. A limpeza física depende do inventário completo dos arquivos versionados e da análise de referências.