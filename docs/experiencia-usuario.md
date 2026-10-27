# Tutorial inicial e nível de conhecimento

Novos cadastros por senha e Google recebem um tutorial opcional de três passos.
Ele aparece após o carregamento da página, sem se sobrepor à verificação de
e-mail ou a outra janela. Contas antigas não recebem a apresentação automática;
o botão **Rever tutorial** fica em Configurações da conta.

O primeiro passo permite escolher **Estou começando**, **Conheço o básico** ou
**Tenho experiência**. A escolha é opcional e pode ser alterada no perfil.
O tutorial apresenta as duas formas de montagem, sem exigir um roteiro de navegação.

## Diferenças entre os níveis

- **Estou começando:** guias do formulário inicialmente abertos, explicações sobre
  a função de cada categoria junto das peças e orientações extras de preço dos
  tamanhos de gabinete.
- **Conheço o básico:** guias inicialmente abertos, sem os parágrafos extras junto
  das peças nem as dicas de preço específicas para iniciantes.
- **Tenho experiência:** guias inicialmente recolhidos, podendo ser abertos; sem
  os parágrafos e dicas específicos para iniciantes.
- **Prefiro não informar:** mesma apresentação do nível básico.

As orientações gerais sobre vidro e peças brancas aparecem para todos. O glossário
explica termos que aparecem nas peças (GB, TB, MHz, DDR, entre outros), em vez de
repetir a função da categoria. Pode ser aberto por toque ou teclado, rolado pelo
teclado e fechado com Escape. Medidas técnicas do gabinete continuam acessíveis
em detalhes opcionais, inicialmente recolhidos em todos os níveis.

O formulário mantém pergunta e ajuda juntas à direita, respostas à esquerda e
pergunta antes das respostas no celular. A preferência não muda catálogo, orçamento,
motor de compatibilidade, seleção da IA ou acesso a funcionalidades.

## Desfazer e refazer no editor

- Até 25 alterações em memória: remoção/quantidade de peças, melhorias aplicadas
  e opções de periféricos, rede e fans. Sair ou recarregar limpa o histórico.
- Ctrl/Cmd+Z desfaz; Ctrl/Cmd+Shift+Z refaz. Existem botões equivalentes e razões
  acessíveis quando estão indisponíveis. Nova alteração descarta o refazer anterior.
- Inputs de texto/número, descrição e campos editáveis mantêm o desfazer nativo.
  Nome, orçamento, descrição e privacidade não são revertidos pelo histórico de peças.
  Atalhos da build não são aplicados enquanto outra janela modal está aberta.
- A operação aguarda a fila de salvamento e grava o estado restaurado pela mesma
  API. Tranca, outra build ou mudança inesperada de componentes impedem a restauração.
  Falhas são apresentadas como erro, preservando o estado local para conferência.

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
