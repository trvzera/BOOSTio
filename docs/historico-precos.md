# Histórico na atualização de preços

`AtualizarPrecosService` continua orquestrando a coleta. A reserva e os limites
existentes de `ConsultaPreco` permanecem. Nenhuma coleta é disparada ao importar
a aplicação e não há nova rota pública para gravar preços.

## Fluxo

1. Verificar se a tabela de histórico está preparada, antes de consultar a loja.
2. Selecionar e reservar a consulta pelo mecanismo existente.
3. Buscar e validar a cotação, recarregando a peça para conferir seu link.
4. `HistoricoPreco.registrar_observacao` valida e adiciona o registro à sessão,
   sem commit: preço decimal em BRL, disponibilidade, data UTC, loja, anúncio,
   URL e vínculo com a tentativa e a peça.
5. `Peca.aplicar_cotacao` compara valores em centavos. Só altera `preco` e
   `preco_atualizado_em` quando o preço muda. Estoque é comparado separadamente:
   `esgotado` muda mesmo quando o preço permanece igual.
6. `ConsultaPreco.confirmar` confirma histórico, peça e status da tentativa na
   mesma transação. Falha no commit reverte os três; a reserva feita antes da
   rede permanece registrada, conforme o comportamento anterior da coleta.

As consultas ao banco e as mutações persistentes ficam nos models. Os services
validam/orquestram por meio desses métodos. O histórico não chama `salvar()` de
forma independente, porque isso separaria o commit da atualização da peça.

## Regras

- Toda coleta bem-sucedida registra uma observação, mesmo se preço/estoque forem
  iguais. Nesse caso, nenhuma atualização é enviada à tabela da peça.
- Cotações iguais em dias diferentes são observações distintas. A mesma consulta
  não gera duas linhas, protegida pelo vínculo único `consulta_id`.
- Se preço mudar, sua data na peça recebe o instante da cotação. Se só o estoque
  mudar, a data do preço permanece. O instante de cada coleta está no histórico.
- Se a primeira cotação real for igual a um valor já cadastrado, a data do preço
  na peça também não muda; a confirmação dessa observação fica no histórico.
- Produto esgotado sem preço registra `preco = NULL`, nunca zero, e mantém o
  último preço/data na peça. O estoque continua atualizado.
- Preço inválido ou falha de rede não cria observação nem modifica a peça; a
  tentativa recebe seu status de falha existente.
- Se o anúncio mudar durante a requisição, a cotação é ignorada.
- Não há reconstrução de preços antigos: as tentativas anteriores não guardavam
  esses valores. Não existe tela ou endpoint de consulta nesta etapa.

## Resumo administrativo

O comando existente `precos-atualizar` retorna também:

| Campo | Significado |
|---|---|
| `historicos` | Observações confirmadas no banco |
| `precos_alterados` | Peças com preço diferente |
| `estoques_alterados` | Peças com disponibilidade diferente |
| `atualizadas` | Peças com alteração de preço ou de estoque |
| `inalteradas` | Coletas válidas que gravaram histórico sem alterar a peça |
| `consultas`, `falhas`, `ignoradas` | Mantêm o acompanhamento anterior |

Uma peça com mudança de preço e estoque conta uma vez em `atualizadas`.

## Preparação do banco

Em bancos novos, `db.create_all()` inclui o model. Em SQLite existente,
`banco-preparar` já cria tabelas ausentes com seu backup habitual. Para preparar
apenas o histórico, inclusive em **MySQL existente**, há a migração explícita:

```bash
# Na VPS, após disponibilizar o código e construir a imagem nova:
export BOOSTIO_BACKUP_DIR="$HOME/backups/boostio"
bash deploy/backup_mysql.sh

docker compose --env-file .env.production run --rm --no-deps \
  api python -m flask --app app historico-precos-preparar
```

O comando cria somente `historico_preco`, sem recriar usuários/peças. Recusa se a
tabela de tentativas não existir ou se encontrar colunas incompatíveis em uma
tabela de histórico existente. Repetir o comando com a tabela pronta não apaga
registros. O comando de histórico não faz backup automaticamente.

Depois use o agendamento ou comando de preços já existente. Sem a tabela, a coleta
interrompe antes da rede com orientação para executar a preparação. Não foram
executadas migrações nem coletas reais no banco local ou na VPS nesta etapa.

## Verificações

Testes de integração usam SQLite temporário e respostas simuladas da loja.
Cobrem histórico em preço igual, ausência de UPDATE da peça, mudança de preço,
estoque independente, indisponibilidade, dias distintos/reexecução, centavos,
entrada inválida, falha de rede, link trocado, rollback e preparação repetível.
A validação em um MySQL real continua sendo uma etapa de implantação.

## Consulta pelo frontend

A página `peca.html` das builds da conta carrega o gráfico pela rota autenticada:

```http
GET /build/catalogo/<categoria>/<peca_id>/historico-precos
```

`categoria` deve ser uma tabela de peça conhecida; o ID deve ser positivo. A rota
usa a mesma autenticação do catálogo da conta e não aceita parâmetros adicionais.
Retorna `peca_id` (ex.: `placa_video:12`), `loja`, `produto_id_loja` quando houver
anúncio válido, `historico_precos`, `limite` e `tem_mais`. Cada observação contém
`data` ISO UTC com milissegundos, `preco` numérico ou null, `esgotado`, `loja` e
`produto_id_loja`. Não expõe tentativas, erros internos ou credenciais.

O model consulta apenas a peça, loja KaBuM e anúncio atualmente vinculado à peça.
Trocas de anúncio não misturam séries antigas no gráfico. Registros anteriores
continuam no banco. A consulta retorna os últimos 1.000 registros, ordenados do
mais antigo ao mais recente, com desempate por ID; `tem_mais` indica recorte.
O frontend sinaliza esse limite e mantém filtros locais de 30/90 dias e registros
carregados. Datas sem observação não são preenchidas. Cotações esgotadas ficam no
contrato para rastreabilidade, mas não entram na curva de preços disponíveis.

Peça existente sem histórico retorna lista vazia; peça inexistente, 404;
identificação inválida, 400; banco/tabela indisponível, 503. As respostas de sucesso
usam `Cache-Control: no-store`. A página mostra carregamento e permite tentar
novamente após falha, sem converter erro em histórico vazio.

O modo demonstrativo e o exemplo do laboratório não consultam IDs do banco. O
Mercado Livre ainda não grava no histórico e não é misturado à curva da KaBuM.
Esta conexão não exige nova migration; a tabela existente deve estar preparada
com `historico-precos-preparar` nos ambientes que ainda não a possuem.
