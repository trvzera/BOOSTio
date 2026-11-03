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
Este histórico tem uma série separada da KaBuM e agora pode ser selecionado na
página da peça. A exibição usa apenas ofertas previamente importadas no banco.

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
gravacões simultâneas. Seis testes de integração passaram. O código usa leituras
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
ignorados na suíte normal. A suíte normal é executada separadamente; os seis testes MySQL
foram executados no servidor local descartável.

A imagem Docker da API foi construída com sucesso em Python 3.12 e os comandos
foram carregados sem credenciais reais; `.env` não estava na imagem. Não houve push.

Uma simulação online, em cópia temporária do banco local, consultou cinco CPUs e
cinco GPUs: 10 requisições, zero falhas, dez casos para revisão e zero propostas
de ofertas. Esse resultado não comprova cobertura automática: a identidade exata
não estava comprovada nos códigos e atributos retornados. A revisão dos vínculos
ou o cadastro dos MPNs reais continua necessário antes da primeira importação.
Nenhuma oferta foi gravada no banco original, nem houve acesso à VPS.

## Execução na VPS

O wrapper `deploy/atualizar_ofertas_mercadolivre.sh` executa a validação antes da
coleta, usa lock por host e não faz pull, build, migration ou configuração sozinho.
O comando `mercadolivre-validar` verifica variáveis, chave Fernet, tabelas, controle
de coleta, identidade e leitura do par de tokens. Não chama a API nem renova tokens;
`renovacao_necessaria=true` informa que a próxima coleta tentará renovar. Isso não
comprova que a autorização externa continua válida: essa confirmação ocorre na
consulta real. O wrapper exige `flock` (util-linux) na VPS.

Na primeira instalação, configure as quatro variáveis descritas em
[mercado-livre.md](mercado-livre.md), faça backup e prepare o ambiente:

```sh
cd /opt/BOOSTio
export BOOSTIO_BACKUP_DIR="$HOME/backups/boostio"
bash deploy/backup_mysql.sh
docker compose --env-file .env.production build api
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app integracoes-tokens-preparar
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app mercadolivre-ofertas-preparar
```

Cadastre um par OAuth válido com `mercadolivre-tokens-configurar` se ainda não
existe no banco da VPS. Tokens e chave locais não são enviados por Git. Não rode
`banco-preparar` num MySQL já populado nem substitua o banco da VPS pelo SQLite.

Simule um lote pequeno e examine especialmente os casos de revisão:

```sh
bash deploy/atualizar_ofertas_mercadolivre.sh \
  --categoria processador --limite-pecas 5 --max-requisicoes 20
```

Após resolver as identidades e conferir o relatório:

```sh
bash deploy/atualizar_ofertas_mercadolivre.sh --aplicar \
  --categoria processador --limite-pecas 5 --max-requisicoes 20
```

Não são cadastradas peças novas. O wrapper não resolve identidades ambíguas;
precisam de MPN real ou vínculo revisado antes de aparecerem ofertas.
Para publicar também a exibição no site, reconstrua `web` e recrie os serviços
`api`/`web`, preservando os volumes do banco.

## Exibição no frontend

O catálogo da conta e das builds públicas anexa ofertas ativas em uma consulta
em lote, sem consultas adicionais por peça. Não há consulta à API externa durante
a navegação. Antes da migration de ofertas, o catálogo segue sem essa parte.

A página da peça mostra preço registrado, vendedor e data da consulta no Mercado
Livre. Estoque NULL é apresentado como não confirmado. Links externos passam por
validação de HTTPS/domínio; `url_afiliado` configurada e válida tem preferência,
e o link original é usado como alternativa. Links não são gerados automaticamente.
A compra da build mostra as opções do marketplace mesmo quando a referência da
KaBuM está indisponível. Totais da build continuam usando o preço de referência,
sem substituir o orçamento pela menor oferta externa.

O histórico da peça permite selecionar KaBuM ou um anúncio/vendedor do Mercado
Livre. Cada gráfico é carregado separadamente, sem misturar anúncios. A rota
`GET /build/catalogo/<categoria>/<id>/ofertas/<oferta_id>/historico-precos` exige
sessão e valida que a oferta é ativa e pertence à peça. Dados indisponíveis geram
erro com nova tentativa; não viram uma série vazia. O modo demonstrativo não
consulta histórico de IDs reais.


Na leitura do catálogo, ofertas com vínculo cuja identidade local mudou são
ocultadas até revisão, mesmo que ainda tenham `ativa=true`. Isso evita mostrar
um anúncio antigo para um componente que foi renomeado ou teve seu MPN alterado.


