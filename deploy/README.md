# Ajustes de produção

## URLs das páginas

O Nginx serve `/`, `/builds`, `/formulario`, `/pecas`, `/peca`, `/sobre` e as
demais páginas sem `.html`. Os arquivos continuam em `frontend/pages`.
Links antigos redirecionam com HTTP 301, preservando os parâmetros de build,
categoria, filtros e compartilhamento. Não há alteração nas rotas da API.

As regras estão em `deploy/nginx.conf`, copiadas pelo `Dockerfile.frontend`.
É necessário reconstruir/publicar o serviço `web` para aplicá-las à VPS.
Atualizar apenas os arquivos HTML não instala essas regras. A prévia estática
do editor continua usando os arquivos `.html`.

## Blender Open Data

O navegador consulta a rota autenticada `/benchmark/blender` da BOOSTio.
O Python consulta os dados públicos do Blender, valida o modelo exato e salva
resultados válidos em cache por uma hora. Não executa testes no computador.

A consulta real via Python respondeu para i3-12100F, Ryzen 5 5600 e RTX 3060
em 25/10/2026. Isso confirma o contrato a partir do ambiente local; não confirma
a conectividade de saída da VPS nem identifica o erro ocorrido na conta.

Após publicar o serviço `api`, a mensagem do teste e os logs permitem distinguir:

- `422 / sem-dados`: a fonte não retornou resultados válidos para aquele modelo.
- `503 / rede` ou `tls`: falha de conexão entre a VPS e o Blender.
- `504 / timeout`: a fonte não respondeu dentro do prazo.
- `503 / acesso-provedor`: a fonte respondeu 401 ou 403 para a VPS.
- `503 / redirecionamento`: a fonte redirecionou a consulta, que não foi seguida.
- `502 / resposta`: JSON ou estrutura incompatível com o contrato esperado.
- `429 / limite`: aguardar o intervalo informado antes de consultar novamente.

O log `Blender:` inclui categoria, HTTP da BOOSTio, HTTP da fonte e formato da
resposta. Não registra cookies, credenciais ou conteúdo retornado por terceiros.
Se falhar na VPS, guarde a referência exibida e o modelo consultado antes de
alterar a integração. Nenhuma pontuação é inventada para substituir uma falha.


## Ofertas do Mercado Livre

Use `bash deploy/atualizar_ofertas_mercadolivre.sh` para simular. A gravação exige
`--aplicar`. O wrapper verifica a integração e impede jobs simultâneos no mesmo
host com `flock`. Ele adiciona ofertas a componentes existentes; não cria peças.
A preparação de tabelas e tokens é explícita. Veja
[execução e publicação](../docs/ofertas-mercado-livre.md#execução-na-vps).

Para autorizar o Mercado Livre diretamente no servidor, use
`mercadolivre-autorizacao-preparar` e depois `mercadolivre-conectar`.
O link administrativo expira em dez minutos e não deve ser compartilhado.
Instruções e configuração do callback em `docs/ofertas-mercado-livre.md`.

## Atualização diária de preços na VPS

As unidades em `deploy/systemd/` executam o script existente
`deploy/atualizar_precos.sh` diariamente às **03h de Brasília**, inclusive após
reiniciar a VPS. O fuso é declarado na própria agenda; em um servidor UTC,
o horário equivalente atual é 06h. A execução respeita a trava `flock` do script
e as reservas e limites de consulta da aplicação. O serviço não recria o banco.

Instalação no host Ubuntu, para o projeto em `/opt/BOOSTio` (confira unidades ou
agendamentos anteriores antes de instalar para não duplicar tarefas):

```bash
sudo install -m 644 deploy/systemd/boostio-precos.service /etc/systemd/system/
sudo install -m 644 deploy/systemd/boostio-precos.timer /etc/systemd/system/
sudo systemd-analyze verify /etc/systemd/system/boostio-precos.service /etc/systemd/system/boostio-precos.timer
sudo systemctl daemon-reload
sudo systemctl enable --now boostio-precos.timer
```

Executar agora, sem depender de manter o terminal conectado:

```bash
sudo systemctl start --no-block boostio-precos.service
```

Acompanhar o próximo horário e os resultados:

```bash
systemctl list-timers boostio-precos.timer --no-pager
systemctl status boostio-precos.service --no-pager
journalctl -u boostio-precos.service -n 30 --no-pager
```

Durante a execução, um serviço `oneshot` pode aparecer como `activating (start)`.
Isso não significa falha nem conclusão. O resumo JSON ao final informa quantas
consultas, alterações, históricos e falhas realmente ocorreram. Antes de aplicar
migrações, suspenda a agenda e aguarde encerrar qualquer coleta em execução.
O limite de três horas evita uma execução indefinida. Retomar após interrupção
continua sujeito às reservas diárias da aplicação; não apague essas reservas
para forçar requisições repetidas.
