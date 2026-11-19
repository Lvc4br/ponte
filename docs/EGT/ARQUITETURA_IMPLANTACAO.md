# PONTE EGT — arquitetura de implantação

## 1. Decisão arquitetural
Aplicação desktop para os usuários, com serviços centrais em rede corporativa. Os clientes desktop não se conectam diretamente ao PostgreSQL. Toda operação passa pela API, que aplica autenticação, autorização, validação, regras de negócio e auditoria.

## 2. Arquitetura lógica

Estações dos engenheiros (30+)
  PONTE Desktop — Python / PySide6
              |
              | HTTPS / rede corporativa
              v
  API PONTE — serviço central (FastAPI)
  Autenticação | autorização | regras | auditoria
              |
       +------+------+
       |             |
       v             v
  PostgreSQL     Storage corporativo
  dados          documentos e versões
       |
       v
  Backup, monitoramento e recuperação

## 3. Componentes recomendados

| Camada | Tecnologia inicial | Responsabilidade |
|---|---|---|
| Desktop | Python + PySide6 | Experiência do usuário |
| API | FastAPI | Contrato de comunicação e serviços |
| Banco | PostgreSQL | Fonte oficial dos dados |
| ORM | SQLAlchemy | Persistência e consultas |
| Migrações | Alembic | Evolução versionada |
| Validação | Pydantic | Contratos de entrada/saída |
| Identidade | Integração corporativa a definir | Autenticação |
| Arquivos | Storage corporativo | Binários e versões |
| Testes | Pytest | Unitários, integração e carga |
| Empacotamento | PyInstaller/instalador corporativo | Distribuição desktop |

Versões serão fixadas durante a implementação.

## 4. Implantação inicial
Hospedar API e PostgreSQL em infraestrutura gerenciada pela TI da EGT, em VM ou servidor corporativo. Separar os processos da API e do banco, mesmo que inicialmente usem a mesma infraestrutura de virtualização.

- Acesso somente pela rede corporativa ou VPN aprovada.
- HTTPS com certificado confiável.
- Firewall permitindo aos clientes acesso apenas à API.
- PostgreSQL sem exposição direta às estações.
- Credenciais fora do código-fonte e segredos em mecanismo aprovado pela TI.
- Ambientes separados de desenvolvimento, homologação e produção.
- Logs centralizados, sem senhas ou dados desnecessários.

CPU, memória, disco e conexões devem ser dimensionados por volume, padrão de consulta e teste de carga; não apenas pela quantidade de usuários.

## 5. Concorrência e desempenho
- Filtros, ordenação e paginação executados no PostgreSQL.
- Índices para chaves estrangeiras, identificadores e filtros frequentes.
- Pool de conexões na API.
- Transações para operações que alteram múltiplas entidades.
- Controle de concorrência otimista para evitar sobrescrita silenciosa.
- Timeouts, limites de requisição e erros padronizados.
- Importações demoradas em tarefas controladas com status consultável.

Validar 30+ usuários com consultas, gravações, importação e acesso a documentos simultâneos.

## 6. Segurança
Identidade individual; autorização no servidor; menor privilégio; permissões por projeto; auditoria de criação, edição, exclusão lógica, importação e mudanças de permissão; segredos protegidos; criptografia em trânsito; revisão de segurança antes da produção.

## 7. Documentos
O banco guarda metadados, identificadores, hash, tamanho, tipo, vínculo, revisão e estado. O conteúdo binário fica em armazenamento corporativo com permissões e backup. Não usar caminhos locais de usuário como referência oficial.

## 8. Backup e continuidade
Definir com TI RPO, RTO, frequência, retenção, cópia fora do servidor principal, criptografia, controle de acesso e testes periódicos de restauração. Backup só é considerado válido após restauração testada.

## 9. Observabilidade
Monitorar disponibilidade da API, latência, erros, consultas lentas, conexões, CPU, memória, disco, importações, falhas de autenticação e backups.

## 10. Decisões pendentes
Provedor de identidade; hospedagem; armazenamento; RPO/RTO; retenção documental; regras de acesso por contrato/projeto; distribuição e atualização do desktop.