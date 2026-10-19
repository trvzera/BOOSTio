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

**Em desenvolvimento ativo.** Cadastro e login já estão conectados ao back-end. O editor, o catálogo, a comparação, a busca de melhorias, as configurações prontas, o budget e a importação/exportação estão disponíveis no front-end com dados demonstrativos e armazenamento local. As builds e preferências ainda não são sincronizadas com a conta. Preços atualizados, montagem automática pela LLM e resultados de benchmark aguardam suas integrações. A página [`frontend/testes.html`](frontend/testes.html) permanece como laboratório de interface.

## Funcionalidades

Os 20 requisitos do produto estão listados abaixo. **Conectado** indica front-end e back-end integrados; **local** significa que os dados ficam somente neste navegador; **protótipo** indica uma experiência de teste, ainda fora do fluxo principal. Um requisito **parcial** ainda não deve ser considerado concluído.

| Nº | Funcionalidade requerida | Situação atual |
| --- | --- | --- |
| 1 | Criar conta e fazer login | **Conectado:** cadastro, login, logout e sessão usam o back-end. |
| 2 | Cadastrar o setup atual | **Local:** o usuário pode informar peças próprias e definir uma build salva como setup atual; falta persistir esse vínculo na conta. |
| 3 | Pesquisar compatibilidade e peças | **Parcial:** há busca no catálogo e verificações de compatibilidade no front-end, com dados demonstrativos. |
| 4 | Montar o setup atual por meio de formulário | **Parcial:** acessível pelo botão “Criar pelo formulário” em “Minhas builds”; quatro etapas coletam objetivo, orçamento, peças existentes e conexão com a internet e levam os dados ao editor. A montagem automática pela LLM ainda não está integrada. |
| 5 | Salvar configurações de computadores | **Local:** alterações no editor e seleções pelo catálogo/ficha são salvas automaticamente neste navegador, com limite de três builds; ainda não há sincronização com a conta. |
| 6 | Excluir configurações salvas no perfil | **Local:** a exclusão funciona para builds salvas neste navegador. |
| 7 | Comparar configurações salvas | **Local:** comparação de duas ou três builds por modal em “Minhas builds”, com adição/remoção durante a comparação; desempenho depende da API de benchmark. |
| 8 | Compartilhar configurações por link | **Parcial:** uma build pública pode gerar um link com uma cópia dos seus dados; não há autorização ou revogação de links no servidor. |
| 9 | Buscar melhorias do setup | **Parcial:** CPU e GPU podem ser avaliadas juntas com budget combinado, compatibilidade e aplicação local após prévia; ganhos de desempenho e popularidade aguardam dados confiáveis. |
| 10 | Ver configurações prontas | **Local:** página “Builds prontas”, acessível pelo seletor junto a “Minhas builds”, com filtros, detalhes e “Usar como base” em cópia editável; falta curadoria e ofertas atualizadas no back-end. |
| 11 | Editar e modificar configurações salvas | **Local:** o editor altera componentes e detalhes das builds do navegador. |
| 12 | Ver o preço da peça pelo site | **Parcial:** preços demonstrativos e campos de ofertas por loja são exibidos; ainda não há cotações atualizadas de todas as lojas. |
| 13 | Ver informações de compatibilidade e consumo de energia da montagem | **Parcial:** o editor mostra validações e consumo estimado com os dados conhecidos; isso não substitui a conferência técnica de dados ausentes. |
| 14 | Adicionar periféricos ao setup e considerar seu custo | **Parcial:** periféricos entram no preço demonstrativo. O formulário coleta conexão, posse, velocidade e comprimento do cabo, sem preço manual. “Incluir rede” mostra a categoria “Wi-Fi / Rede”, no mesmo padrão das peças; cabos/adaptadores aguardam cadastro no catálogo. |
| 15 | Registrar o budget no perfil para compras e melhorias futuras | **Local:** configurações de perfil guardam budget e autorização de uso no range de novas montagens; cada build pode ajustar seu orçamento. Falta sincronização por conta. |
| 16 | Baixar a build em JSON e CSV | **Local:** exportação versionada inclui modelos, quantidades, peças próprias, nome, descrição, conexão e orçamento. |
| 17 | Alterar a visibilidade da build | **Local:** a interface alterna entre pública e privada, sem controle de acesso implementado no servidor. |
| 18 | Duplicar uma build | **Local:** uma cópia editável pode ser criada, respeitando o limite local de builds. |
| 19 | Definir nome e descrição da build | **Local:** ambos os campos podem ser editados e salvos no navegador. |
| 20 | Importar builds por arquivos CSV ou JSON | **Local:** lê JSON e CSV da BOOSTio, valida o arquivo e mostra uma prévia; a importação cria uma cópia privada e editável dentro da quota local. |

O fluxo de autenticação também inclui login com Google, recuperação de senha, verificação de e-mail e configurações de conta. Essas funções não substituem a integração pendente das builds com o back-end.

O botão **Testar build** está no editor e no menu dos cards, disponível com 100% das peças e sem erros de compatibilidade. O modal já apresenta as opções de resolução e qualidade; resultados de FPS dependem da API de benchmark. **Comprar build**, disponível somente dentro da build, permite consultar as lojas de cada peça e suas quantidades. A BOOSTio informa junto aos links e nos termos que não vende, entrega ou processa pagamentos; a compra ocorre no site da loja.

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
- Integrar a LLM ao formulário para sugerir builds com peças reais do catálogo e revalidar as respostas no servidor.
- Integrar a API de benchmark aos controles já disponíveis e alimentar as comparações de desempenho.
- Integrar builds, setup atual, comparação, melhorias e budget à conta e aos dados reais do back-end.
- Administrar a curadoria das configurações prontas no servidor e manter compatibilidade dos arquivos importados/exportados com os IDs da API.
- Documentar os contratos e as rotas da API.

O detalhamento das pendências é mantido localmente em `docs/pendencias-produto.md`, arquivo ignorado pelo Git. Ao concluir uma etapa, atualizar também a situação do requisito neste README.
