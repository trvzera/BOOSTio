# Endereços e login Google

## Inicialização, banco e tarefas separadas

Instale as dependências com `python -m pip install -r requirements.txt`, na raiz.
Gunicorn está incluído para Linux; a instalação no Windows continua sem ele.

Os comandos abaixo são executados dentro de `backend`.

### Desenvolvimento no Windows

```console
python -m flask --app app banco-preparar
python app.py
```

Execute `banco-preparar` antes do primeiro uso e após atualizações que tragam
migrações. Não é necessário executá-lo a cada início do servidor. Seu SQLite
existente recebe uma cópia `.antes-migracao-*.db` antes das alterações; mantenha
essa cópia protegida. As migrações do banco local são específicas para SQLite.
Pare os processos que escrevem no banco ao migrar. O conjunto de migrações
possui várias transações: em caso de falha, corrija e repita ou restaure o backup
com o servidor parado. Não execute a migração simultaneamente em várias réplicas.

### Produção no Linux

Com o ambiente de produção configurado, execute uma vez por implantação:

```console
python -m flask --app app banco-preparar
python configurar_frontend.py
```

Com `URL_DATABASE=mysql+pymysql://...`, `banco-preparar` cria o esquema somente
em um banco MySQL vazio. Ele recusa um MySQL que já tenha tabelas, para não
silenciar mudanças de esquema. Para implantações futuras com alterações nos
models, faça uma migração versionada e um backup do MySQL antes de atualizar a
aplicação. Isso não altera o SQLite local.

Depois inicie o processo web:

```console
gunicorn -c gunicorn.conf.py wsgi:app
```

`wsgi.py` exige `APP_ENV=producao` e desativa debug. `python app.py` recusa iniciar
o servidor de desenvolvimento quando esse ambiente estiver ativo. Importar o
app não cria tabelas, executa migrações nem cadastra ou consulta peças.

O Gunicorn começa com um worker e quatro threads. Ajuste após medir memória e
carga, pelas variáveis `WEB_CONCURRENCY`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT`
e `GUNICORN_GRACEFUL_TIMEOUT`. O timeout de worker não é um prazo máximo de
requisição em workers com threads; mantenha os timeouts das integrações e alinhe
os limites do proxy com as chamadas de IA. Os logs vão para a saída do processo,
sem query strings no log de acesso.

Por padrão, `GUNICORN_BIND=127.0.0.1:8000`, para receber um proxy local. Plataformas
com contêineres podem exigir `GUNICORN_BIND=0.0.0.0:8000`, ou outra porta: use a
porta indicada pela hospedagem e restrinja o acesso à rede do proxy. Configure o
comando acima como serviço/processo web com reinício automático na hospedagem.
Não coloque a migração no comando de cada worker.

### Cadastro e atualização de preços

```console
python -m flask --app app pecas-popular
python -m flask --app app precos-atualizar --limite 20
python -m flask --app app pecas-imagens --limite 20
```

O primeiro comando cadastra as peças ausentes sem consultar lojas. O segundo
consulta os preços separadamente. `pecas-popular --atualizar-precos` permite
combinar as operações explicitamente. Não é necessário parar o backend para
atualizar preços, mas evite executar dois coletores ao mesmo tempo.

Para atualização periódica, configure `precos-atualizar` como um job separado no
agendador da hospedagem, com o mesmo ambiente e acesso ao mesmo banco persistente.
Defina frequência e limite conforme o orçamento de consultas. Nenhum agendamento
foi ativado automaticamente, e os workers web não executam essa coleta.

Defina no `backend/.env` local ou nas variáveis de ambiente da hospedagem.
Variáveis fornecidas pela hospedagem têm prioridade sobre o arquivo `.env`.
Não publique o `.env` na pasta estática do site.

## Desenvolvimento

`APP_ENV=desenvolvimento` mantém o comportamento local atual. Sem `API_PUBLIC_URL`,
o frontend chama o mesmo hostname local na porta 5000.
`FRONTEND_URL` continua aceitando um caminho, por exemplo
`http://127.0.0.1:5500/frontend`. Use sempre o mesmo hostname ao abrir o site e ao
cadastrar o callback: localhost e 127.0.0.1 não compartilham os mesmos cookies.

## Produção

### VPS Hostinger com Docker

O `compose.yaml` inicia MySQL, Redis, API e Caddy. Na VPS, aponte os registros
DNS de `boostio.com.br` e `api.boostio.com.br` para o IP da máquina e libere as
portas 80 e 443. O Caddy obtém os certificados HTTPS e serve a pasta `frontend`;
os contêineres de banco, Redis e API não publicam portas externas.

Copie `.env.production.example` para `.env.production` na raiz do projeto e
preencha as credenciais. Use a mesma senha em `MYSQL_PASSWORD` e na
`URL_DATABASE`, codificando caracteres especiais da senha na URL. Restrinja o
arquivo a quem administra a VPS (`chmod 600 .env.production`). Não copie o
`.env` local para a VPS. O SQLite local continua disponível fora do Docker.

Na primeira instalação, com o MySQL vazio:

```console
docker compose --env-file .env.production up -d --build db redis
docker compose --env-file .env.production run --rm api python -m flask --app app banco-preparar
docker compose --env-file .env.production run --rm api python -m flask --app app pecas-popular
docker compose --env-file .env.production up -d --build api web
```

