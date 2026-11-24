# Changelog

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
