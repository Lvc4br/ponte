# Status do projeto — EGT

**Status:** entrega desktop inicial concluída; projeto em manutenção e atualizações.  
**Branch:** `release/desktop-onefile`  
**Aplicativo:** `EGT.exe`  
**Distribuição:** executável único Windows (PyInstaller One File).  
**Persistência:** SQLite local, separado do executável.

## Atualização de manutenção — nomenclatura técnica

- [x] Criado catálogo explícito de aliases para Ponte estaiada.
- [x] Normalização de acentos, caixa, pontuação e espaços.
- [x] Regra de comparação compartilhada entre busca legada e filtros técnicos do espaço de dados.
- [x] Preservação dos valores originais importados.
- [x] Relatório programático de termos reconhecidos e não mapeados.
- [x] Testes automatizados adicionados ao repositório.
- [ ] Executar suíte completa no GitHub Actions.
- [ ] Gerar e validar novo `EGT.exe` para Windows.
- [ ] Publicar o novo executável como ativo de uma Release.

Detalhes: [Nomenclatura técnica](EGT/NOMENCLATURA_TECNICA.md).

## Entrega desktop inicial

- [x] Aplicativo desktop empacotado em executável único.
- [x] Inicialização local do executável e abertura da janela principal.
- [x] Fechamento normal do aplicativo.
- [x] Banco SQLite local verificado com integridade `ok`.
- [x] Persistência local de registros testada após reabrir o aplicativo.
- [x] Distribuição planejada sem banco de dados ou registros pessoais junto ao executável.
- [x] Orientações de preservação da pasta `data` durante atualizações.

## Validações de distribuição ainda pendentes

- [ ] Primeiro arranque em pasta vazia, confirmando a criação automática de `data`.
- [ ] Execução em Windows limpo, sem Python instalado.
- [ ] Teste de atualização sobre uma instalação independente preservando o banco.
- [ ] Varredura do executável pelo antivírus do ambiente de distribuição.

## Política de manutenção

O projeto permanece concluído como entrega inicial. Novas publicações devem ser restritas a correções, segurança, compatibilidade, estabilidade e melhorias pontuais validadas.

## Dados e atualização

O `EGT.exe` não contém os dados do usuário. O banco SQLite fica na pasta `data`, ao lado do executável. A pasta deve ser preservada entre versões.

1. Fechar o aplicativo.
2. Fazer backup da pasta `data`.
3. Substituir apenas o `EGT.exe`.
4. Abrir o aplicativo e verificar os registros.

Nunca publique a pasta `data` de uma instalação real: ela pode conter dados privados.

## Distribuição

O executável deve ser anexado à página [GitHub Releases](https://github.com/Lvc4br/ponte/releases), como ativo de uma versão. Não adicionar o arquivo de aproximadamente 109 MB ao histórico comum do Git.