O comando de preparação do MySQL só aceita um banco vazio. Em novas versões que
mudem o esquema, faça backup e uma migração específica antes de atualizar a API.
Não apague o volume `mysql_data`, que contém os dados. Os volumes `caddy_data` e
`caddy_config` guardam os certificados; `redis_data` guarda os contadores e
reservas de geração. Verifique `docker compose ps` e os logs da API e do Caddy
após subir os serviços. Configure backup periódico do MySQL fora da VPS.

Para publicar o conteúdo da pasta `frontend` na raiz do site, use:

```dotenv
APP_ENV=producao
FRONTEND_URL=https://boostio.com.br
API_PUBLIC_URL=https://api.boostio.com.br
CORS_ORIGINS=https://boostio.com.br
SESSION_COOKIE_SAMESITE=Lax
TRUSTED_PROXY_HOPS=0
TRUSTED_PROXY_PROTO_HOPS=0
```

O arquivo `backend/.env.producao.example` lista as variáveis necessárias. Preencha
os segredos nas variáveis da hospedagem, sem publicá-los no frontend ou no Git.
O backend recusa iniciar em produção sem `SECRET_KEY` de pelo menos 32 caracteres,
`URL_DATABASE`, credenciais Google, chave Gemini e credenciais de e-mail. O Redis
também é obrigatório para o Flask-Limiter. Mantenha a mesma `SECRET_KEY` entre
workers e implantações para preservar as sessões.

A geração de builds limita cada conta a dez tentativas por dia e reserva no Redis
até 100 chamadas diárias à IA para o projeto inteiro, contando revisões e tentativas
com outro modelo. O dia vira à meia-noite de São Paulo. Há uma trava por usuário
durante a geração; outra solicitação simultânea da mesma conta recebe HTTP 409.
Se o Redis estiver indisponível, o backend não gera builds sem esse controle.

Configure DNS e certificado HTTPS para `boostio.com.br` e
`api.boostio.com.br`. Publique a pasta `frontend` como raiz do site para que
`https://boostio.com.br/pages/index.html` exista. A API deve responder em
`https://api.boostio.com.br`, sem prefixo `/api` nessa configuração.

`FRONTEND_URL` é a base que contém `/pages`, usada nos retornos do login e links de
recuperação. Se o frontend estiver em `/frontend`, inclua esse caminho.
`API_PUBLIC_URL` é a base pública das rotas do backend. Pode incluir `/api` se o
proxy encaminhar esse prefixo ao Flask removendo-o.

Antes de publicar os arquivos estáticos, na raiz do projeto, execute:

```console
python backend/configurar_frontend.py
```

Esse comando lê o ambiente e gera `frontend/js/config-publica.js` **somente com a
URL da API**. Não acessa o banco nem exporta segredos. Publique esse arquivo junto
do frontend. Após mudar endereços, execute novamente e reinicie o backend.
Para voltar o arquivo gerado ao modo local, use `APP_ENV=desenvolvimento`, retire
`API_PUBLIC_URL` e execute novamente. O navegador não lê `.env` diretamente.

O backend exige URLs HTTPS em produção. CORS aceita por padrão apenas a origem
de `FRONTEND_URL`. Se houver outras origens legítimas, configure explicitamente:

```dotenv
CORS_ORIGINS=https://boostio.com.br
```

Não inclua caminhos nem `*`. Cookies continuam HttpOnly e Secure em produção.
`Lax` é adequado para frontend e API HTTPS no mesmo site, incluindo subdomínios.
Se estiverem em sites diferentes, configure `SESSION_COOKIE_SAMESITE=None`;
alguns navegadores ainda bloqueiam cookies de terceiros. Prefira domínios do mesmo
site ou proxy no domínio do frontend. CORS não substitui CSRF.

## Proxy da hospedagem

O proxy recebe o HTTPS do navegador e encaminha a requisição ao Flask, muitas
vezes por HTTP numa rede interna. Ele deve preservar o Host público e informar
o protocolo e IP originais nos cabeçalhos encaminhados.

Só configure valores maiores que zero se a hospedagem realmente usar esses
cabeçalhos. Se houver um proxy confiável escrevendo cada cabeçalho:

```dotenv
TRUSTED_PROXY_HOPS=1
TRUSTED_PROXY_PROTO_HOPS=1
```

O primeiro trata `X-Forwarded-For` (IP, usado nos limites); o segundo trata
`X-Forwarded-Proto` (HTTP/HTTPS). Os números podem ser diferentes: confirme com
a hospedagem. O proxy deve remover/substituir cabeçalhos enviados pelo cliente,
e o backend não deve ficar acessível diretamente por fora dele. Não use 1 por
suposição. `X-Forwarded-Host` não é aceito; o Host deve ser o domínio da API.

## Google Cloud

Cadastre em **URIs de redirecionamento autorizados** do cliente OAuth web:

```text
https://api.boostio.com.br/auth/google/entrar
```

O endereço é exatamente `API_PUBLIC_URL` + `/auth/google/entrar`, incluindo eventual
prefixo `/api`. É o mesmo callback para login e confirmação de identidade.
Não cadastre a URL de início `/auth/google/redirecionar` como callback.
O callback local pode permanecer cadastrado junto do de produção.

## Validação após publicar

Confirme que o navegador chama a API HTTPS correta, recebe o cookie de sessão,
conclui login Google, obtém `/auth/me`, envia ações com CSRF e recebe links de
recuperação apontando para o frontend publicado. Valide também o IP recebido pelo
Flask e os limites entre clientes distintos. Testes locais não substituem essa
validação na hospedagem escolhida.
