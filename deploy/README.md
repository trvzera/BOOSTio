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

## Login Google: redirect_uri_mismatch

Em 25/10/2026, a rota pública de login enviou ao Google este `redirect_uri`:

```text
https://api.boostio.com.br/auth/google/entrar
```

No Google Cloud, abra o cliente OAuth do tipo **Aplicativo da Web** usado pela
API e adicione esse endereço em **URIs de redirecionamento autorizados**.
Ele precisa coincidir exatamente, inclusive protocolo, domínio, caminho e
ausência de barra final. Não use a página inicial ou a rota de início do login
(`/auth/google/redirecionar`). Preserve os retornos locais que ainda usa.

O servidor deriva o callback de `API_PUBLIC_URL`; por isso ele permanece HTTPS
mesmo quando a comunicação entre Traefik e API é HTTP. Não é preciso alterar
o código do OAuth para o endereço público observado. O cadastro no Google
Cloud é uma etapa externa ao repositório e não foi modificado nesta revisão.

Referência: [OAuth para aplicações web — Google](https://developers.google.com/identity/protocols/oauth2/web-server#redirect-uri).

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
