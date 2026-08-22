> **EN:** Repository for BOOSTio, my annual final course software project — a platform that helps people choose and build PC setups based on budget and goals. Auth flow (signup, login, logout, session-protected routes) is functional end-to-end; the PC-building core is still in development.
>
> *The rest of this README is in Brazilian Portuguese (pt-BR).*

---

# BOOSTio

Repositório do meu **projeto de software anual e final do curso**, desenvolvido no **Colégio Cotemig**. É aqui que o BOOSTio é desenvolvido, versionado e documentado ao longo do ano.

## Sobre o projeto

O BOOSTio é uma plataforma que simplifica a montagem de computadores. A ideia é ajudar o usuário a escolher as peças ideais com base no seu orçamento e objetivo (jogos, trabalho, uso cotidiano), permitindo também a seleção manual de componentes específicos, com o sistema integrando essas escolhas à sugestão final. O usuário pode salvar seus setups no perfil e compartilhar com outras pessoas.

## Status

**Em desenvolvimento ativo.** O fluxo de autenticação (cadastro, login, logout e proteção de rotas) já está funcional de ponta a ponta, com front-end e back-end conectados. O núcleo de montagem de PC (catálogo de peças, formulário de recomendação, builds salvas) ainda está em construção — os modelos de dados já existem no back-end, mas as rotas e telas correspondentes ainda não.

## Funcionalidades

### ✅ Concluído (front + back conectados)

-Cadastro de usuário com verificação de força de senha em tempo real, confirmação de senha e aceite obrigatório dos termos.
-Login tradicional com exibição de erros retornados pela API (ex: senha incorreta).
-Login com Google (OAuth2), permitindo criar conta ou autenticar sem precisar de senha.
-Logout, encerrando a sessão via cookie httpOnly.
-Atualização de dados do usuário (PUT /usuarios/<id>), protegida por login e por um decorator que garante que só o próprio usuário edite seus dados.
-Exclusão de conta (DELETE /usuarios/<id>), restrita ao próprio usuário, com logout automático após a exclusão.
-Busca do usuário logado (buscarUsuarioLogado.js), usada para checar sessão ativa e popular dados no front.
-Recuperação de senha por e-mail, com token seguro e expiração, sem revelar se o e-mail está cadastrado (proteção contra enumeração de usuários).
-Envio e conferência de código de verificação por e-mail, usado na ativação de conta e na redefinição de senha.
-Menu de perfil dinâmico no header e mostrar/ocultar senha em todos os campos, com proteção de rotas restritas no front para usuários não autenticados.

### 🚧 Pronto na interface, aguardando rota no back-end (PUT/DELETE)

- Edição de nome e e-mail do perfil
- Troca de senha, com indicador de força e confirmação
- Exclusão de conta, com modal de confirmação por digitação do nome de usuário

### 📋 Planejado

- Formulário de recomendação de setup (orçamento + objetivo)
- Catálogo de peças (`Peca`, `Fonte`)
- Montagem e salvamento de setups (`Setup`)
- Página "Suas Builds", com listagem dos setups salvos pelo usuário

## Stack

**Back-end**
- Python + Flask, com arquitetura em camadas (`controllers` → `services` → `models`)
- Flask-Login, para autenticação baseada em sessão (cookie httpOnly)
- SQLAlchemy, como ORM
- Werkzeug Security, para hash de senha

**Front-end**
- HTML5, CSS3 (variáveis nativas, sem framework ou pré-processador) e JavaScript (ES Modules, vanilla, sem framework)
- Font Awesome, para ícones
- Fontes próprias (Lexend e Poppins)
- View Transitions API, para transições de página nativas do navegador

## Próximos passos

- Implementar as rotas `PUT` e `DELETE` de usuário no back-end e conectar às telas de Configurações já prontas
- Iniciar o catálogo de peças e o formulário de recomendação de setup
- Documentar as rotas da API (ex: via Swagger/OpenAPI ou uma tabela neste README)

Este README será atualizado conforme o projeto avança.
