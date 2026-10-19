> **EN:** Repository for BOOSTio, my annual final course software project — a platform that helps people choose and build PC setups based on budget and goals. Auth flow (signup, login, logout, session-protected routes) is functional end-to-end; the PC-building core is still in development.
>
> *The rest of this README is in Brazilian Portuguese (pt-BR).*

---

<img src="./frontend/imgs/logoBOOSTio.gif">

# BOOSTio

Repositório do meu **projeto de software anual e final do curso**, desenvolvido no **Colégio Cotemig**. É aqui que o BOOSTio é desenvolvido, versionado e documentado ao longo do ano.

## Sobre o projeto

O BOOSTio é uma plataforma que simplifica a montagem de computadores. A ideia é ajudar o usuário a escolher as peças ideais com base no seu orçamento e objetivo (jogos, trabalho, uso cotidiano), permitindo também a seleção manual de componentes específicos, com o sistema integrando essas escolhas à sugestão final. O usuário pode salvar seus setups no perfil e compartilhar com outras pessoas.

A página [Sobre nós](frontend/pages/sobre.html) apresenta a proposta da BOOSTio, suas ferramentas e o estágio de desenvolvimento da plataforma.

## Status

**Em desenvolvimento ativo.** Cadastro, login e consulta de desempenho esperado já usam o back-end. O editor, o catálogo, a comparação, a busca de melhorias, as configurações prontas, o budget e a importação/exportação estão disponíveis no front-end com dados demonstrativos e armazenamento local. As builds e preferências ainda não são sincronizadas com a conta. Preços atualizados e montagem automática pela LLM aguardam integração. A página [`frontend/testes.html`](frontend/testes.html) permanece como laboratório de interface.

## Funcionalidades

Os 20 requisitos do produto estão listados abaixo. **Conectado** indica front-end e back-end integrados; **local** significa que os dados ficam somente neste navegador; **protótipo** indica uma experiência de teste, ainda fora do fluxo principal. Um requisito **parcial** ainda não deve ser considerado concluído.

| Nº | Funcionalidade requerida | Situação atual |
| --- | --- | --- |
| 1 | Criar conta e fazer login | **Conectado:** cadastro, login, logout e sessão usam o back-end. |
| 2 | Cadastrar o setup atual | **Local:** o usuário pode informar peças próprias e definir uma build salva como setup atual; falta persistir esse vínculo na conta. |
| 3 | Pesquisar compatibilidade e peças | **Parcial:** há busca no catálogo e verificações de compatibilidade no front-end, com dados demonstrativos. |
| 4 | Montar o setup atual por meio de formulário | **Parcial:** “Criar build” em “Minhas builds” abre a escolha entre montagem manual e formulário inteligente; quatro etapas coletam objetivo, orçamento, peças existentes e conexão com a internet e levam os dados ao editor. A montagem automática pela LLM ainda não está integrada. |
| 5 | Salvar configurações de computadores | **Local:** alterações no editor e seleções pelo catálogo/ficha são salvas automaticamente neste navegador, com limite de três builds; ainda não há sincronização com a conta. |
| 6 | Excluir configurações salvas no perfil | **Local:** a exclusão funciona para builds salvas neste navegador. |
| 7 | Comparar configurações salvas | **Local:** comparação de duas ou três builds por modal em “Minhas builds”, com adição/remoção durante a comparação; desempenho depende da API de benchmark. |
| 8 | Compartilhar configurações por link | **Parcial:** uma build pública pode gerar um link com uma cópia dos seus dados; não há autorização ou revogação de links no servidor. |
| 9 | Buscar melhorias do setup | **Parcial:** CPU e GPU podem ser avaliadas juntas com budget combinado, compatibilidade e aplicação local após prévia; ganhos de desempenho e popularidade aguardam dados confiáveis. |
| 10 | Ver configurações prontas | **Local:** página “Builds prontas”, acessível pelo seletor junto a “Minhas builds”, com filtros, detalhes e “Usar como base” em cópia editável; falta curadoria e ofertas atualizadas no back-end. |
| 11 | Editar e modificar configurações salvas | **Local:** o editor altera componentes e detalhes das builds do navegador. |
| 12 | Ver o preço da peça pelo site | **Parcial:** preços demonstrativos e campos de ofertas por loja são exibidos; ainda não há cotações atualizadas de todas as lojas. |
| 13 | Ver informações de compatibilidade e consumo de energia da montagem | **Parcial:** o editor valida formato da placa-mãe, comprimento da GPU, altura do air cooler, radiadores e fans quando há dados, além do consumo estimado. Falta revalidar no Python e completar o encaixe físico por posição, incluindo interferências de radiador/GPU/RAM, fonte e baias. Medidas ausentes não confirmam compatibilidade. |
| 14 | Adicionar periféricos ao setup e considerar seu custo | **Parcial:** periféricos entram no preço demonstrativo. O formulário coleta conexão, posse, velocidade e comprimento do cabo, sem preço manual. “Incluir rede” mostra a categoria “Wi-Fi / Rede”, no mesmo padrão das peças; cabos/adaptadores aguardam cadastro no catálogo. |
| 15 | Registrar o budget no perfil para compras e melhorias futuras | **Local:** configurações de perfil guardam budget e autorização de uso no range de novas montagens; cada build pode ajustar seu orçamento. Falta sincronização por conta. |
| 16 | Baixar a build em JSON e CSV | **Local:** exportação versionada inclui modelos, quantidades, peças próprias, nome, descrição, conexão e orçamento. |
| 17 | Alterar a visibilidade da build | **Local:** a interface alterna entre pública e privada, sem controle de acesso implementado no servidor. |
| 18 | Duplicar uma build | **Local:** uma cópia editável pode ser criada, respeitando o limite local de builds. |
| 19 | Definir nome e descrição da build | **Local:** ambos os campos podem ser editados e salvos no navegador. |
| 20 | Importar builds por arquivos CSV ou JSON | **Local:** lê JSON e CSV da BOOSTio, valida o arquivo e mostra uma prévia; a importação cria uma cópia privada e editável dentro da quota local. |

