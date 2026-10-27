# Tutorial inicial e nível de conhecimento

Novos cadastros por senha e Google recebem um tutorial opcional de três passos.
Ele aparece após o carregamento da página, sem se sobrepor à verificação de
e-mail ou a outra janela. Contas antigas não recebem a apresentação automática;
o botão **Rever tutorial** fica em Configurações da conta.

O primeiro passo permite escolher **Estou começando**, **Conheço o básico** ou
**Tenho experiência**. A escolha é opcional e pode ser alterada no perfil.
Iniciantes veem explicações junto das peças. O nível básico mantém as orientações
por etapa; para quem tem experiência, elas começam recolhidas. A ajuda e as mesmas funções continuam
disponíveis em todos os níveis. Essa preferência não altera a escolha de hardware
nem aprova compatibilidade.

## Preparação do banco existente

Antes de ativar a versão atualizada da API, dentro de `backend`, execute:

```sh
python -m flask --app app preferencias-preparar
```

O comando é idempotente e cria **somente** a tabela `preferencias_uso` quando
ela não existe, tanto em SQLite quanto nos bancos aceitos pelo SQLAlchemy.
Não recria a tabela `usuario`, não modifica contas existentes e não coleta preços.
Em um banco novo, `banco-preparar` já inclui a tabela no `db.create_all()`.
Importar `app.py` continua sem criar ou migrar tabelas automaticamente.

## Implementação

- `PreferenciasUso` guarda uma linha por conta, ligada por `usuario_id`.
  O cadastro cria a conta e o estado `pendente` na mesma transação.
  Ausência de registro significa `nao-oferecido`, preservando contas antigas.
- `GET /auth/me` entrega as preferências apenas ao próprio usuário autenticado.
  Serializações públicas não incluem esses dados.
- `PUT /usuarios/<id>/preferencias-uso` aceita somente `nivel_hardware` e/ou
  `tutorial` (`concluido` ou `pulado`), com sessão, propriedade da conta, CSRF,
  limite de requisições e `Cache-Control: no-store`.
- A conclusão e o nível ficam no servidor e são mantidos em outros dispositivos.
  Um marcador por conta em `sessionStorage` evita reapresentação na mesma sessão
  caso a pessoa feche o tutorial e a rede impeça o registro no servidor.
- Pular, fechar ou pressionar Escape fecha a janela imediatamente e tenta registrar
  a escolha. Se o nível foi alterado no tutorial, ele também é enviado. Uma falha
  mostra feedback; não é anunciada como sucesso. Concluir aguarda a confirmação
  e mantém o tutorial disponível para nova tentativa em caso de falha.
- `components/onboarding.js` é carregado sob demanda. O modal usa `dialog`,
  mantém foco por teclado, devolve o foco ao controle de origem e mantém os botões
  visíveis com rolagem apenas no conteúdo. Aguarda o loading e outras janelas.
- `conta/preferencias-uso.js` aplica a apresentação; `pages/experiencia-perfil.js`
  permite editar e rever; `salvar-preferencias-uso.js` impede aplicar respostas
  antigas após troca de conta e exige confirmação dos campos retornados.

## Validação

Os testes de backend usam bancos temporários e verificam persistência entre
sessões, contas antigas/novas, Google, CSRF, isolamento por conta e rollback.
Os testes de interface usam respostas simuladas, sem cadastrar usuários reais,
enviar e-mails, chamar a IA ou salvar builds.
