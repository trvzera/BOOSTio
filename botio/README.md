# BOTio

Bot oficial da BOOSTio, executado separadamente do site. Primeira função:
atribuir o cargo **Membro** quando o Discord indicar a conclusão da verificação
nativa (`pending=False`). Não lê mensagens nem precisa de Administrador.

## Boas-vindas privadas

Depois da liberação do cargo, novos membros recebem um embed privado com o
site https://boostio.com.br/, Instagram https://www.instagram.com/boostiooficial/
e botão para abrir a comunidade. Não publica saudações nos canais.
Membros antigos encontrados na sincronização não recebem mensagens em massa.
Entradas e membros pendentes observados pelo bot ficam registrados em
`botio/state.sqlite3` (ignorado pelo Git). Preserve esse arquivo entre reinícios
e deploys para evitar duplicações e recuperar saudações pendentes.
Quem entrar e concluir o aceite inteiramente com o bot desligado não recebe
saudação retroativa, mas continua recebendo o cargo na sincronização.

Cada entrada recebe no máximo uma tentativa de DM: se o destinatário bloquear
mensagens ou houver falha de envio, o acesso permanece e o bot não insiste.
Uma saída seguida de nova entrada permite nova saudação. Se o processo parar
entre a reserva e o envio, a saudação não é repetida para evitar mensagens duplicadas.

## Configuração no Discord

1. Ative Comunidade e o aceite obrigatório das regras em Configurações de Segurança.
2. No https://discord.com/developers/applications crie a aplicação **BOTio**.
3. Na seção Bot, ative **Server Members Intent**. Message Content e Presence não são necessários.
4. Gere o token e guarde-o somente em `botio/.env`, nunca no código, Git ou chat.
5. Em OAuth2 → URL Generator, selecione `bot` e a permissão **Manage Roles**.
   Abra o link gerado e adicione o bot ao servidor BOOSTio.
6. Crie o cargo **Membro**, sem permissões administrativas. Coloque o cargo do
   BOTio acima dele, abaixo dos cargos de equipe. Não conceda cargos de equipe ao bot.
7. Ative Modo desenvolvedor nas configurações avançadas da sua conta Discord;
   clique com o botão direito no cargo Membro e copie seu ID.
8. Copie `.env.example` para `.env` nesta pasta e preencha token e ID do cargo.
   O ID do servidor BOOSTio já está no exemplo.

## Visibilidade

| Área | @everyone | Membro |
| --- | --- | --- |
| Boas-vindas e regras | Ver e ler; sem enviar | Ver e ler |
| Dúvidas de entrada | Ver e ler | Ver e participar |
| Comunidade, hardware e voz | Negar Ver canal | Permitir Ver canal e participação |
| Equipe e logs | Negar Ver canal | Sem autorização; liberar só cargos da equipe |

Sincronize os canais às permissões de suas categorias. Verifique cargos de
interesse do onboarding para que eles não liberem as categorias restritas.
Antes do aceite, o Discord bloqueia a participação, inclusive no canal de dúvidas;
deixe nele orientações de entrada que possam ser lidas sem conversar.

Não use autorole na entrada, botão alternativo de verificação ou verificação
manual em conjunto com esse fluxo: podem dispensar o aceite nativo.
`pending=False` indica que o Discord liberou a pessoa, não prova de clique:
também abrange membros antigos e pessoas dispensadas pela administração.
O bot sincroniza esses membros existentes no primeiro início e a cada 10 minutos.
Se o aceite obrigatório estiver desativado, não concede novos cargos.
Não remove cargos já existentes nem modifica canais automaticamente.

## Executar (Python 3.11+)

Na raiz do repositório:

```sh
python3 -m venv botio/.venv
botio/.venv/bin/python -m pip install -r botio/requirements.txt
cp botio/.env.example botio/.env
# Preencha botio/.env em um editor antes de executar.
botio/.venv/bin/python botio/main.py
```

O bot precisa continuar ligado para entregar cargos imediatamente. Se parar,
recupera os membros liberados na próxima inicialização. Esta versão não foi
integrada ao deploy do site: hospede como processo independente.

## Validação

```sh
botio/.venv/bin/python -m unittest discover -s botio -p 'test_*.py'
```

Teste real com uma conta sem administração: entre sem aceitar e confira apenas
os três canais de entrada; confirme que não recebeu Membro; aceite as regras;
confirme o cargo e os demais canais. Repita aceitando com o bot desligado e
reiniciando-o. Confira também que nenhuma categoria privada de equipe foi liberada.

## Novos comandos e operação

