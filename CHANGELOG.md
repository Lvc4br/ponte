# Changelog

## Atualização de manutenção — nomenclatura técnica

- Adicionado catálogo explícito de equivalências para nomenclaturas de pontes estaiadas.
- Criada normalização de acentos, caixa, espaços e pontuação para comparação.
- Unificadas as regras de comparação de tipo na busca da base legada e nos filtros do espaço de dados.
- Preservado integralmente o valor original importado; a forma canônica é usada apenas para comparação.
- Incluído relatório de termos reconhecidos e rótulos ainda não mapeados, sem classificação automática de termos ambíguos.
- Incluídos testes para sinônimos, variações de escrita e prevenção de agrupamentos incorretos.
- Documentada a arquitetura em `docs/EGT/NOMENCLATURA_TECNICA.md`.

**Atenção:** o código-fonte atualizado ainda precisa passar pela suíte de testes e gerar um novo `EGT.exe`. O executável anteriormente distribuído não recebe esta melhoria automaticamente.

## EGT — entrega desktop inicial concluída

- Encerrada a implementação da entrega desktop Windows do EGT.
- Aplicativo empacotado em arquivo único `EGT.exe` (PyInstaller One File).
- Persistência local em SQLite, separada do executável.
- Testada a inicialização, abertura da janela, fechamento e persistência local no ambiente de desenvolvimento.
- Verificada a integridade do banco SQLite local.
- Definido o procedimento de atualização preservando a pasta `data`.
- Próximas publicações destinadas somente a correções, segurança, compatibilidade, estabilidade e melhorias pontuais.

### Validações complementares

Ainda precisam ser confirmados o primeiro arranque em pasta vazia, a execução em Windows sem Python e a atualização em uma instalação independente. Consulte [docs/EGT/ENTREGA_DESKTOP_ONEFILE.md](docs/EGT/ENTREGA_DESKTOP_ONEFILE.md).

### Distribuição

O binário `EGT.exe` deve ser anexado como ativo de uma Release do GitHub. Não versionar o executável de aproximadamente 109 MB nem bancos de dados de usuários no histórico comum do Git.
