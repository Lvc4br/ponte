# Status do projeto — EGT

**Status:** entrega desktop inicial concluída; projeto em manutenção e atualizações.  
**Branch:** `release/desktop-onefile`  
**Aplicativo:** `EGT.exe`  
**Distribuição:** executável único Windows (PyInstaller One File).  
**Persistência:** SQLite local, separado do executável.

## Entrega concluída

- [x] Aplicativo desktop empacotado em executável único.
- [x] Inicialização local do executável e abertura da janela principal.
- [x] Fechamento normal do aplicativo.
- [x] Banco SQLite local verificado com integridade `ok`.
- [x] Persistência local de registros testada após reabrir o aplicativo.
- [x] Distribuição planejada sem banco de dados ou registros pessoais junto ao executável.
- [x] Orientações de preservação da pasta `data` durante atualizações.

## Validações ainda não realizadas

- [ ] Primeiro arranque em pasta vazia, confirmando a criação automática de `data` pelo executável.
- [ ] Execução em Windows limpo, sem Python instalado.
- [ ] Teste de atualização sobre uma instalação de usuário preservando o banco.
- [ ] Varredura do executável pelo antivírus do ambiente de distribuição.

Esses itens são validações complementares de distribuição; não alteram o encerramento da implementação desta entrega desktop.

## Política daqui em diante

O projeto está encerrado como entrega inicial. Não há novas funcionalidades estruturais planejadas para esta etapa. Serão publicadas somente atualizações necessárias, como:

- correções de erros;
- ajustes de compatibilidade com Windows;
- correções de segurança;
- melhorias pontuais de usabilidade e estabilidade.

## Dados e atualização

O `EGT.exe` não contém os dados do usuário. O banco SQLite fica na pasta `data`, ao lado do executável. A pasta deve ser preservada entre versões.

Procedimento recomendado:

1. Fechar o aplicativo.
2. Fazer backup da pasta `data`.
3. Substituir apenas o `EGT.exe`.
4. Abrir o aplicativo e verificar os registros.

Nunca publique a pasta `data` de uma instalação real: ela pode conter dados privados.

## Distribuição

O executável deve ser anexado à página [GitHub Releases](https://github.com/Lvc4br/ponte/releases), como ativo binário de uma versão. Não adicionar o arquivo de aproximadamente 109 MB ao histórico comum do Git, que possui limite de tamanho por arquivo.
