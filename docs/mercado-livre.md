# Mercado Livre: catálogo e OAuth no banco

O coletor `BuscarOfertasMercadoLivreService.executar(catalogo_id)` consulta
`/products/{id}` e `/products/{id}/items`, com paginação, preços Decimal em BRL,
identidade de anúncio/vendedor e condição. Não grava peças, ofertas ou histórico.
Lista vazia não prova falta de estoque. `esgotado`, pagamento e afiliação ficam
`None`; frete não é calculado. Anúncios usados são identificados e não são
convertidos em novos. Associe peças ao catálogo por especificações revisadas.

No contexto Flask:

```python
from services.preco_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
resultado = BuscarOfertasMercadoLivreService().executar("MLB47814270")
```

Sem argumento de token, lê as credenciais do model `TokenIntegracao`, com renovação
quando restam até 60 segundos. O argumento opcional `access_token` é reservado a
chamadas explícitas/testes e não tem renovação automática.

## Configuração

No ambiente do backend:

```dotenv
MERCADO_LIVRE_CLIENT_ID=
MERCADO_LIVRE_CLIENT_SECRET=
MERCADO_LIVRE_CONTA_ID=
INTEGRACOES_TOKEN_CHAVE=
```

CONTA_ID é o ID retornado por `/users/me` ou `user_id` da autorização OAuth. A chave
Fernet deve ser gerada uma vez e conservada fora do banco/Git (ver
[tokens-integracao.md](tokens-integracao.md)). Não substituir por SECRET_KEY.
Não é necessário access token ou refresh token no `.env`: o par vive no banco.
O callback OAuth inicial continua fora do coletor.

Na VPS, após backup e reconstrução da imagem:

```sh
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app integracoes-tokens-preparar
```

Para cadastrar um par obtido em autorização, com prompts ocultos:

```sh
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app mercadolivre-tokens-configurar
```

Por padrão expira imediatamente para renovar na próxima consulta. Use
`--validade-segundos` apenas com a validade **restante** conhecida. Este comando
substitui intencionalmente um par existente, por exemplo após reautorização.

## Transferir arquivo antigo

Pare coletores antigos que usem o arquivo antes de transferir; mantenha-os parados
após a troca. Configure a mesma aplicação/conta e chave de criptografia. O comando
não consegue descobrir a identidade a partir de um arquivo que só contém tokens;
a configuração deve corresponder à conta autorizada.

```sh
docker compose --env-file .env.production run --rm --no-deps \
  -v "$PWD/instance:/origem" api python -m flask --app app \
  mercadolivre-tokens-transferir --arquivo /origem/mercado_livre_tokens.json \
  --remover-arquivo
```

A pasta de origem precisa ser gravável se usar `--remover-arquivo`; sem a flag,
o arquivo é preservado. O comando bloqueia a origem, valida o conteúdo, cifra e
confirma no banco e verifica a leitura antes de remover. Repete sem alterações se
o registro for igual; recusa substituir um registro diferente por arquivo antigo.
Falha antes da confirmação preserva a origem. Falha de remoção após confirmação
pode deixar ambos; o service lê exclusivamente o banco, nunca faz fallback.
A identidade da conta local foi conferida por `/users/me` antes da transferência.

A aplicação não usa mais o volume `mercado_livre_oauth`. Não remova volumes antigos
sem conferir seu conteúdo e sua política de backup. Nenhuma VPS foi alterada.

## Concorrência e renovação

O repository SQL delega consultas e escrita ao model. Cada escrita usa transação
própria, não confirma alterações pendentes de builds na sessão Flask. A coluna
`versao` realiza compare-and-swap: somente quem leu a versão atual pode alterá-la.
Uma renovação pendente é confirmada antes do POST OAuth, evitando dois consumos
do mesmo refresh token. Um concorrente recebe erro para repetir a leitura depois,
sem renovar em paralelo. A unicidade protege a criação inicial concorrente.

Depois da resposta, o novo par é cifrado e salvo junto com a expiração. Falha de
rede/HTTP, resposta inválida ou falha na gravação final deixa o estado pendente:
o service exige reautorização, sem repetir um refresh token que pode ter sido
consumido. Erro 403 de consulta não dispara renovação. Esse estado conservador
pode exigir intervenção mesmo em erros transitórios.

Os testes exercitam SQLite, inclusive concorrência com duas conexões. Ainda é
necessário validar no MySQL real antes de publicar. A transferência local cria a
tabela e preserva as demais; não executa coleta nem salva builds.

## Transporte e limites

Não segue redirects; timeout 10s conexão/30s leitura. Respostas do catálogo têm
limite 2 MB; OAuth, 64 KB. Máximo 1.000 ofertas e páginas de 100. HTTP inesperado,
JSON inválido, valores/site/moeda inválidos, duplicatas e paginação incompleta ou
com total alterado falham sem lista parcial. Paginação não é snapshot atômico e
pode não detectar alterações simultâneas que não mudem total. Controle frequência
e respeite 429. Erros não incluem credenciais ou respostas completas.

O teste real pelo catálogo retornou anúncio de terceiro por R$44; os endpoints
diretos de anúncio responderam 403. Não é garantia de acesso permanente ou de
cobertura de todo o banco.

Referências: [catálogo](https://developers.mercadolivre.com.br/buscador-de-produtos),
[OAuth](https://developers.mercadolivre.com.br/autenticacao-e-autorizacao).
