# Entrega desktop — PONTE em arquivo único

## Objetivo desta branch

Preparar uma entrega desktop Windows que possa ser distribuída como um único arquivo executável, sem exigir Python ou uma pasta de bibliotecas ao usuário final.

- Branch: release/desktop-onefile
- Base: rebuild/egt-foundation
- Formato esperado: PONTE.exe (PyInstaller --onefile)
- Entrada da aplicação legada atual: main.py
- Persistência desta primeira entrega: SQLite local.
- Arquitetura central futura: desktop → API FastAPI → PostgreSQL.

## Limite importante

Esta branch prepara o processo de build e validação do executável a partir da aplicação legada existente. Ela **não** transforma automaticamente o legado no rebuild central multiusuário. O SQLite local não deve ser colocado em compartilhamento de rede para 30+ usuários. A integração com API/PostgreSQL continua sendo uma etapa de desenvolvimento separada.

## Indicadores técnicos obrigatórios

Os indicadores abaixo são requisitos permanentes do PONTE e não podem ser removidos nas próximas etapas:

| Indicador | Unidade solicitada | Situação |
|---|---|---|
| Paf | kg/m² | Fórmula e base aguardam validação da engenharia |
| Pap | kg/m² | Fórmula e base aguardam validação da engenharia |
| Ecm | m³/² (notação recebida) | Confirmar unidade antes de fixar fórmula |
| Af | m²/m² | Fórmula e base aguardam validação da engenharia |
| Aço total indicativo | kg/m² e kg/m³ | Fórmula e bases aguardam validação da engenharia |

Não inventar definições, numeradores, denominadores ou valores. Indicador sem dados suficientes deve aparecer como pendente/indisponível, nunca como zero. O catálogo, o modelo de dados, a interface, os testes e a documentação devem preservar esses indicadores ao longo do rebuild.

## Processo de build

1. Windows runner configura Python 3.13.
2. Instala requirements.txt.
3. Executa compileall e pytest.
4. Executa build/build_windows.bat, que chama PyInstaller com --onefile.
5. Confere que dist contém somente PONTE.exe.
6. Publica o artefato PONTE-Windows-OneFile.

O artefato de CI é um candidato de validação. Antes de declarar a versão pronta para uso corporativo, testar em Windows limpo sem Python: inicialização, cadastro, persistência após reabrir, backup/restauração, atualização e permissões sem administrador.

## Dados e atualizações

O executável é único, mas os dados de trabalho são persistidos fora do binário, em SQLite local. A aplicação atual usa diretório ao lado do executável; por isso o usuário precisa salvar PONTE.exe em uma pasta com permissão de gravação. Para atualizar, fechar o aplicativo e preservar a pasta data. Nunca sobrescrever nem apagar dados existentes sem backup e confirmação.

## Critérios de aceite desta entrega

- [ ] Workflow Windows verde.
- [ ] Somente PONTE.exe no artefato.
- [ ] Inicialização em máquina limpa sem Python.
- [ ] Cadastro/edição/consulta persistem após fechar e abrir.
- [ ] Backup e restauração validados.
- [ ] Atualização não perde dados.
- [ ] Sem privilégios administrativos.
- [ ] Versão identificada e limitações documentadas.

## Próximo passo após a validação

Evoluir a aplicação para consumir a API central, com autenticação, autorização, auditoria e PostgreSQL. A aplicação desktop não deverá conectar diretamente ao PostgreSQL. Validar desempenho para 30+ usuários com teste de carga representativo.
