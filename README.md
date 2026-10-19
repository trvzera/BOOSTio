> **EN:** Repository for BOOSTio, my annual final course software project — a platform that helps people choose and build PC setups based on budget and goals. Auth flow (signup, login, logout, session-protected routes) is functional end-to-end; the PC-building core is still in development.
>
> *The rest of this README is in Brazilian Portuguese (pt-BR).*

---

<img src="./frontend/imgs/logoBOOSTio.gif">

# BOOSTio

Repositório do meu **projeto de software anual e final do curso**, desenvolvido no **Colégio Cotemig**. É aqui que o BOOSTio é desenvolvido, versionado e documentado ao longo do ano.

## Sobre o projeto

O BOOSTio é uma plataforma que simplifica a montagem de computadores. A ideia é ajudar o usuário a escolher as peças ideais com base no seu orçamento e objetivo (jogos, trabalho, uso cotidiano), permitindo também a seleção manual de componentes específicos, com o sistema integrando essas escolhas à sugestão final. O usuário pode salvar seus setups no perfil e compartilhar com outras pessoas.

## Status

**Em desenvolvimento ativo.** Cadastro e login já estão conectados ao back-end. O editor de builds, o catálogo e a página “Suas Builds” existem no front-end, mas usam um catálogo demonstrativo e armazenamento local no navegador; as builds ainda não são sincronizadas com a conta. Comparação, busca de melhorias, configurações prontas e budget têm protótipos em [`frontend/testes.html`](frontend/testes.html).

## Funcionalidades

Os 20 requisitos do produto estão listados abaixo. **Conectado** indica front-end e back-end integrados; **local** significa que os dados ficam somente neste navegador; **protótipo** indica uma experiência de teste, ainda fora do fluxo principal. Um requisito **parcial** ainda não deve ser considerado concluído.

| Nº | Funcionalidade requerida | Situação atual |
| --- | --- | --- |
| 1 | Criar conta e fazer login | **Conectado:** cadastro, login, logout e sessão usam o back-end. |
| 2 | Cadastrar o setup atual | **Parcial:** o usuário pode informar peças que já possui, mas ainda não há um setup atual persistido no perfil. |
| 3 | Pesquisar compatibilidade e peças | **Parcial:** há busca no catálogo e verificações de compatibilidade no front-end, com dados demonstrativos. |
| 4 | Montar o setup atual por meio de formulário | **Parcial:** o formulário coleta objetivo, orçamento e peças existentes e leva essas informações ao editor; não identifica nem monta automaticamente todos os modelos. |
| 5 | Salvar configurações de computadores | **Local:** é possível salvar builds no navegador, ainda não na conta do usuário. |
| 6 | Excluir configurações salvas no perfil | **Local:** a exclusão funciona para builds salvas neste navegador. |
| 7 | Comparar configurações salvas | **Protótipo:** há um comparador de duas ou três builds na página de testes; falta integrá-lo à página “Suas Builds”. |
| 8 | Compartilhar configurações por link | **Parcial:** uma build pública pode gerar um link com uma cópia dos seus dados; não há autorização ou revogação de links no servidor. |
| 9 | Buscar melhorias do setup | **Protótipo:** a página de testes sugere trocas compatíveis dentro de um budget, sem modificar a build salva. |
| 10 | Ver configurações prontas | **Protótipo:** há exemplos na página de testes; falta uma vitrine de builds curadas com a opção “Usar como base”. |
| 11 | Editar e modificar configurações salvas | **Local:** o editor altera componentes e detalhes das builds do navegador. |
| 12 | Ver o preço da peça pelo site | **Parcial:** preços demonstrativos e campos de ofertas por loja são exibidos; ainda não há cotações atualizadas de todas as lojas. |
| 13 | Ver informações de compatibilidade e consumo de energia da montagem | **Parcial:** o editor mostra validações e consumo estimado com os dados conhecidos; isso não substitui a conferência técnica de dados ausentes. |
| 14 | Adicionar periféricos ao setup e considerar seu custo | **Local:** o editor permite incluir periféricos opcionais e somá-los ao preço demonstrativo. |
| 15 | Registrar o budget no perfil para compras e melhorias futuras | **Protótipo:** valor e preferência de uso em novas builds existem apenas na sessão da página de testes. |
| 16 | Baixar a build em JSON e CSV | **Parcial:** o JSON pode ser baixado; o CSV atual precisa incluir modelos, quantidades e demais dados das peças. |
| 17 | Alterar a visibilidade da build | **Local:** a interface alterna entre pública e privada, sem controle de acesso implementado no servidor. |
| 18 | Duplicar uma build | **Local:** uma cópia editável pode ser criada, respeitando o limite local de builds. |
| 19 | Definir nome e descrição da build | **Local:** ambos os campos podem ser editados e salvos no navegador. |
| 20 | Importar builds por arquivos CSV ou JSON | **Pendente:** o botão existe, mas ainda não lê nem valida arquivos. |

O fluxo de autenticação também inclui login com Google, recuperação de senha, verificação de e-mail e configurações de conta. Essas funções não substituem a integração pendente das builds com o back-end.

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

- Persistir builds por usuário no back-end, com componentes múltiplos e validação no servidor.
- Integrar o catálogo e o monitoramento de preços; até lá, preços demonstrativos não devem ser apresentados como cotações atuais.
- Levar os protótipos de comparação, melhorias e budget para o fluxo principal após a integração necessária.
- Criar a vitrine de configurações prontas e implementar importação e exportação completas.
- Documentar os contratos e as rotas da API.

Outras decisões e dependências estão em [`docs/pendencias-produto.md`](docs/pendencias-produto.md). O README será atualizado conforme o projeto avança.
