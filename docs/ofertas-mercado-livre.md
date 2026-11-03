# Descoberta e atualização de ofertas do Mercado Livre

O comando administrativo percorre peças existentes, procura produtos de catálogo,
valida a identidade e atualiza ofertas de vendedores. Não cria componentes, não
altera preço/estoque da peça da KaBuM e não gera links de afiliado. A integração
OAuth deve estar configurada conforme [mercado-livre.md](mercado-livre.md).

## Preparação

Após backup e reconstrução da imagem na VPS:

```sh
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app mercadolivre-ofertas-preparar
```

A migration cria `oferta`, `vinculo_mercado_livre` e `historico_oferta` se ausentes,
sem alterar tabelas existentes. Recusa nomes de colunas incompatíveis antes de
criar tabelas. Requer tabelas de controle de coleta já preparadas. DDL MySQL não
é uma transação atômica; a criação é repetível, mas teste numa cópia antes da VPS.

## Simulação e aplicação

Simula por padrão, com até cinco ofertas novas de vendedores distintos:

```sh
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app mercadolivre-ofertas-atualizar \
  --categoria processador --limite-pecas 20 --max-requisicoes 100
```

Adicione `--aplicar` para gravar os resultados. A simulação não grava vínculos,
ofertas ou histórico; a obtenção de token pode renovar as credenciais OAuth.
`--peca-id 12` restringe a uma peça e exige categoria. Para percorrer lotes de uma
categoria use `--depois-id ID` (exclusivo) com `--limite-pecas`. O resumo informa
`ultima_peca_concluida`. Em interrupção por cota, a peça que falhou deve ser
retentada: não avance o cursor até o ID dela. Falhas intermediárias devem ser
revisadas individualmente antes de avançar, pois o último sucesso não comprova
que todos os IDs anteriores foram processados.

Limites configuráveis:

- `--ofertas-por-peca`: padrão 5, entre 1 e 20.
- `--limite-pecas`: padrão 20, máximo 5.000 por execução.
- `--max-requisicoes`: padrão 100 tentativas GET, incluindo retries.
- `--intervalo`: padrão 1 segundo entre GETs, mínimo 0,1 segundo.

## Associação segura

Um vínculo já salvo é reutilizado apenas enquanto a identificação local e a ficha
remota do catálogo não mudarem. Sem vínculo, a busca usa MPN, se disponível, ou
fabricante/modelo. Códigos internos `SEED-*`, `DEMO-*` e `BOOSTIO-*` não são MPNs.

Somente MPN e fabricante explícitos e equivalentes nos atributos podem provar uma
associação automática. Não usa fuzzy matching, benchmark ou semelhança de nomes.
Preserva pontuação, sufixos e números no MPN, normalizando caixa, marcas e espaços.
A busca precisa retornar todos os seus candidatos (até 20) e apenas uma identidade
comprovada. Busca incompleta, mais de uma correspondência e ausência de evidência
vão para revisão; os nomes dos primeiros candidatos aparecem no resumo.

CPU e GPU rejeitam kits, combos, upgrades e notebooks nos vínculos automáticos.
CPU exige domínio de processadores. MPN terminado em BOX não é ligado a nome OEM
ou tray. Isso não certifica todos os detalhes do hardware: a precisão depende dos
códigos cadastrados e da qualidade dos atributos do Mercado Livre. Peças sem MPN
real exigem revisão; não há promessa de cobertura automática do catálogo atual.

Depois de conferir variante, código e especificações, pode registrar um vínculo
manual com o ID exato de catálogo:

```sh
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app mercadolivre-vincular \
  --categoria processador --peca-id 12 --catalogo-id MLB_ID_REVISADO --revisado
```

Troque o exemplo pelo ID real, composto por MLB e números. O comando consulta a
ficha e exige a flag de revisão; não comprova sozinho a equivalência. Não permite
substituir vínculo existente nem associar o mesmo catálogo a duas peças. Depois,
execute novamente a simulação/atualização. Mudança de ficha exige nova revisão;
não há substituição silenciosa do vínculo.

## Seleção, histórico e transações

O coletor percorre todas as páginas permitidas do catálogo (até 1.000 anúncios),
filtra condição `new`, ordena por preço e desempata por vendedor/anúncio. Escolhe
até o limite, com apenas uma oferta por vendedor. Isso não inclui frete, reputação,
Pix ou cupons. O menor preço informado não garante menor custo final ou melhor
vendedor. Limite de ofertas salvas não limita a resposta de cada página da API.

