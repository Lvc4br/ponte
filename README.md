# EGT — Gerenciador de Estruturas

Aplicativo desktop Windows para organizar projetos, tabelas, registros técnicos e documentos. Esta branch contém a entrega desktop local do EGT.

<badge>Projeto concluído — manutenção e atualizações</badge>

## Situação da versão

A entrega inicial do aplicativo desktop está concluída. A partir desta versão, o projeto entra em manutenção: as próximas publicações serão atualizações, correções, ajustes de compatibilidade, segurança e melhorias pontuais.

- Aplicativo distribuído em um único arquivo: `EGT.exe`.
- Empacotamento: PyInstaller One File.
- Persistência local: SQLite.
- Os dados ficam fora do executável, na pasta `data`, criada pela aplicação quando necessário.
- O executável de distribuição não inclui banco de dados nem registros pessoais.
- Esta entrega é local e não representa ainda a arquitetura central multiusuário com API e PostgreSQL.

## Download

O executável deve ser publicado como ativo de uma versão na página [Releases](https://github.com/Lvc4br/ponte/releases). Por seu tamanho, o arquivo `EGT.exe` deve ser anexado à Release, e não versionado diretamente no histórico normal do Git.

## Instalação

1. Baixe `EGT.exe` na seção Releases.
2. Salve-o em uma pasta na qual seu usuário tenha permissão de gravação.
3. Execute o arquivo.
4. Na primeira execução, a aplicação deverá preparar a pasta `data` e o banco SQLite local.

## Atualizações e preservação dos dados

1. Feche o EGT.
2. Faça uma cópia de segurança da pasta `data`.
3. Substitua somente o `EGT.exe` pela versão nova.
4. Abra o aplicativo e confira os dados.

**Não apague nem substitua a pasta `data` durante uma atualização.** O executável e o banco de dados são itens separados.

## Verificações realizadas

- Inicialização do executável empacotado e abertura da janela principal.
- Fechamento normal do aplicativo.
- Verificação de integridade do banco SQLite local: `ok`.
- Teste local de persistência dos dados após reabrir o aplicativo.

Ainda não foi comprovada a execução em uma máquina Windows limpa, sem Python, nem o primeiro arranque do executável em uma pasta totalmente vazia. Esses pontos devem ser validados antes de tratar a distribuição como universalmente testada.

## Documentação

- [Entrega desktop e procedimento de atualização](docs/EGT/ENTREGA_DESKTOP_ONEFILE.md)
- [Visão geral da EGT](docs/EGT/README.md)
- [Arquitetura de implantação](docs/EGT/ARQUITETURA_IMPLANTACAO.md)

## Segurança

Não publique bancos SQLite de usuários, planilhas internas, documentos corporativos, credenciais ou dados pessoais. O executável atual não possui assinatura Authenticode; o Windows pode exibir avisos de reputação ao executá-lo.
