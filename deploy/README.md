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
