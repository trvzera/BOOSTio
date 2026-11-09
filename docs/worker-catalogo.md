# Etapa 6 — processo de catálogo

`ProcessarCatalogoService` roda em um processo independente da API Flask, no mesmo repositório. O comando `catalogo-worker` usa o contexto Flask para os models e credenciais, mas não inicia servidor HTTP. Não há rota pública para dispará-lo.

Cada ciclo processa uma etapa limitada de um trabalho vencido: descoberta → classificação → enriquecimento → importação. Os trabalhos têm categoria, palavras-chave e limites próprios. O exemplo está em `backend/data/catalogo/plano-exemplo.json`; ele não representa todas as categorias do marketplace. O plano aceita até 20 trabalhos, intervalo mínimo de 5 minutos entre varreduras concluídas, até 200 requisições por ciclo e até 50 pendências por etapa. Use valores menores inicialmente.

## Concorrência, retomada e limites

A trava cobre o banco inteiro: advisory lock de sessão no MySQL e `flock` por arquivo SQLite. Não depende de TTL fixo; o encerramento do processo libera a trava. Um segundo worker retorna `ocupado` e não consulta a API. A posse da trava é conferida antes e depois das chamadas externas e antes da importação. Migrações e alterações administrativas de plano devem ocorrer com o worker parado.

`estado_catalogo` guarda fase, cursor de descoberta, cursor da fila, próxima execução, tentativas e resumo. A descoberta grava checkpoint de busca/produto/página somente após confirmar a página; inclusive um limite que corte a página ao meio pode ser retomado. O checkpoint contém até 20 identidades/fichas parciais de catálogo. Erros de persistência não avançam o cursor de anúncios. A etapa de importação encerra o snapshot anterior à rede e repete a busca de duplicatas sob bloqueio, evitando leituras antigas no REPEATABLE READ do MySQL.

Os checkpoints são confirmados entre etapas/lotes. Se o processo cair entre a gravação de uma pendência e o checkpoint, reexecuta o lote com deduplicação. Se cair depois de importar e antes de salvar o estado do worker, a pendência importada é ignorada na retomada. Não prometemos uma fotografia estável de toda a busca externa: anúncios podem entrar e sair; novas varreduras periódicas reiniciam a busca.

A janela de offset é limitada a 1000. `janela_limitada` informa encerramento dessa janela, sem alegar cobertura completa. As palavras-chave e filtros devem ser específicos para evitar concentrar todo o trabalho nessa janela. A descoberta precisa estar concluída dentro dessa janela antes de avançar à classificação; limites de páginas/anúncios fazem continuar no próximo ciclo.

HTTP 429 usa as tentativas/esperas existentes. As etapas compartilham um orçamento de chamadas por ciclo. Falhas persistentes agendam novas tentativas em 60 e 120 segundos; a partir da terceira, aguardam o período do trabalho. Falhas de uma tarefa não bloqueiam as outras. Não há repetição agressiva de OAuth incerto. Logs são JSON por ciclo, sem tokens ou cabeçalhos; evidências e resultados permanecem no banco.

SIGTERM/SIGINT solicitam parada entre chamadas. A etapa confirma o que já foi concluído; transações interrompidas são revertidas. O Compose concede 45 segundos de encerramento e o checkpoint permite recomeçar se o processo for encerrado antes. O worker não cria nem altera esquema na inicialização; esquema incompleto faz recusar a execução.

## Preparar e testar na VPS

Nada é iniciado automaticamente ao atualizar o Compose: o serviço pertence ao perfil opcional `catalogo`. Faça backup e prepare as tabelas antes de ativá-lo. Os comandos abaixo são instruções, não foram executados na VPS nesta implementação.

```bash
# Constrói a imagem; não inicia o worker.
docker compose --env-file .env.production --profile catalogo build catalogo-worker

# Revise o plano de migração antes de aplicar.
docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app catalogo-preparar

docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app catalogo-preparar --aplicar

docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app mercadolivre-identidades-preparar

docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app mercadolivre-ofertas-preparar
```

Esses comandos pressupõem que o banco e as tabelas anteriores de coleta/tokens já existem, como na instalação atual. Se a imagem `api` ainda estiver antiga, construa também `api` antes de usar seus comandos. A migração do catálogo acrescenta `estado_catalogo`, preservando peças e usuários. A preparação de identidades acrescenta GTIN opcional. Não substitua o banco.

Revise o plano de exemplo, ou defina `CATALOGO_PLANO` no arquivo de ambiente apontando para outro JSON local. O arquivo é montado somente para leitura. Não coloque credenciais no plano. Use as credenciais OAuth e a chave de criptografia da API, pelo mesmo `.env.production`; os tokens continuam no banco e são renovados pelo serviço existente.

Simular uma única etapa, sem salvar fila, importações ou checkpoints:

```bash
docker compose --env-file .env.production --profile catalogo run --rm --no-deps -T \
  catalogo-worker python -m flask --app app catalogo-worker \
  --plano /app/plano-catalogo.json --uma-vez
```

A simulação ainda consulta a API e pode renovar tokens. Ela não demonstra acesso se os endpoints responderem 403. Como não avança o estado, não permite modo contínuo sem `--aplicar`.

Para confirmar apenas uma etapa, acrescente `--aplicar`. Revise um lote pequeno antes da execução contínua:

```bash
docker compose --env-file .env.production --profile catalogo up -d catalogo-worker
docker compose --env-file .env.production logs -f --tail=100 catalogo-worker
```

O processo usa até 0,5 CPU e 256 MB, sem portas ou exposição no Traefik. Sondagem padrão: 60 segundos; cada trabalho respeita sua própria agenda. Para parar:

```bash
docker compose --env-file .env.production stop catalogo-worker
```

Por padrão, novas peças **não são criadas**. Para habilitar essa possibilidade depois da revisão prevista na etapa 8, defina `CATALOGO_PERMITIR_NOVOS=true` e recrie o worker. Mesmo habilitado, apenas fichas completas com identidade comprovada podem passar. A maioria das lacunas de fonte continuará para revisão. Ofertas de peças existentes podem ser importadas automaticamente após confirmação inequívoca.

## Alterar plano ou reiniciar busca

Mudar os parâmetros de um trabalho mantendo seu nome é recusado para não reutilizar um cursor incompatível. Pare o worker e use outro nome de trabalho, ou reinicie explicitamente o estado:

```bash
docker compose --env-file .env.production --profile catalogo run --rm --no-deps -T \
  catalogo-worker python -m flask --app app catalogo-worker-reiniciar \
  --plano /app/plano-catalogo.json --nome ram-kingston-ddr4
```

Esse comando redefine somente agenda/checkpoints do trabalho. Não apaga pendências, componentes, ofertas ou históricos. Cadastros já importados continuam deduplicados.

As etapas 7 (painel administrativo) e 8 (revisão do lote real e ativação controlada em produção) continuam pendentes.