O fluxo de autenticação também inclui login com Google, recuperação de senha, verificação de e-mail e configurações de conta. Essas funções não substituem a integração pendente das builds com o back-end.

O botão **Testar build** está no editor e no menu dos cards, disponível com 100% das peças e sem erros de compatibilidade. O modal consulta a FPSHQ pelo backend autenticado para os modelos com correspondência cadastrada, com jogo, resolução, qualidade, FPS médio e 1% low quando disponível. A comparação de ajustes já fica visível e usa a matriz recebida, sem novas consultas. Peças não mapeadas não são substituídas por modelos parecidos. **Comprar build**, disponível somente dentro da build, permite consultar as lojas de cada peça e suas quantidades. A BOOSTio informa junto aos links e nos termos que não vende, entrega ou processa pagamentos; a compra ocorre no site da loja.

**Desempenho esperado** usa `GET /benchmark/fps` e `GET /benchmark/jogos`, seguindo `controllers → services` e exigindo sessão. O Flask valida os parâmetros e a combinação retornada, mantém cache em memória por uma hora e trata limites, ausência de dados e indisponibilidade do provedor. Fonte e licença continuam visíveis. O laboratório também usa essas rotas, com a combinação de referência Ryzen 5 5600 + RTX 3060 e login necessário para consultar. Não é uma medição da máquina nem uma aprovação dos requisitos do jogo: RAM e requisitos mínimos/recomendados ainda precisam de validação separada. O cache e os limites são por processo; múltiplos workers exigirão um armazenamento compartilhado. A exigência de login para criar builds permanece pendente nas demais páginas locais.

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
- Ampliar os mapeamentos exatos de hardware, compartilhar cache/limites entre workers e alimentar as comparações de desempenho com condições equivalentes. A consulta individual de benchmark já está integrada ao backend.
- Validar requisitos mínimos/recomendados dos jogos e RAM antes de aprovar o desempenho esperado; distinguir hardware abaixo do mínimo, modelo sem dados e falha do provedor, sem interpretar FPS previsto como garantia de execução.
- Integrar builds, setup atual, comparação, melhorias e budget à conta e aos dados reais do back-end.
- Administrar a curadoria das configurações prontas no servidor e manter compatibilidade dos arquivos importados/exportados com os IDs da API.
- Documentar os contratos e as rotas da API.

O detalhamento das pendências é mantido localmente em `docs/pendencias-produto.md`, arquivo ignorado pelo Git. Ao concluir uma etapa, atualizar também a situação do requisito neste README.
