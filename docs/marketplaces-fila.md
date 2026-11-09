# Fila durável de marketplaces — implementação em andamento

## Estado atual

A fila compartilhada está implementada e integrada ao Mercado Livre e à Shopee. O adaptador da Shopee
usa a API de Afiliados (`productOfferV2`) e está descrito em [shopee.md](shopee.md). Nenhuma chamada real
à Shopee foi feita: os testes usam respostas simuladas, porque as credenciais não estão neste checkout.
Nenhuma coleta externa, migração no banco do usuário ou implantação foi executada.
A nova fila não é iniciada ao importar a aplicação. Os comandos antigos permanecem.

## Organização

- `models/tarefa_marketplace.py`: tarefa durável e estado de limite por loja.
- `repositories/fila_marketplace_repository.py`: identidade única, reservas,
  finalização, reagendamento e reserva atômica de intervalo.
- `services/marketplace_service/controle_requisicoes_service.py`: intervalo
  compartilhado entre workers, classificação e pausa por marketplace.
- `services/marketplace_service/processar_fila_service.py`: processamento e
  recuperação de tarefas após encerramento inesperado.
- `services/marketplace_service/executores_service.py`: usa a atualização,
  associação e persistência atuais do Mercado Livre, uma peça por tarefa.
- `commands/marketplaces.py`: preparação, enfileiramento, worker, resumo e reativação.
- `migrations/fila_marketplaces.py`: adição de duas tabelas sem alterar as existentes.

Não há Redis/Celery novo. O controle usa MySQL/SQLite. A trava exclusiva por loja
reutiliza GET_LOCK no MySQL e flock no SQLite. O SQLite requer arquivo compartilhado
no mesmo host. Vários hosts devem usar o mesmo MySQL. A reserva de horário usa UPDATE
condicional; não existe transação de banco mantida aberta durante HTTP ou espera.

## Semântica das tarefas

A identificação da execução + tipo + parâmetros gera a chave idempotente. Repetir
um comando com os mesmos parâmetros e identificação não cria outra tarefa, inclusive
se a anterior concluiu. Para uma nova coleta de preços, usar outra identificação.
Tarefas concluídas não são repetidas. Após um crash, uma tarefa `executando` é
recuperada pelo próximo worker que adquirir a trava da loja. A importação existente
reconfere identidade e duplicatas na própria transação.

Isso oferece entrega ao menos uma vez: se o processo cair após gravar uma oferta,
mas antes de finalizar a tarefa, a próxima execução poderá consultar novamente.
A idempotência da persistência impede duplicar a oferta. Não se promete exatamente
uma requisição à API em caso de crash.

As lojas têm travas e pausas separadas. No worker atual, as tarefas são processadas
por turnos num processo; uma chamada em andamento pode ocupar o turno até seu timeout.
Pausas longas são persistidas e liberam o scheduler em vez de deixá-lo dormindo.

## Intervalos e erros

O intervalo do worker é de pelo menos 1 segundo entre requisições da mesma loja.
Pode aumentar com `MERCADO_LIVRE_INTERVALO_REQUISICOES` e, futuramente,
`SHOPEE_INTERVALO_REQUISICOES`. Valores inferiores a 1 são rejeitados.
A reserva é compartilhada entre workers que usam o mesmo banco.

429: pausa de pelo menos 60 segundos; respeita Retry-After em segundos ou data.
Limitações repetidas aumentam o backoff até uma hora, sem reduzir um Retry-After
maior. O contador de limitações volta a zero quando uma tarefa conclui sem 429,
então uma limitação isolada não mantém a loja pausada por uma hora. A tarefa permanece pendente. 500/502/503/504 e falhas temporárias de rede
reagendam com backoff progressivo, também limitado a uma hora. Não há limite que
apague uma tarefa temporariamente indisponível.

401/403: bloqueio somente da loja afetada, evitando repetição infinita. O Mercado
Livre mantém sua renovação de tokens existente. Se a renovação ficar inconclusiva,
não se repete cegamente um refresh token possivelmente rotacionado: a integração
aguarda reautorização e reativação administrativa.

400/404 e dados inválidos: a tarefa fica registrada como falhou. O resumo permite
acompanhar os estados. Exceções SQL interrompem o worker, mantendo a tarefa para
recuperação após reinicialização; um supervisor de processo deve reiniciá-lo.

O limitador durável é aplicado no contexto do novo worker. Comandos legados fora
desse contexto mantêm seu controle anterior; até completar a integração global,
não executar coletas legadas em paralelo com a nova fila usando a mesma credencial.
O worker antigo de descoberta continua usando seu checkpoint e não foi migrado
para a nova fila nesta parte. A integração completa dos dois fluxos é pendente.

## Uso local/VPS após revisão e backup

A partir de `backend/`, com o ambiente correto configurado:

```sh
python -m flask --app app marketplaces-fila-preparar
python -m flask --app app marketplaces-fila-preparar --aplicar
python -m flask --app app marketplaces-enfileirar-ofertas --loja mercado_livre --categoria ssd --execucao teste-ssd
# sem --categoria: todas as categorias (só peças aprovadas e com o mínimo técnico)
python -m flask --app app marketplaces-enfileirar-ofertas --loja mercado_livre --execucao teste-todas
python -m flask --app app marketplaces-enfileirar-ofertas --loja mercado_livre --categoria ssd --execucao teste-ssd --aplicar
python -m flask --app app marketplaces-worker --uma-vez
python -m flask --app app marketplaces-fila-resumo
```

O primeiro enfileiramento só conta. O segundo grava tarefas que **simulam a
importação**, sem gravar ofertas. Para tarefas que gravam ofertas, acrescentar
`--gravar-ofertas` ao enfileiramento. `--peca-id` permite restringir a uma peça.
Somente peças com requisitos mínimos são selecionadas.

Para execução contínua, usar `marketplaces-worker`, sob supervisão de processo.
Ainda não foi adicionado um serviço ao Compose: a Shopee e os limites oficiais
precisam ser confirmados antes da ativação conjunta. Para desbloquear após corrigir
uma autorização: `marketplaces-fila-reativar --loja mercado_livre`.

## Testes e pendências

Testes usam arquivos SQLite temporários, APIs simuladas e relógios controlados.
Cobrem migração repetível, persistência, tarefa duplicada, crash, intervalo atômico
concorrente, exclusão entre workers, lojas independentes, 429/Retry-After, backoff,
503, 400, 401, reativação e falhas de rede. O grupo fila + Mercado Livre passou com
227 testes. Nenhum teste real da API da Shopee foi executado.

O snapshot de esquema da refatoração exclui explicitamente as duas tabelas novas,
para continuar verificando que todas as tabelas anteriores permanecem iguais.
A migração aditiva é testada separadamente. Não houve atualização dos hashes dos
prompts nem da seed.

Pendências: credenciais Shopee e uma execução real limitada; limitação global dos comandos legados;
filas de descoberta/enriquecimento/importação do Mercado Livre; serviço do worker no Compose;
integração real em MySQL descartável.
