# Guia de execução local — PONTE v2 (Windows)

Este guia explica como baixar e testar uma cópia isolada da branch `rebuild/ponte-v2`.

## 1. O que será executado

**Importante:** neste estágio, `rebuild/ponte-v2` ainda contém a aplicação desktop legada usada como referência e módulos/documentação iniciais do rebuild. O domínio de pontes e o catálogo de indicadores ainda não estão conectados à interface nem a uma persistência própria. Portanto, executar `main.py` abre a aplicação legada disponível nessa branch; isso não significa que o novo PONTE central esteja pronto.

A arquitetura central (cliente desktop → API → PostgreSQL), autenticação, sincronização e concorrência multiusuário não devem ser consideradas implementadas apenas porque aparecem na documentação.

## 2. Preparação segura

1. Não sobrescreva sua pasta de trabalho atual.
2. Crie uma pasta separada, por exemplo: `C:\PONTE\rebuild-ponte-v2`.
3. Mantenha bancos SQLite, documentos e planilhas reais fora da cópia baixada.
4. Baixe o ZIP da branch pelo GitHub: abra a branch `rebuild/ponte-v2`, clique em **Code → Download ZIP** e extraia o conteúdo para a pasta criada.

Link da branch: https://github.com/Lvc4br/ponte/tree/rebuild/ponte-v2

## 3. Criar ambiente Python (PowerShell)

Abra o PowerShell dentro da pasta extraída, na qual aparecem `main.py` e `requirements.txt`, e execute:

```powershell
py -0p
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se Python 3.11 não estiver instalado, instale uma versão suportada (3.11 ou superior) e repita a criação do ambiente. Não reutilize a pasta `.venv` de outro projeto.

Se o PowerShell bloquear a ativação, não é necessário alterar a política do computador: use diretamente `.\.venv\Scripts\python.exe` nos comandos abaixo.

## 4. Validar antes de abrir

```powershell
.\.venv\Scripts\python.exe -m compileall -q app tests main.py
.\.venv\Scripts\python.exe -m pytest -q
```

Aguarde o término. Se houver falhas, copie o comando executado e a saída completa. Não considere a aplicação validada apenas porque a janela abriu.

## 5. Executar a interface disponível nesta branch

```powershell
.\.venv\Scripts\python.exe main.py
```

Use apenas dados fictícios para os primeiros testes. Não conecte bases de produção nem documentos confidenciais.

## 6. Testar isoladamente o domínio novo

Os testes atuais do domínio podem ser executados separadamente:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_bridge_domain.py tests/test_indicator_catalog.py
```

Eles validam regras básicas dos objetos de ponte/OAE e o catálogo provisório. Não validam interface, banco, importação, relatórios ou fórmulas de engenharia.

## 7. Gerar pacote Windows (opcional)

Depois de testes aprovados:

```powershell
build\build_windows.bat
```

O pacote fica em `dist\PONTE\`. O script atual gera distribuição em diretório (`--onedir`), não um único arquivo EXE. A geração local também não substitui os testes em uma máquina limpa.

## 8. Atualizar a cópia local sem Git

Para obter uma versão mais recente sem comandos Git:

1. Feche a aplicação.
2. Faça backup da pasta de teste e de qualquer banco local.
3. Baixe novamente o ZIP da branch `rebuild/ponte-v2`.
4. Extraia em uma nova pasta com data, por exemplo `C:\PONTE\rebuild-2026-11-23`.
5. Crie um novo ambiente virtual e instale as dependências.
6. Rode compileall e pytest antes de abrir a interface.
7. Compare e migre somente arquivos de dados que tenham formato e compatibilidade confirmados. Não copie `.venv`, `__pycache__`, `dist`, `build`, logs ou bancos antigos para dentro da nova versão.

## 9. Organização recomendada no computador

```text
C:\PONTE\
  repositorios\
    ponte-main-preservado\
    ponte-rebuild-v2\
  testes-locais\
    2026-11-23\
  backups\
  dados-ficticios\
  pacotes\
```

- `ponte-main-preservado`: cópia de consulta da linha principal; não desenvolver nela.
- `ponte-rebuild-v2`: cópia de trabalho obtida da branch de reconstrução.
- `testes-locais`: resultados, capturas e logs de validação.
- `backups`: cópias datadas dos dados, fora do repositório.
- `dados-ficticios`: planilhas e documentos sem dados corporativos reais.
- `pacotes`: builds gerados e identificados pela data/commit.

## 10. O que reportar após o teste

Envie:
- commit/ZIP baixado e data;
- versão do Python (`python --version`);
- resultado de `compileall`;
- resumo final do `pytest`;
- erro completo, se a janela não abrir;
- comportamento observado, sem anexar documentos internos ou banco real.

**Regra de segurança:** não mescle branches, não substitua a `main` e não use dados reais até haver integração, migração, backup/restauração e testes de aceitação aprovados.
