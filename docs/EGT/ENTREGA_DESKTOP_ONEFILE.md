# EGT.exe — entrega desktop concluída

## Resultado

A entrega inicial do EGT para Windows está concluída. O aplicativo é distribuído como um único executável:

- Nome: `EGT.exe`
- Empacotamento: PyInstaller One File.
- Persistência: SQLite local, fora do executável.
- Pasta de dados: `data`, ao lado do executável.
- Distribuição: anexar somente `EGT.exe` à página GitHub Releases; não incluir banco de dados de usuário.

Esta versão encerra a etapa de implementação desktop. A partir daqui, o projeto recebe somente atualizações de manutenção, correções, segurança, compatibilidade e melhorias pontuais.

## Testes já realizados

- [x] Executável empacotado inicia no Windows usado no desenvolvimento.
- [x] Janela principal abre e responde.
- [x] Aplicativo fecha normalmente.
- [x] Banco SQLite local apresenta integridade `ok`.
- [x] Persistência local foi testada após fechar e reabrir o aplicativo.
- [x] A distribuição foi preparada sem os dados locais do usuário.

## Validações complementares pendentes

- [ ] Executar uma cópia do `EGT.exe` em uma pasta totalmente vazia e confirmar que o próprio executável cria `data` e o banco.
- [ ] Executar em um Windows limpo, sem Python instalado.
- [ ] Validar atualização de uma instalação existente mantendo a pasta `data`.
- [ ] Concluir a varredura antivírus no computador de distribuição.

O código contém criação automática dos diretórios-pai antes da abertura dos bancos SQLite, mas isso ainda precisa ser confirmado no executável em uma pasta vazia. Não declarar esses testes como aprovados antes de executá-los.

## Distribuição no GitHub

O executável tem aproximadamente 109 MB. Ele ultrapassa o limite de 100 MiB para arquivos normais no GitHub. Portanto:

1. Criar uma Release na página [Releases do repositório](https://github.com/Lvc4br/ponte/releases).
2. Usar uma identificação de versão, por exemplo `EGT v1.0.0`.
3. Anexar somente `EGT.exe) como ativo da Release.
4. Publicar a Release e manter o link de download nesta documentação.

Não colocar `EGT.exe` no histórico normal do Git. Não publicar a pasta `data`, bancos SQLite reais, planilhas ou documentos de usuários.

## Como instalar

1. Baixar `EGT.exe` na Release.
2. Salvar em uma pasta com permissão de gravação.
3. Executar o programa.

A pasta `data` é separada do executável e deve ser criada pela aplicação na primeira execução. Se o Windows bloquear a gravação, mover o executável para uma pasta do usuário, como Documentos, e tentar novamente.

## Como atualizar sem perder dados

1. Fechar o EGT.
2. Copiar a pasta `data` para um local seguro.
3. Substituir apenas o `EGT.exe`.
4. Abrir o EGT e conferir os dados.

Nunca apagar a pasta `data` para instalar uma atualização.

## Limite desta entrega

Esta é a versão desktop local com SQLite. Ela não é a arquitetura central multiusuário com API FastAPI e PostgreSQL. O encerramento aqui se refere à entrega desktop atual; qualquer evolução futura será publicada como atualização ou etapa separada, sem apagar os dados locais.
