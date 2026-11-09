# Publicação de 9 de novembro de 2026

## Situação

**Publicação em produção pendente.** O PR [#89](https://github.com/trvzera/BOOSTio/pull/89)
foi incorporado à `main`, mas preparar a imagem não atualiza os contêineres em execução.

## Executado e observado na VPS

- `git fetch origin`: `origin/main` avançou para `95c8cfb`, merge do PR #89.
- A cópia isolada `/opt/BOOSTio-rotina-20261109` estava sem alterações e foi
  atualizada para esse commit, com HEAD destacado.
- A construção da imagem `boostio-catalogo:20261109` terminou com sucesso,
  usando `Dockerfile.api` dessa cópia.
- O checkout de produção `/opt/BOOSTio` foi preservado. Na inspeção anterior,
  estava em `62258e4`, com alterações locais em páginas HTML e arquivos não
  rastreados. Essas alterações precisam ser revisadas e preservadas ao atualizar.
- O preflight do MySQL identificou colunas de validação do catálogo e outras
  tabelas ainda ausentes. A migração de benchmarks recusou avançar antes delas.
- O backup terminou em `/root/boostio-backups/boostio-20261109T130922Z.sql.gz`.
  O script verifica a integridade gzip antes de publicar o arquivo.
- A primeira rotina parou depois do backup, sem confirmar as migrações. API e
  frontend foram reiniciados, e os endereços públicos voltaram a responder HTTP 200.
- O responsável confirmou `boostio-precos.timer` ativo. Isso comprova o
  agendamento antigo, não uma nova coleta nem o funcionamento do worker.
- `marketplaces-fila-preparar --aplicar` criou `tarefa_marketplace` e
  `limite_marketplace`. A repetição retornou `tabelas: []`, e o resumo retornou
  `[]`: fila preparada, ainda sem tarefas.

O console web perdeu repetidamente o foco de digitação e deixou de confirmar
novos comandos, mesmo após abrir outra sessão e receber foco manualmente.
A conexão de automação do navegador também informou indisponibilidade.
Não foi usado SSH, conforme a preferência do responsável pelo projeto.

## Validação executada

Na cópia local `69d91c8`, correspondente ao head do PR #89:

- Frontend: `node --test frontend/tests/*.test.mjs` — **776 testes aprovados**.
- Migrações e fila: aprovação em lote, fila de marketplaces, catálogo técnico,
  ofertas do Mercado Livre e migração MySQL de benchmarks — **35 aprovados**.
- Serviços de benchmark — **163 aprovados**.

As verificações Python usaram um ambiente temporário. Os testes automatizados
não comprovam a migração do MySQL de produção nem a disponibilidade dos provedores
externos. A consulta pública `GET https://api.boostio.com.br/health` respondeu
`{"status":"ok"}`; ela verifica o serviço que já estava publicado.

## Ainda pendente na VPS

- Aplicação das demais migrações, repetição dos preflights e conferência dos dados preservados.
- Atualização do checkout de produção, reconstrução/publicação de API e frontend.
- Homologação dos fluxos com a versão publicada.
- Rotina de aprovação da amostra, enfileiramento de ofertas, worker e sugestões de IA.

Não foram apagados volumes, restaurados bancos, publicadas novas imagens de
API/frontend nem executadas sugestões de IA na VPS nesta preparação.

## Correção da entrada do backup

O `docker compose exec -T` do backup herdava a entrada padrão. Quando chamado
de uma rotina lida pelo stdin, podia consumir os comandos seguintes. O problema
foi reproduzido localmente com um executável Docker simulado; a correção redireciona
a entrada para `/dev/null`. Os dois testes verificam que o comando posterior é
executado, tanto no sucesso quanto na falha, e que uma falha não publica o dump.

Essa correção no repositório ainda precisa ser publicada na VPS. Até lá, ao
chamar o backup existente em um bloco, redirecionar explicitamente a entrada:

```bash
BOOSTIO_BACKUP_DIR=/root/boostio-backups bash /opt/BOOSTio/deploy/backup_mysql.sh </dev/null
```

## Retomada

Primeiro, restabelecer uma sessão do console com entrada e saída confiáveis.
Conferir novamente o estado do repositório, dos contêineres e de qualquer tarefa
em execução. O comando abaixo repete o **preflight, sem aplicar alterações**, e usa a
imagem já construída, com a configuração de produção existente no servidor:

```bash
docker run --rm --network boostio_backend --env-file /opt/BOOSTio/.env.production -e APP_ENV=producao -w /app/backend boostio-catalogo:20261109 python -m flask --app app banco-atualizar-mysql
```

Esse comando simula a migração de benchmarks; não cobre automaticamente todas
as migrações de catálogo e marketplaces. Se indicar outras tabelas ou colunas
ausentes, revisar as migrações específicas antes de aplicar qualquer alteração.

Depois do diagnóstico, fazer o backup privado e testar sua integridade. Parar
os processos que escrevem durante as migrações que exigirem manutenção. Seguir
as orientações de [produção](configuracao-producao.md), conferir
[`deploy/atualizar_banco_mysql.sh`](../deploy/atualizar_banco_mysql.sh) e preservar
as alterações locais antes de atualizar o checkout de produção. Não executar
`banco-preparar` em um MySQL existente nem remover volumes para corrigir esquema.
