# Privacidade do BOTio

O BOTio é operado pela equipe BOOSTio para liberar o cargo Membro após a
verificação nativa do Discord, enviar uma saudação de entrada e publicar
atualizações solicitadas pela equipe. Contato: contato@boostio.com.br ou equipe
do servidor oficial.

## Dados e finalidades

- IDs do servidor e do membro, data de entrada e situação da tentativa de
  boas-vindas: usados para entregar uma única saudação por entrada e recuperar
  operações interrompidas.
- Estado de verificação e cargos: consultados para liberar o acesso, sem cópia
  persistente da lista de cargos.
- Nome de exibição e ícone do servidor: usados na apresentação da mensagem,
  sem gravação no banco do bot.
- Título e texto de anúncios: usados na prévia temporária e na publicação
  confirmada no canal configurado. Não há arquivamento próprio do conteúdo.
- Entrada e saída: quando configurado, um canal privado da equipe recebe
  username, apelido no servidor e ID, com indicação de entrada ou saída.
  Esses registros ficam em mensagens do Discord, sem cópia em banco local.
- Contador: o total de membros, incluindo bots, é exibido no nome de um canal
  de voz. Não é mantido histórico desse total nem criada uma lista própria de membros.
- Atendimento: tickets ficam em canais privados do Discord. O tópico contém o ID
  do solicitante para localizar o atendimento após reinícios. Solicitante, equipe
  e cargos com Administrador têm acesso às mensagens enviadas nesse canal.
- Mensagens: quando habilitado, edições e exclusões de mensagens em canais da
  comunidade geram registros privados para a equipe, com autor quando conhecido,
  IDs, canal, horário e trechos de texto antes/depois ou excluído. Anexos são
  representados pela quantidade, sem download. Tickets, threads privadas,
  canais privados da equipe e DMs não são copiados para esses registros.

O bot não mantém histórico de conversas no banco local, não solicita senhas e não usa os dados
para publicidade, venda ou treinamento de IA. Os links para o site e Instagram
na saudação não fazem inscrição em campanhas. Aceitar as regras não equivale
a consentir com publicidade ou com uma futura vinculação de contas.

## Armazenamento e retenção

O registro de boas-vindas fica em SQLite na máquina que executa o bot, ou em
volume privado na VPS quando hospedado. Permanece durante a participação no
servidor para evitar duplicações. É excluído quando o bot observa a saída ou na
próxima sincronização completa após voltar a funcionar. Uma nova entrada pode
gerar novo registro e nova saudação.

Tickets abertos permanecem no Discord até encerramento pelo solicitante ou pela
equipe. Encerrar exige confirmação e apaga o canal com suas mensagens. O BOTio
não mantém transcrições ou cópia dessas conversas no banco local. A saída do
servidor e `/apagar-meus-dados` não encerram tickets; procure a equipe ou use
`/fechar-ticket` no canal do atendimento para solicitar seu encerramento.

O monitoramento mantém cache temporário de até 1.000 mensagens na memória do
processo, perdido ao reiniciar. Não consulta o histórico para recuperar mensagens
antigas. Os registros de edições e exclusões são novas mensagens no canal privado
da equipe e permanecem no Discord até exclusão pela equipe. Cada trecho tem até
1.024 caracteres; exclusões em lote mostram até 20 IDs e 5 trechos de até 800
caracteres. `/apagar-meus-dados` e o encerramento de tickets não apagam esses logs.
Para solicitar a remoção deles, procure a equipe pelo contato informado.

Logs próprios evitam identificar membros e não registram token ou conteúdo das
conversas. No modelo Docker fornecido, os logs têm rotação por tamanho.
Não há backup automático dos registros do bot nessa configuração. Cópias feitas
manualmente pela equipe precisam de proteção, prazo de retenção e aplicação
das exclusões antes de uma restauração.

O Discord processa mensagens, comandos e eventos conforme sua própria política.
Ao hospedar na VPS, o provedor de infraestrutura armazena os arquivos como
prestador de serviço. O fornecedor e a região devem ser informados nesta página
antes da publicação definitiva. Instagram e site tratam dados de navegação quando
o próprio usuário abre os respectivos links.

## Acesso, correção e exclusão

O comando `/privacidade` apresenta estas informações de forma resumida.
`/apagar-meus-dados` exclui o registro local do solicitante sem retirar o cargo.
Não apaga as mensagens já entregues pelo Discord. Para consulta dos dados,
correção, outras solicitações ou relato de incidente, procure a equipe pelo
contato acima. A equipe deve confirmar a identidade de quem solicita dados de
outro meio antes de revelar qualquer informação.

O comando de exclusão local não apaga registros de movimentação e mensagens do canal da
equipe; a remoção dessas mensagens pode ser solicitada pelo mesmo contato.
Não há limpeza automática desse canal nesta versão. A equipe precisa definir
e aplicar um prazo de retenção justificado antes do uso em produção.

## Antes de publicar esta política

Este texto descreve o código atual, mas a configuração técnica não certifica
conformidade jurídica. A equipe deve identificar o responsável pelo tratamento,
informar fornecedor/região da hospedagem, documentar a base legal adequada ao
tratamento e sua avaliação quando necessária, manter contato funcional e
publicar uma URL acessível no Portal do Desenvolvedor. Atualize a política antes
de acrescentar vinculação de contas ou monitoramento com novos dados.