Validação da conexão frontend/VPS: 1.411 testes backend e 755 testes frontend
passaram; seis testes MySQL foram executados separadamente. O Nginx validou sua
configuração e os novos módulos estão presentes na imagem do site. O wrapper foi
testado quanto a simulação padrão, aplicação explícita e bloqueio após falha de
validação/lock. Isso não substitui a configuração e a primeira simulação na VPS.

## Preencher MPNs reais nas peças existentes

`part_number` também é referência das imagens e medidas físicas das seeds.
Por isso o MPN confirmado fica em `identidade_fabricante`, sem renomear peças,
perder imagens ou recriar componentes. A associação automática prefere esse MPN,
conferindo fabricante e MPN explícito do catálogo Mercado Livre. Códigos
`SEED-*`, `REDE-*`, `DEMO-*` e `BOOSTIO-*` não são MPNs.

O manifesto versionado `backend/data/identidades-fabricante-revisadas.json`
contém **somente dois registros revisados nesta etapa**:

| Peça | Referência interna | MPN | Evidência |
| --- | --- | --- | --- |
| Kingston Fury Beast 8GB DDR4-3200 CL16, um módulo | SEED-RAM-01 | KF432C16BB/8 | [Ficha Kingston](https://www.kingston.com/datasheets/kf432c16bb_8.pdf) e [produto KaBuM](https://www.kabum.com.br/produto/172365/memoria-ram-kingston-fury-beast-8gb-3200mhz-ddr4-cl16-preto-kf432c16bb-8) |
| AMD Ryzen 7 5700X, sem cooler | SEED-CPU-02 | 100-100000926WOF | [Identificação AMD](https://www.amd.com/en/support/downloads/drivers.html/processors/ryzen/ryzen-5000-series/amd-ryzen-7-5700x.html) e [produto KaBuM](https://www.kabum.com.br/produto/320797/processador-amd-ryzen-7-5700x-3-4ghz-4-6ghz-max-turbo-cache-36mb-8-nucleos-16-threads-am4-sem-video-integrado-100-100000926wof) |

Não é um preenchimento completo do catálogo. A revisão encontrou links de
variantes divergentes: RAM cadastrada DDR5 com link DDR4; placa B550M DS3H com
link DS3H AC R2; headset Kraken X com link Kraken V4 X. Não foram aproveitados
como prova de identidade. Não se pode inferir o parceiro/fabricante de uma GPU
somente pelo nome do chip. MPN confirmado tampouco garante anúncio disponível
ou identificadores completos no catálogo Mercado Livre.

Na VPS, após atualizar o código, reconstruir a API e fazer o backup:

```sh
# Apenas cria a tabela nova; não modifica tabelas de usuários ou peças.
docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app mercadolivre-identidades-preparar

# Simulação: conferir propostas e casos enviados para revisão.
docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app mercadolivre-identidades-importar

# Grava somente identidades conferidas. Repetir não duplica nem substitui divergências.
docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app mercadolivre-identidades-importar --aplicar

# Coleta limitada: primeiro simular; depois repetir com --aplicar para cadastrar ofertas.
bash deploy/atualizar_ofertas_mercadolivre.sh \
  --categoria processador --limite-pecas 20 --max-requisicoes 100
bash deploy/atualizar_ofertas_mercadolivre.sh --aplicar \
  --categoria processador --limite-pecas 20 --max-requisicoes 100
```

Para RAM, repetir a coleta com `--categoria memoria_ram`. O manifesto não usa IDs
numéricos locais: exige categoria, referência interna, fabricante e modelo
exatos, produto KaBuM correspondente e especificações iguais. Ausência,
ambiguidade ou divergência gera revisão. Cada identidade tem sua transação;
falha de persistência interrompe a execução, podendo existir registros anteriores
já confirmados. A repetição é idempotente.

Para ampliar o preenchimento, revisar mais produtos e acrescentar registros ao
manifesto; `--arquivo` aceita outro JSON local (montá-lo no container). Não há
scraper que transforme automaticamente slug ou código da loja em MPN. Quem
mantém o manifesto deve conferir fonte, variante, kit, capacidade e especificações.
O importador valida consistência local; não prova sozinho a veracidade de um
manifesto fornecido pelo administrador. Não faz downloads nem cria vínculos
forçados no Mercado Livre.

Validação desta etapa: dois MPNs gravados apenas em cópia SQLite, segunda execução
com dois inalterados; testes de divergências e associação por MPN; migração e
idempotência também verificadas em MySQL 8.4 descartável. Nenhuma coleta foi
aplicada na VPS e nenhuma oferta foi criada no banco original por esta validação.
