# Operação e segurança do BOTio

## VPS

O bot pode usar a mesma VPS da BOOSTio em serviço independente. Não necessita
de portas de entrada, proxy, acesso ao Docker socket, banco MySQL, Redis, pastas
do site ou suas credenciais. Necessita de conexão de saída HTTPS/WebSocket ao
Discord e DNS. O compose usa rede própria, usuário sem root, filesystem somente
leitura, capacidades removidas, limite de recursos e volume exclusivo para estado.
O volume é protegido por permissões do sistema, mas não é criptografado pelo bot.

1. Envie a pasta do bot à VPS, excluindo `.venv`, `.env`, token e caches.
2. Em diretório privado da VPS, crie um arquivo contendo somente o token (sem
   `DISCORD_BOT_TOKEN=`). Configure acesso de leitura apenas para o usuário do
   container (UID 10001) e administradores autorizados. Não coloque o token na imagem.
3. Crie `botio/.env` com IDs do servidor, cargo Membro, canal de anúncios e
   `BOTIO_TOKEN_FILE=/caminho/privado/do/token`. Esse arquivo não precisa conter o token.
   Para o contador, preencha `DISCORD_MEMBER_COUNT_CHANNEL_ID` com o canal de voz
   existente e conceda Ver canal e Gerenciar canais ao BOTio somente nesse canal.
4. Pare o processo do Mac com Ctrl+C; mantenha apenas uma instância ativa.
5. Na pasta `botio`, execute:

```sh
docker compose config --quiet
docker compose up -d --build
docker compose logs --tail=50 botio
```

O arquivo de token precisa estar legível para UID 10001 dentro do container:
secrets do Compose local usam arquivo montado; não constituem cofre criptografado.
Preserve `botio_data` entre atualizações. Não use `down -v` para atualizar.
Valide o acesso aos três canais iniciais e a ocultação da equipe com conta comum.

Não foi executado deploy automaticamente. O build Docker e a conectividade real
precisam ser verificados na VPS. Mantenha SO, Docker e dependências atualizados;
o lock fixa versões para revisão e reprodutibilidade, não garante ausência de CVEs.

## Permissões e credenciais

- BOTio abaixo de toda a equipe e acima apenas dos cargos que precisa atribuir.
- Cargo Membro sem poderes administrativos; configure categorias por permissões.
- Autorole de outros bots e verificação manual podem dispensar o aceite nativo.
- MFA nas contas da equipe e no GitHub; SSH por chave na VPS, sem expor credenciais.
- Nunca envie tokens no chat, logs, commits, screenshots ou argumentos de comandos.
- Em vazamento: redefina o token no Developer Portal, substitua o segredo e
  reinicie o bot; revise auditoria, permissões e acesso à VPS. Avalie comunicação
  ao Discord e titulares/autoridade conforme o incidente e obrigações aplicáveis.
- A API não comprova o clique nas regras: pending=False também inclui dispensa
  administrativa. O bot não faz concessão quando o aceite nativo está desativado.

## Atualizações do projeto

Configure `DISCORD_ANNOUNCEMENTS_CHANNEL_ID` com o canal público de novidades.
Reinicie para registrar os comandos exclusivos do servidor BOOSTio.
`/anunciar titulo:... texto:...` requer Gerenciar servidor, mostra prévia privada
e destino, e publica apenas ao confirmar em até 3 minutos. Não menciona cargos,
everyone ou here, mesmo que o texto contenha essas marcações. Um preview só
publica uma vez. Não usa shell, não interpreta texto como código e não busca URLs.

Commits não disparam anúncios públicos. O próximo passo é ligar eventos de
deploy bem-sucedido a um canal privado. A publicação para usuários continua
controlada; a integração GitHub/deploy ainda não foi implementada.

## Tickets

Configure `DISCORD_TICKETS_CATEGORY_ID` e `DISCORD_SUPPORT_ROLE_ID`. A categoria
deve ser reservada ao atendimento; o BOTio precisa de Ver canal, Gerenciar canais
e Gerenciar permissões. Cada canal criado tem permissões próprias, sem conceder
acesso aos demais membros. Administradores continuam com acesso.
Após reiniciar, valide `/ajuda`, `/montar`, `/ticket` e `/fechar-ticket`.
Use uma conta comum para conferir que somente seu atendimento aparece e que
cancelar o encerramento preserva o canal. Confirme uma exclusão apenas em um
ticket de teste: ela remove o canal e suas mensagens definitivamente.