- `/ajuda`: painel privado com links oficiais, regras e comandos de privacidade.
- `/montar`: envia o link do site da BOOSTio, em resposta privada.
- `/ticket`: abre um atendimento privado; o botão em `/ajuda` faz o mesmo.
- `/fechar-ticket`: solicita confirmação antes de apagar o canal e suas mensagens.
- `/privacidade`: resumo dos dados e canal de contato, em resposta privada.
- `/apagar-meus-dados`: remove o registro local do próprio membro.
- `/anunciar`: prévia privada e confirmação para equipe com Gerenciar servidor;
  configure `DISCORD_ANNOUNCEMENTS_CHANNEL_ID` antes de publicar.
- `/testar-boas-vindas`: equipe testa a DM somente na própria conta, sem
  alterar o histórico de saudações automáticas.
- `DISCORD_MOVEMENT_CHANNEL_ID`: canal privado para registros de entrada e
  saída com username, apelido no servidor e ID. 📥 indica entrada e 📤 indica saída.
  Não atribua essa função também à Loritta
  se não quiser registros duplicados. O canal precisa estar oculto para
  `@everyone` e `Membro`; o bot precisa de Ver canal, Enviar mensagens e Inserir links.

Após editar o código, encerre o processo antigo no VS Code e execute novamente.
O terminal da versão atual informa `BOTio 0.4` e os canais configurados.
Boas-vindas são enviadas após o aceite, não antes. A tabela local distingue
`waiting` (aguardando), `sent`, `blocked`, `failed` e `claimed` (tentativa reservada).
Não exclua o banco para testar: use `/testar-boas-vindas` e depois uma conta comum
entrando e aceitando as regras. Falta de configuração do canal de movimentação
não impede o cargo nem a DM. A sincronização de segurança ocorre a cada 10 minutos.

## Contador de membros

Configure `DISCORD_MEMBER_COUNT_CHANNEL_ID` com o ID de um canal de voz existente.
O BOTio exibe `👥 Membros: N`, incluindo todas as pessoas e bots do servidor,
mesmo que não estejam conectados a um canal de voz ou ainda aguardem o aceite.
O total vem do servidor, sem depender da lista parcial de membros no cache.

A primeira atualização ocorre após conectar, e as seguintes a cada 5 minutos.
O canal só é renomeado quando o total muda. Falhas temporárias são registradas
e tentadas novamente no próximo ciclo; a biblioteca respeita os limites da API.
Conceda ao BOTio **Ver canal** e **Gerenciar canais** nesse canal. Não precisa
de permissão de conectar ao áudio. O bot preserva as permissões do canal.
Deixe apenas o BOTio atualizando esse contador; desative o Server Stats nele
ou remova o outro bot. Apagar o canal exige configurar o ID de um novo canal.

Ao atualizar a versão, preserve o banco de boas-vindas. A primeira inicialização
padroniza automaticamente as datas antigas para milissegundos, recuperando DMs
aguardando envio sem repetir tentativas já registradas como enviadas ou bloqueadas.

## Atendimento privado

Configure `DISCORD_TICKETS_CATEGORY_ID` com uma categoria de suporte e
`DISCORD_SUPPORT_ROLE_ID` com o cargo da equipe. O cargo não pode ser Membro,
@everyone ou um cargo gerenciado por outro bot. Conceda ao BOTio Ver canal,
Gerenciar canais e Gerenciar permissões nessa categoria.

Cada pessoa, após liberação do acesso, pode abrir um ticket por vez. O canal
é criado com permissões explícitas para o solicitante, equipe e BOTio,
oculto aos demais membros. Cargos com Administrador mantêm acesso pelo Discord.
O nome é `ticket-ID` e o tópico identifica o solicitante. A consulta desses
canais permite recuperar tickets e evitar duplicações após reinícios.

`/fechar-ticket` e o botão Encerrar atendimento pedem confirmação, válida por
um minuto. Apenas o solicitante, o cargo de suporte ou quem tem Gerenciar servidor
pode encerrar. A permissão é verificada de novo ao confirmar. Encerrar exclui o
canal e suas mensagens; não há transcrições nem arquivo de conteúdo pelo BOTio.
Tickets abertos permanecem no Discord até encerramento; sair do servidor ou
usar `/apagar-meus-dados` não encerra um atendimento. A equipe pode encerrá-lo.
Há intervalo de um minuto entre novas aberturas. Os botões existentes continuam
funcionando após reiniciar o bot; confirmações de exclusão expiram normalmente.

Consulte [OPERACAO.md](OPERACAO.md) para o serviço Docker independente na VPS,
atualizações e cuidados com credenciais. A [PRIVACIDADE.md](PRIVACIDADE.md)
descreve os dados atuais e identifica informações organizacionais que precisam
ser completadas antes da publicação definitiva da política.
