# Catálogo automatizado — etapa 1

Esta etapa prepara o armazenamento. Não descobre anúncios, não cadastra componentes automaticamente, não aprova fichas e não cria painel ou worker. Os coletores existentes continuam separados.

## Modelos

`Oferta` mantém os nomes e contratos existentes: `loja`, `produto_id_loja` (ID externo do anúncio), `tabela_peca` (tipo do componente), `peca_id`, `preco`, `url`, `url_afiliado`, `esgotado`, `ativa` e datas de consulta. Preço e disponibilidade desconhecidos continuam nulos; disponibilidade não é quantidade em estoque. O vínculo é polimórfico, pois não há uma tabela concreta única de peças. Por isso não existe uma FK genérica de `peca_id`; o importador deve validar categoria e existência da peça na transação.

A identidade única passa a ser **loja + produto_id_loja**. Vendedor é metadado. O mesmo anúncio não pode representar duas peças ou dois vendedores; mudança de vendedor no coletor exige revisão. Anúncios distintos podem apontar para a mesma peça. A migração recusa duplicatas antigas antes de alterar qualquer tabela, sem apagar ofertas ou históricos. O índice único antigo de três campos pode permanecer redundante em bancos migrados.

`ProdutoPendente` usa a tabela `produto_pendente`, seguindo o padrão singular do projeto. Guarda identidade externa, título, URL, vendedor opcional, categoria sugerida, resposta original JSON, evidências e candidatos JSON opcionais, motivo e datas reais de coleta/revisão. `oferta_id` é opcional e aponta para uma oferta existente; sua exclusão desfaz apenas essa referência. A identidade externa é única. Estados: `pendente`, `em_revisao`, `rejeitado`, `importado`. Não há API pública para essa tabela. As consultas e a paginação ficam no model.

## Publicação dos componentes

Todas as 17 categorias herdam `status_validacao`, `validacao_motivo` e `validado_em`:

- Novos registros começam `pendente`, fora do catálogo público, histórico público, candidatos de builds e inclusão de IDs em builds manuais.
- `em_revisao` e `rejeitado` também ficam fora.
- `aprovado` e `legado` permitem publicação.
- Registros anteriores à migração permanecem com status nulo, interpretado como legado, sem inventar auditoria ou data de aprovação. As seeds atuais usam explicitamente `legado`.

Não se deve atribuir nulo a novos registros: ele é reservado à compatibilidade histórica. No SQLite migrado um trigger transforma inserções com status nulo em pendentes; no MySQL o padrão passa a ser `pendente` depois da adição da coluna, preservando os nulos antigos. Processos que escrevem SQL diretamente devem respeitar essa regra. A aplicação continua podendo consultar pendências administrativamente; filtros públicos ficam nos models. Builds já salvas não são apagadas ou reescritas.

Esta etapa cria o bloqueio, não um aprovador automático. A definição de campos obrigatórios por categoria e as evidências necessárias para aprovação pertencem à etapa de enriquecimento.

Índices cobrem publicação/disponibilidade/preço, fabricante/modelo e part number em cada categoria, ofertas por componente/atividade/preço e fila de pendências por status/categoria/ID e loja/data.

## Migração explícita

Faça backup e pare os processos que gravam antes de aplicar. Use a imagem com o código novo, mas execute a migração antes de reiniciar a API nova sobre o banco antigo. Não use `banco-preparar` para atualizar um MySQL existente.

Simulação, sem alterar o esquema:

```bash
docker compose --env-file .env.production run --rm --no-deps -T \
  api python -m flask --app app catalogo-preparar
```

Aplicação, após revisar a simulação:

```bash
docker compose --env-file .env.production run --rm --no-deps -T \
  api python -m flask --app app catalogo-preparar --aplicar
```

O comando aceita SQLite e MySQL, inspeciona o esquema antes de começar e pode ser repetido: após completar, `alteracoes` fica vazio. Não recria tabelas existentes nem modifica usuários, builds, preços ou históricos. Tabelas de componentes ausentes continuam a cargo da inicialização existente. No SQLite, `banco-preparar` também inclui esta migração após as anteriores.

MySQL faz commit implícito de alterações de estrutura: não existe rollback global do plano. Em falha, mantenha escritores parados, confira o esquema e só retome/reaplique depois de corrigir a causa. Um esquema incompatível ou identidades duplicadas exige revisão; não remova registros apenas para fazer o comando passar.

## Verificação

Os testes exercitam preservação de dados, simulação, repetição, duplicatas, status de publicação, exclusão de pendências da seleção e identidade do anúncio independente do vendedor. O teste MySQL usa exclusivamente uma base descartável local chamada `boostio_ml_teste`, configurada em `BOOSTIO_MYSQL_TEST_URI`. Nunca aponte os testes para a VPS.