Ofertas são únicas por loja/anúncio/vendedor. Reexecuções atualizam a mesma linha,
preservando `url_afiliado`. `esgotado` permanece NULL porque o endpoint não prova
estoque. `ativa` indica seleção local, não disponibilidade confirmada.

Uma transação por peça confirma vínculo, ofertas e histórico juntos, usando o
controle de coleta do banco para serializar escritas. Falhas não confirmam um lote
parcial. Não há transação aberta durante buscas HTTP. Simulação recarrega a peça
para não aplicar uma identificação que mudou durante a rede.

`HistoricoOferta` preserva observações por anúncio. Registra preço alterado ou uma
nova observação no dia seguinte (UTC); repetir preço e disponibilidade desconhecida
no mesmo dia não duplica histórico. Se a API mudar o preço dentro do dia, registra
a mudança. Ofertas que saem da seleção ficam inativas, sem apagar seu histórico
nem marcá-las como esgotadas. Resultado vazio preserva os registros anteriores.
Este histórico não entra no gráfico atual da KaBuM e não expõe novas ofertas no
frontend automaticamente; são integrações separadas.

## Cotas e falhas

A documentação oficial não oferece uma cota universal garantida para esta busca.
O controle é principalmente por Client ID e endpoint. O ritmo padrão é uma escolha
conservadora da aplicação, não uma autorização de consumo da API.

O controle deste job é por processo, não global entre várias instâncias. Execute
um único job por vez por aplicação, respeitando o consumo dos outros serviços.
Cada peça sem vínculo costuma usar busca, detalhe e uma ou mais páginas de ofertas;
com vínculo economiza a busca. OAuth pode exigir uma chamada extra para renovar,
não incluída na contagem GET do job.

429 aplica até duas novas tentativas com backoff exponencial/jitter e respeita
Retry-After (segundos ou data). Se a espera exceder 60 segundos ou as tentativas
acabarem, interrompe para execução posterior. 401, 403, 5xx e cota local esgotada
interrompem o lote geral; erros de formato/identidade são registrados por peça.
Não contorna bloqueios. Paginação incompleta, duplicatas ou total mutável não
produzem lista parcial de ofertas.

O JSON final distingue revisão, não encontradas, falhas, sem ofertas, ofertas
criadas/atualizadas/inalteradas/desativadas, histórico e tentativas HTTP. Em
simulação as quantidades são propostas. Interrupções retornam erro no CLI depois
do resumo, para que jobs agendados não indiquem sucesso indevidamente.

Referência: [rate limit e 429](https://developers.mercadolivre.com.br/pt_br/usuarios-e-aplicativos/rate-limit-erro-429).


## Validação local antes do deploy

Executados em MySQL 8.4 real descartável: migrations e preservação de usuário,
idempotência, histórico, rollback, renovação cifrada (resposta OAuth simulada),
concorrência de renovação, revalidação da peça alterada por outra conexão e duas
gravacões simultâneas. Cinco testes de integração passaram. O código usa leituras
com lock para revalidar o estado atual no MySQL, evitando snapshots antigos da
transação iniciada antes das chamadas HTTP.

Para repetir, use SOMENTE um MySQL local descartável com banco `boostio_ml_teste`:

```sh
# Na pasta backend; substituir PORTA e SENHA do servidor descartável.
BOOSTIO_MYSQL_TEST_URI='mysql+pymysql://root:SENHA@127.0.0.1:PORTA/boostio_ml_teste' \
  ../venv/bin/python -m pytest tests/integration/test_mercadolivre_mysql.py -q
```

Esses testes criam e removem tabelas: não use banco da aplicação. O teste recusa
hosts externos e nomes de banco diferentes. Sem a variável, os testes MySQL são
ignorados na suíte normal. A suíte normal passou com 1.401 testes; estes cinco
foram executados separadamente no servidor local descartável.

A imagem Docker da API foi construída com sucesso em Python 3.12 e os comandos
foram carregados sem credenciais reais; `.env` não estava na imagem. Não houve push.

Uma simulação online, em cópia temporária do banco local, consultou cinco CPUs e
cinco GPUs: 10 requisições, zero falhas, dez casos para revisão e zero propostas
de ofertas. Esse resultado não comprova cobertura automática: a identidade exata
não estava comprovada nos códigos e atributos retornados. A revisão dos vínculos
ou o cadastro dos MPNs reais continua necessário antes da primeira importação.
Nenhuma oferta foi gravada no banco original, nem houve acesso à VPS.
