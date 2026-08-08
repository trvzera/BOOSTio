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

- Cadastro de usuário, com verificação de força de senha em tempo real, confirmação de senha e aceite de termos obrigatório
- Login, com exibição de erros vindos da API (ex: senha incorreta)
- Logout, encerrando a sessão via cookie
- Verificação de sessão ativa (rota `GET /auth/me`)
- Proteção de páginas restritas no front — usuário não autenticado é redirecionado ao tentar acessar Configurações
- Mostrar/ocultar senha em todos os campos de senha do site
- Menu de perfil dinâmico no header — mostra "Entrar / Criar conta" ou "Builds / Configurações / Sair", dependendo da sessão

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

## Estrutura do repositório
BOOSTio/
├── backend/
│ ├── controllers/ # Recebem requisições HTTP e chamam os services
│ │ ├── auth_controller.py
│ │ └── usuario_controller.py
│ ├── models/ # Entidades do banco de dados
│ │ ├── base.py
│ │ ├── fonte.py
│ │ ├── peca.py
│ │ ├── setup.py
│ │ └── usuario.py
│ ├── repositories/ # Acesso direto ao banco de dados
│ ├── services/
│ │ └── usuario_service/ # Regras de negócio (criar, entrar, atualizar, deletar, listar)
│ ├── app.py # Ponto de entrada da aplicação Flask
│ └── configs.py # Configurações do projeto
├── frontend/
│ ├── fonts/
│ ├── imgs/
│ ├── js/
│ │ ├── api/ # Funções de comunicação com a API (fetch)
│ │ ├── config.js # URL base da API
│ │ ├── scripts.js # Ponto de entrada, carregado em todas as páginas
│ │ ├── header.js # Menu de perfil e menu hambúrguer
│ │ ├── pagina-protegida.js # Guard de rotas autenticadas
│ │ ├── login.js
│ │ ├── signin.js
│ │ ├── configuracoes.js
│ │ └── services-carousel.js
│ ├── pages/ # login.html, signin.html, configuracoes.html
│ ├── styles/ # CSS organizado por módulo (about, header, home, services, utilitários...)
│ ├── video/
│ └── index.html
├── database/ # Banco de dados local (desenvolvimento)
├── instance/ # Instância do Flask (config e banco sensíveis, fora do versionamento)
├── BRAND/ # Identidade visual (logo, ícones)
├── ANOTAÇÕES/ # Rascunhos de design, tarefas e ideias do projeto
├── .env # Variáveis de ambiente (fora do versionamento)
├── requirements.txt # Dependências Python
└── test.py
## Próximos passos

- Implementar as rotas `PUT` e `DELETE` de usuário no back-end e conectar às telas de Configurações já prontas
- Iniciar o catálogo de peças e o formulário de recomendação de setup
- Documentar as rotas da API (ex: via Swagger/OpenAPI ou uma tabela neste README)

Este README será atualizado conforme o projeto avança.
