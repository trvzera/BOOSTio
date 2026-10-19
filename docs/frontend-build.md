# Editor de build e efeitos de scroll

Abra pelo Live Server:

- `frontend/pages/configuracao-build.html`: editor vazio.
- `frontend/pages/configuracao-build.html?id=build-demo-1`: configuração de exemplo.
- `frontend/pages/pecas.html?categoria=processador`: catálogo por categoria.
- `frontend/pages/peca.html?id=SEED-CPU-02`: ficha técnica e lojas.
- `frontend/pages/configuracoes-prontas.html`: modelos demonstrativos e cópia editável.
- `frontend/pages/sobre.html`: apresentação da BOOSTio, proposta, ferramentas e estágio do projeto.
- `frontend/testes.html`: demonstração que usa o mesmo menu hamburger das demais páginas.

O catálogo demonstrativo é uma cópia das 750 peças de
`backend/services/peca_service/popular_pecas_service.py`, criada em 28/09/2026.
Os preços da seed são gerados para demonstração, não cotações atuais.
Não foram executados o Flask, a seed nem o scraper para montar essa cópia.
Quando a seed mudar, o JSON não se atualiza sozinho.

## Como funciona o blur no scroll

`frontend/js/components/scroll-reveal.js` usa um IntersectionObserver.
Quando 12% do elemento passa a ser visível, ele recebe `is-visible`.
O `rootMargin: "60px 0px -32px 0px"` ajusta a área em que a entrada é detectada.
A classe é retirada ao sair, portanto a animação pode repetir.

O CSS em `frontend/styles/componentes/scroll-reveal.css` controla:

- `--reveal-distance: 42px`: deslocamento vertical inicial.
- `--reveal-blur: 6px`: desfoque inicial.
- `--reveal-scale: 0.985`: escala inicial.
- `--reveal-duration: 0.75s`: duração de opacidade e blur.
- `--reveal-move-duration: 0.9s`: duração do movimento.

Para animar um novo elemento, adicione `data-reveal` ao HTML.
Para atrasar sua entrada, use `data-reveal-delay="80ms"`.
Os cards de serviço usam 0, 80 e 160 ms.
Para revelar só uma vez, dentro do callback mantenha a classe e chame
`observer.unobserve(target)` quando `isIntersecting` for verdadeiro.

É uma animação disparada pela visibilidade; o blur não varia continuamente
com a velocidade do scroll. As opções de movimento reduzido do sistema são respeitadas.
Os conteúdos continuam visíveis se o JavaScript ou o observer não estiverem disponíveis.
Na home, o reveal é aplicado ao card inteiro para manter texto e fundo juntos.
O footer e os cards/sections das demais páginas recebem o mesmo reveal automaticamente
após o loading. Um MutationObserver registra também cards criados pelo JavaScript,
sem duplicar observers; a área principal da home continua sem blur inicial.

## Estado local e pontos de integração

`js/build/catalogo.js` centraliza o carregamento do catálogo e as informações das lojas.
A futura API pode substituir `carregarCatalogo()`, mantendo o mesmo formato:
id estável, categoria, imagem, preço, consumo e campos técnicos da peça.
O campo `imagem` já é suportado; ausências exibem um placeholder.

`js/build/estado.js` guarda os rascunhos e a lista demonstrativa de builds no localStorage.
Salvar no perfil nesta versão significa salvar neste navegador. Não há gravação na conta
do Flask nem sincronização entre dispositivos. Dados do formulário entram como peças
próprias sem preço; o usuário precisa selecionar o modelo para a validação técnica.
`js/build/autosalvar.js` grava cada alteração válida na lista local, inclusive seleções
do catálogo e da ficha da peça. Abrir o editor sem editar não cria uma build salva.
Nome vazio ou quota completa preservam somente o rascunho e exibem a pendência;
build trancada não pode ser sobrescrita. O botão **Salvar build e voltar** continua
disponível para concluir e retornar à lista, sem ser necessário para persistir cada edição.

Links compartilhados carregam a configuração por IDs de catálogo e quantidades, e abrem
uma cópia. A visibilidade e a tranca são controles locais de interface, não autorização
do servidor. Links já enviados não podem ser revogados por esse protótipo.

RAM é uma lista em `componentes.memoria_ram`; o formato antigo com um objeto é migrado
automaticamente. Cada entrada tem `id` e `quantidade` de kits. Todos os módulos de todos
os kits contam nos slots e na capacidade máxima da placa-mãe. Novos modelos precisam
ter o mesmo DDR e frequência; misturar marcas/modelos gera aviso de estabilidade.
Duplicação e remoção são individuais. SSD, HD e fan também são listas de modelos e
quantidades; objetos antigos são migrados sem perder os dados. Para trocar outras peças,
remova a atual primeiro. A duplicação soma preço, consumo e capacidade; diminuir libera
conexões sem remover os demais modelos. Rascunhos, JSON e links preservam quantidades.

`js/build/compatibilidade.js` verifica socket, DDR, slots, capacidade, formato do gabinete,
altura do air cooler, comprimento da GPU, radiadores, diâmetro/quantidade de fans,
slots M.2, portas SATA compartilhadas por HD/SSD e potência da fonte.
Dados genéricos como “Intel/AMD” produzem dica para conferir o socket no fabricante.
BIOS, conectores, disposição dos encaixes e disponibilidade não são plenamente validados.
Medidas ausentes produzem dicas azuis, nunca um encaixe confirmado. Novas unidades de discos
exigem uma placa identificada com limite conhecido; não se presume que uma placa tenha
quatro portas SATA. Trocar a placa ou o gabinete também revalida as peças já selecionadas.
O consumo exclui monitor e periféricos externos e é apenas uma estimativa da seed.
Não há potência recomendada. Fonte abaixo do consumo é erro; igual ao consumo gera aviso
de ausência de margem. Fans são obrigatórias. Air cooler e water cooler ficam em uma categoria;
cooler separado é obrigatório somente quando o processador não inclui cooler.
Periféricos são opcionais e podem ser ativados pelo checkbox do editor.
O checkbox mantém o mesmo elemento e a mesma instância Lottie durante a atualização
dos cards, permitindo concluir a animação nos dois sentidos.
SSD e HD aparecem juntos em **SSD / HD**, um grupo obrigatório: basta um dos dois.
As peças continuam armazenadas como `ssd` e `hd`, preservando rascunhos existentes.
O contador de armazenamento mostra unidades de SSD/HD e conexões M.2/SATA ocupadas.
Placa de vídeo é obrigatória quando o processador selecionado não tem vídeo integrado;
enquanto faltar, o status da build permanece incompleto.
O catálogo é filtrado automaticamente pelas verificações quando a build já possui peças.
O botão da página de produto também revalida a seleção antes de adicionar.

### Campos técnicos para a futura API

Em `js/build/hardware.js`, campos numéricos nulos são desconhecidos, não zero.

- Placa-mãe: `quantidade_slots_m2`, `quantidade_portas_sata`,
  `quantidade_slots_m2_sata` e `portas_sata_desativadas_por_m2_sata`.
- GPU: `comprimento_mm`; air cooler: `altura_mm` (o antigo `dimensoes` só serve se numérico).
- Gabinete: `tamanho_max_gpu_mm`, `tamanho_max_cooler_mm`,
  `radiadores_suportados_mm: [120, 240, 360]`, `tamanhos_fan_suportados_mm: [120, 140]`,
  `quantidade_max_fans` e `fans_inclusos`.
- Water cooler: `tamanho_radiador_mm`, `quantidade_fans`; fan: `tamanho_mm`, `quantidade`
  (unidades físicas por kit, multiplicadas pela quantidade de kits na build).

Esses arrays são exemplos de contrato, não medidas de um gabinete real. Radiador de
360 mm precisa estar listado nos tamanhos suportados. Três fans de 120 mm continuam
três unidades de 120 mm, não uma fan de 360 mm. A contagem considera as fans inclusas
e as do radiador como instaladas; modelos com distribuição não informada precisam
de conferência para encaixes compartilhados. Não existe um seletor de posição física ainda.
As medidas de GPU e os encaixes de radiador/fans ainda faltam na seed atual.

O complemento exclusivo do catálogo demonstrativo usa as fichas de
[ASUS PRIME A520M-K](https://www.asus.com/motherboards-components/motherboards/prime/prime-a520m-k/techspec/),
[GIGABYTE B550M DS3H rev. 1.0/1.1/1.2/1.3](https://www.gigabyte.com/Motherboard/B550M-DS3H-rev-10-11-12-13/sp)
e [MSI PRO B760M-P](https://us.msi.com/Motherboard/PRO-B760M-P/Specification).
Esses três modelos têm quatro portas SATA; as quantidades M.2 são respectivamente
uma, duas e duas. Na MSI, M.2 SATA desativa SATA5. Os links de lojas da seed podem
apontar para outras variantes; este complemento usa o nome/modelo da demonstração,
não o anúncio, e não deve ser aplicado a outras revisões sem conferência.

Nenhum arquivo Python foi alterado. O backend atual **não** executa estas validações
nem o limite de três builds; o modelo possui quantidades, mas não há rotas de builds
registradas em `app.py`. O front continua com catálogo demonstrativo e localStorage.
Ao integrar, o servidor deve revalidar estoque, compatibilidade, medidas, quantidades,
tranca, visibilidade, propriedade da build e quota. O modelo atual também só armazena
um ID por categoria; vários modelos de RAM/SSD/HD/fan precisam de um contrato adequado.

KaBuM usa os links já existentes. Pichau e Mercado Livre abrem buscas, claramente rotuladas,
até haver ofertas diretas cadastradas. Não são inventados preços de cada loja.
Ofertas reais são independentes do preço demonstrativo da seed:

```json
{
  "ofertas": [
    {"loja": "kabum", "preco": 1200, "url": "https://www.kabum.com.br/produto/ID", "atualizadoEm": "2026-09-28T12:00:00Z"},
    {"loja": "pichau", "preco": 1190, "url": "https://www.pichau.com.br/produto"},
    {"loja": "mercadolivre", "preco": 1220, "url": "https://produto.mercadolivre.com.br/MLB-ID"}
  ]
}
```

Esses valores são apenas exemplos do contrato, não cotações. Sem o campo `ofertas`,
cada loja exibe “Preço ainda não cadastrado”. Os arquivos locais em `frontend/svgs` são:
`kabum-logo.svg`, `pichau.png`, `mercado-livre-87.svg`. As marcas ficam em escala de cinza;
se uma imagem falhar, o nome da loja continua visível.

## Sistema visual e transições

`styles/utilitarios/tipografia.css` foi restaurado integralmente do commit
[`789d641`](https://github.com/trvzera/BOOSTio/commit/789d6418e1a5118890e4f5675204e4cdaac3219d),
confirmado como o último commit de `main`. Também foram restauradas as regras
tipográficas responsivas e removidas as sobrescritas globais de pesos e entrelinhas.
As classes `font-1-*` usam Lexend e `font-2-*` usam Poppins. Os tokens dos componentes
novos ficam em `ui-system.css` e não substituem essa escala nas páginas existentes.
`cores.css` define
`--status-success`, `--status-warning` e `--status-error`; status também têm rótulos textuais.
Botões compartilham formato capsule, altura mínima, hover discreto e foco visível.
`componentes/ui-system.css` concilia os estilos antigos de cada página com esses tokens.

`js/components/ui.js` inicializa ícones via o controlador Lottie existente,
reproduz no hover/foco e reverte na saída. Plus, login rotacionado 90°, trash e cart
têm alternativas estáticas. Checkbox, hamburger e chevron refletem o estado do controle.
O `arrow.json` original aponta na diagonal: a rotação de 45° aponta para a direita,
225° para a esquerda, 0° mantém a diagonal externa e −45° aponta para cima.
Ícones de elementos removidos são destruídos; falhas nas animações não bloqueiam os controles.
O mesmo módulo adiciona logos sociais e tooltips a botões desabilitados, inclusive
em conteúdo dinâmico. Defina `data-disabled-reason` para informar um motivo contextual;
uma âncora focável permite ler a explicação pelo teclado sem habilitar a ação.

`js/pages/loading.js` usa `sessionStorage["boostio:visita-iniciada"]`, não a conta.
Primeira visita da aba/sessão e toda entrada na home usam vídeo. A home sempre mantém 1×.
As demais páginas mostram um loading curto (linha animada sobre preto), espera mínima
de 320 ms e fade de 600 ms. O fluxo editor → catálogo → peça usa espera de 320 ms e
fade de 460 ms; com catálogo pronto, 160 ms e 360 ms. Links internos e botões desse fluxo
têm também fade preto de saída de 260 ms, sem afetar links externos ou âncoras da mesma página.
Retornos pelo histórico/bfcache reapresentam a transição curta; o fluxo de componentes
reabre o documento para ler o rascunho atualizado. Retornar à home recarrega o loading
completo. A tela curta nunca depende de o vídeo estar disponível.
O formulário tem espera mínima de 800 ms e fade de 700 ms, inclusive nas visitas seguintes.
A primeira visita continua usando o vídeo; movimento reduzido ignora a espera artificial.
Nesse fluxo, um vídeo inicial pode acelerar para 2.2× quando os dados já estiverem prontos;
as outras páginas não alteram sua velocidade.
Configurações aguardam a requisição inicial de perfil; catálogo/editor aguardam o JSON.
O vídeo não simula porcentagem de rede: a mudança de velocidade depende de tarefas reais.
Há limites de espera para evitar tela presa e suporte a movimento reduzido.
Para novas tarefas iniciais, use `acompanharCarregamento(promise)` de `page-loading.js`.
Ao salvar a build, a interface redireciona a `builds.html`, ainda com persistência local.

Depois da retirada do loading, `js/components/page-entry.js` anima os primeiros textos
visíveis, sem exigir scroll, **exceto na home**, onde essa entrada foi desativada.
O efeito durante a rolagem das outras seções da home continua independente.
Em `styles/componentes/page-entry.css`, altere o blur de
8px, a distância de 18px e a duração de 0.7s. A animação respeita movimento reduzido.
O overlay perde a captura de cliques ao começar o fade e é removido também por timeout,
sem depender exclusivamente de `transitionend`.

## Navegação e interatividade

`pages/sobre.html` substitui a antiga página de desenvolvedores. Apresenta a proposta
da BOOSTio, ferramentas de planejamento, origem do projeto e limites atuais, sem
perfis individuais ou promessas de integrações já concluídas. Os footers apontam para
**Conheça a BOOSTio**; a página usa navegação, loading, fontes, glass e reveal compartilhados.
`paginas/sobre.css` e `responsividades/r-sobre.css` cuidam do layout específico.

`js/header.js` renderiza a logo de 100px no topo esquerdo e o perfil no topo direito.
O perfil permanece disponível antes e depois do login; os seus links não usam setas.
O botão usa `profile.json` no tamanho original de 60px. Hover e foco abrem o dropdown;
clicar fixa o menu aberto. Uma ponte entre botão e painel evita fechar durante o movimento
do cursor, e Escape, clique fora ou um segundo clique fecham o menu.
O hamburger flutuante fica oculto até a autenticação. Em `testes.html`, o atributo
`data-menu-preview` permite verificar o hamburger mesmo sem login.
Os painéis usam glass, itens compactos, `inert` quando fechados, Escape e clique fora
para fechar. Abrir um painel fecha o outro. Navegações usam páginas; na home o menu
inclui também Sobre, Como funciona e Começar montagem, ligados às respectivas sections.
O editor tem um botão direto para voltar a Minhas builds, sem depender do histórico.
Minhas builds e Builds prontas compartilham um seletor de páginas com `aria-current`;
o comparador aparece apenas em Minhas builds. Os cards não têm ação de compra.
Em Minhas builds, **Criar build** abre um modal para escolher entre montagem manual
e formulário inteligente. A escolha fecha o modal antes da transição compartilhada.
O botão fica bloqueado quando a quota local de três builds está completa.

Nos cards de builds, o progresso permanece azul e a linha inferior exibe apenas
privacidade e data. Builds trancadas mostram um cadeado ao lado do nome e não
podem ser editadas nem deletadas até serem destrancadas.
A barra à esquerda do título fica azul sem pendências, amarela com aviso/incompletude
e vermelha com erro. Hover, foco ou toque mostram a lista de pendências; Escape fecha.
O editor usa o mesmo indicador. Criar, duplicar e importar ficam bloqueados na quota
completa, inclusive com uma explicação acessível. Importar lê JSON e CSV da BOOSTio,
valida o arquivo e abre uma prévia antes de criar uma cópia privada e destrancada.
O salvamento ainda é local, sem integração com o servidor.

### Recursos de planejamento e arquivos

`js/build/rede.js` mantém conexão, posse, velocidade e comprimento do cabo na quarta
etapa do formulário, sem campo de preço. `custoPrevisto` de arquivos v1 é aceito,
normalizado para `null` e nunca somado. Na build, **Incluir rede** mostra a categoria
**Wi-Fi / Rede** com adicionar/remover igual às outras peças. Os componentes usam
`cabo_rede` e `adaptador_wifi`; `incluirRede` e as respostas do formulário sobrevivem
à edição, duplicação, links e JSON/CSV. O catálogo demonstrativo ainda não possui
esses produtos e mostra um estado vazio explícito, sem inventar preço ou modelo.
Somente o preço de produtos cadastrados entra no total. Rede é opcional e não muda
a conclusão ou o consumo estimado do PC; conferir interfaces/roteador continua necessário.

O dropdown **Nome, descrição e orçamento** usa `components/animated-details.js`
para animar as duas direções e respeita movimento reduzido. Os Lotties `circledot`,
`magnifying` e `magic` usam o controlador compartilhado com hover/foco e reversão.
Na build definida como setup atual, circledot inicia no último frame e inverte
hover/saída; `aria-checked` informa o estado, atualizado ao escolher outra build.
O botão da principal mostra **Remover como setup atual** e desmarca a preferência,
sem excluir a build. As demais mostram **Definir como setup atual**, com ícone normal.
O menu de três pontos abre para baixo, ajustando a rolagem ao abrir se faltar espaço,
sem cobrir os controles flutuantes; sua lista tem rolagem própria e glass mais forte.

`js/build/planejamento.js` guarda budget, preferência de uso e ID de setup atual
neste navegador. O formulário preenche o range quando a preferência está ativa;
`build.orcamento` permite ajustar o limite sem alterar o budget registrado.
Sincronização e separação por conta continuam dependentes do backend.

`js/build/arquivos.js` exporta JSON e CSV versionados (`boostio-build`, versão 1).
O CSV inclui metadados e uma linha por modelo com categoria, ID ou peça própria,
quantidade e nome. Arquivos têm limite de 1 MiB; a importação valida estrutura,
quantidades e IDs, sem confiar em preços/consumo enviados no arquivo. Gera novo UUID,
preserva planejamento e nunca reutiliza a visibilidade pública ou tranca da origem.

`js/build/comparacao.js` abre o comparador da lista real de builds locais.
`js/build/melhorias.js` monta uma prévia de trocas CPU/GPU dentro de um budget combinado
e somente altera a build após confirmação. Rankings de desempenho e de vendas aguardam
dados externos. `js/build/modelos.js` mantém exemplos versionados para a vitrine.

`js/build/acoes-build.js` compartilha os modais de compra e benchmark e o aviso sobre
lojas terceiras. O benchmark abre apenas com 100% das peças e sem erros; permite
escolher jogo, resolução e preset e consulta FPS pelo backend para modelos mapeados.
Comprar build, somente no editor, lista as lojas
e quantidades de cada peça, sem checkout nem abertura automática de múltiplas abas.

### Consulta de FPS — backend e interface compartilhada

Contrato atual conferido no [OpenAPI](https://fpshq.com/openapi.json), na
[documentação pública](https://fpshq.com/pt/api/) e em chamadas reais em 19/10/2026.
A rota é `GET /api/public/v1/fps`, com `game`, `gpu`, `cpu`, `res` e `preset`.
Não usar o contrato antigo `/api/v1/`. Os presets são `low`, `medium`, `high`, `ultra`;
resoluções: `1080p`, `1440p`, `4k`. Retorna `fps`, `low1`, `source` (`measured`/`model`),
`basis` (`measured`/`aggregate`/`model`), `confidence` e matriz 3×4.
Ausências e intervalos nulos não são zero. `verdict` tem base 1080p High, não se aplica
automaticamente à seleção do usuário. A origem de cada célula da matriz não é individualizada.

`GET /api/public/v1/games?q=<texto>` busca de 2 a 60 caracteres e retorna até dez jogos.
Foram encontrados Valorant, Counter-Strike 2 (`cs2`), Fortnite, Cyberpunk 2077 e Forza
Horizon 5, entre outros. Encontrar no catálogo não garante FPS para toda combinação.
Os cinco jogos padrão do laboratório, nesta ordem, são Valorant, Counter-Strike 2,
Fortnite, Cyberpunk 2077 e Red Dead Redemption 2. O último foi confirmado por consulta
direta a `/fps` com `game=red-dead-redemption-2`, apesar de a busca pelo nome completo
ter retornado lista vazia. Outros jogos continuam acessíveis pela busca.
Não há catálogo REST de CPUs listado neste OpenAPI; mapear componentes exatos sem
inventar slugs nem usar uma GPU dedicada como substituta de vídeo integrado.

O laboratório `testes.html` carrega `js/pages/test-benchmark.js`, que inicializa
`js/benchmark/interface.js` com a combinação fixa Ryzen 5 5600 + RTX 3060. O mesmo
controlador é usado pelo modal real de `js/build/acoes-build.js`, com as peças da build.
Ambos chamam `js/api/benchmark/consultarBenchmark.js` → `fetchComErro`, com cookies de
sessão. O cliente direto antigo em `js/experimentos/fpshq.js` não é carregado por essas
interfaces. Nada é consultado automaticamente ao abrir a página ou o modal.
Nas verificações houve respostas lentas/timeouts intermitentes; o cliente encerra a
espera após 20 segundos, sem retentativa automática nem FPS fictício. A resposta real
também foi recebida por fetch no navegador; isso não garante disponibilidade contínua.
Chamada real de Valorant, 1080p/High: 288 FPS, 1% low 261, source/basis `measured`.
São valores retornados naquele momento pelo provedor, não medidos pela BOOSTio e
não fixados como resultados no código. A combinação com CPU inexistente retornou 404.

O provedor declara uso gratuito sem chave, CORS e CC BY 4.0 com atribuição, além de
60 consultas/minuto e 10 mil/dia por IP. Antes de produção, centralizar cache e limites
no backend, validar cobertura/precisão e integrar as builds da conta. RAM, consumo
instantâneo e rede não são parâmetros desse endpoint; os avisos distinguem latência
de FPS. O recurso se chama **Desempenho esperado** e não promete medição ou precisão.
O modal agora consulta o Flask autenticado, que acessa a FPSHQ. As rotas e os serviços
novos estão documentados abaixo; não há alteração de modelos ou migração de banco.
No laboratório, a prévia da montagem fica recolhida e a área principal mostra apenas
hardware de referência, jogo, resolução e qualidade. A busca apresenta resultados
para seleção explícita, sem escolher automaticamente o primeiro. O aviso começa
oculto e aparece após selecionar o jogo ou receber seu resultado; detalhes de RAM,
rede e demais limitações ficam em uma seção expansível, sem remover as ressalvas.
`js/benchmark/view.js` monta a visualização compacta: **Comparar ajustes** fica visível e
permite alternar a qualidade e ver as três resoluções da matriz já recebida, sem
requisitar a API nem substituir os FPS do resultado principal. **Sobre os dados**
reúne origem, definição de 1% low e data. Cotas operacionais ficam apenas nesta
documentação, não no texto do resultado. Fonte e licença continuam visíveis.

O seletor **Interface de teste** alterna **Cards** (métricas lado a lado), **Painel**
(ajustes à esquerda e resultado em destaque à direita no desktop) e **Compacto**
(controles em uma faixa e métricas em linhas). As três variantes usam o mesmo DOM,
cliente e resposta: mudar o visual preserva jogo, ajustes, comparação aberta e dados,
sem consumir outra consulta. Em telas menores, o painel passa a uma coluna.
O seletor de variantes continua exclusivo do laboratório. O modal real usa Cards,
com métricas menores, controles mais curtos e sem repetição de avisos operacionais.

Os menus expansíveis usam `js/components/animated-details.js`: o JS mede a altura
natural e anima abertura/fechamento com Web Animations, mantendo `aria-expanded`.
Em `styles/componentes/benchmark.css`, `.fpshq-disclosure` configura `--details-duration`
(número em milissegundos, padrão do laboratório: `320`) e `--details-easing`.
O CSS também cuida da seta, cores e recorte durante a transição. Movimento reduzido
ou ausência de suporte desativa a animação sem impedir a navegação. Menus inseridos
com o resultado são inicializados após renderizar; seleção da busca fecha o menu
pelo mesmo controlador para não deixar animações pendentes reabrirem o conteúdo.

#### Rotas Flask e serviços

`backend/controllers/benchmark_controller.py` registra o Blueprint `/benchmark`,
conectado em `app.py`, com `@login_required` e erro 401 em JSON. Não aceita URL externa,
ID de usuário fornecido pelo cliente, parâmetros desconhecidos ou repetidos.

- `GET /benchmark/fps?game=valorant&cpu=ryzen-5-5600&gpu=rtx-3060&res=1080p&preset=high`
  → `ConsultarBenchmarkService.executar(dados, current_user.id)`.
- `GET /benchmark/jogos?q=Valorant`
  → `BuscarJogosBenchmarkService.executar(dados, current_user.id)`.

Os serviços ficam em `services/benchmark_service/`, seguindo o padrão existente.
`FpshqService` faz GET apenas no host fixo do provedor, sem redirecionamentos, com
timeout de conexão/leitura de 4/15 segundos. Respostas de FPS só são aceitas quando
CPU, GPU, jogo, resolução e preset correspondem ao pedido; números ausentes não
viram zero. O veredito 1080p High do provedor não é reutilizado.

O JSON de sucesso é `{"resultado": ...}`, com `consulta`, `jogo`, `fps`, `low1`,
`intervalo`, `origem`, `base`, `confianca`, `matriz`, `url`, `consultadoEm` (epoch em ms),
`cache`, `ramAvaliada: false` e `requisitosVerificados: false`. A busca retorna
`resultado.jogos` com até dez pares `slug`/`name`. Erros usam `erro`, `codigo`, `espera`
e, no 429, `Retry-After`; validação 400, ausência 404/422, falha 502/503 e timeout 504.
O frontend não consulta o provedor como fallback e cancela a espera ao fechar o modal.

Cache LRU de até 256 consultas válidas por uma hora, compartilhado entre usuários do
mesmo processo e sem armazenar builds ou dados de perfil. Lock impede consultas
idênticas simultâneas duplicadas. Limites preventivos: 10 consultas externas/minuto
por usuário, 45/minuto e 9 mil/24h por processo; cache não consome outra chamada externa.
429 externo bloqueia novas chamadas pelo intervalo informado, preservando leituras
do cache. Nenhuma retentativa automática. Antes de escalar para múltiplos processos,
usar cache/contador distribuído; esses limites em memória não são globais entre workers.

`js/benchmark/hardware.js` mantém correspondências explícitas de modelos e VRAM;
modelos não registrados, variantes desconhecidas e vídeo integrado mostram motivo e
não são substituídos. A identificação final ainda depende da confirmação do provedor.
Ampliar esse registro ao integrar os IDs definitivos do catálogo, sem deduzir variantes.

Verificação real pela rota Flask autenticada, sem criar usuário no banco: Valorant,
Ryzen 5 5600 + RTX 3060, 1080p/Alta → HTTP 200, 288 FPS/261 de 1% low; segunda consulta
HTTP 200 com `cache: true`. São os valores retornados no teste, não dados fixos da UI.
As verificações automatizadas de falhas e interface usam respostas controladas.
Nesta rodada: 54 testes Python, 133 testes JavaScript e 66 verificações de navegador
sem falhas (320, 390, 768 e 1440 px), incluindo dots apenas por estado, modal real,
comparação visível, foco de retorno, sessão expirada, ausência de dados e 429/rede.

### RAM, peças antigas e requisitos mínimos — investigação, ainda sem integração

Em 19/10/2026 foram conferidos o [OpenAPI REST](https://fpshq.com/openapi.json),
o `tools/list` do [MCP público da FPSHQ](https://fpshq.com/en/api/ai/) e consultas reais.
O REST `/fps` não recebe RAM; seu `/canrun` usa GPU/renderer e devolve a referência
1080p High, sem ser uma checagem completa de CPU, RAM e requisitos técnicos.
Não confundir esse endpoint com a ferramenta MCP `can_run`, que aceita `game`, `gpu`,
`cpu` e `ram_gb` (capacidade inteira de 1 a 512 GB). Ela retorna requisitos e avaliação
da capacidade, não ajusta frequência, latência, canais ou memória efetivamente livre.
`game_requirements` retorna mínimos/recomendados, origem (`steam`/`manual`/`estimate`)
e situação de lançamento. Esse caminho foi pesquisado, não adicionado ao cliente do site.

Resultados observados em Cyberpunk 2077, usando Ryzen 5 5600:

- REST `/fps`, GT 1030 reconhecida (`geforce-gt-1030`), 1080p High: HTTP 200,
  `fps=8`, intervalo `[7,12]`, `low1=6`, `source=model`, `confidence=low` e
  `verdict.key=no`. A GPU abaixo dos mínimos não causou erro HTTP; houve previsão.
- REST `/fps`, slug `gt-710`: HTTP 404 com `error=gpu_not_found`. A busca “GT 710”
  retornou lista vazia. Isso é ausência de modelo nesse acesso ao catálogo, não prova
  de que a peça não roda nenhum jogo nem de que outro slug/variante inexiste.
- MCP `can_run`, GTX 750 Ti, 4 GB RAM: previsão de 11 FPS em 1080p High,
  intervalo `[9,16]`, `verdict=no`, presets para 30/60 FPS nulos e
  `ram.meets_minimum=false`. Nenhum desses números é uma medição da BOOSTio.
- MCP `can_run`, RTX 3060, comparando 4 GB com 16 GB RAM: em ambos retornou
  70 FPS em 1080p High e veredito `ok`/“Roda bem”. Com 4 GB, os campos de RAM
  indicaram `meets_minimum=false` e `meets_recommended=false`; com 16 GB, ambos
  foram `true`. A matriz de FPS foi igual: não usar o veredito isolado como aprovação.
- MCP `game_requirements` informou mínimo 12 GB e recomendado 16 GB RAM, GPU mínima
  GTX 1060 6 GB/RX 580 8 GB e 70 GB de armazenamento. Marcou `requirements_source=manual`
  e `basis=official`. Os valores principais foram conferidos com a
  [publicação da CD Projekt](https://www.cyberpunk.net/en/news/48271/update-to-pc-system-requirements),
  que também especifica SSD. O campo `storage_gb` sozinho não carrega esse detalhe.

Tratamento planejado: validar mínimos/recomendados antes de aprovar o resultado como
expectativa do PC completo; um mínimo conhecido não atendido deve prevalecer sobre
“Roda bem”. Abaixo do mínimo não equivale necessariamente a impossibilidade de iniciar;
mostrar requisito, limitação e ausência de garantia, sem inventar FPS=0. Se houver
recurso técnico obrigatório comprovadamente incompatível, informar o impedimento.
Ausência de dados/modelo e indisponibilidade/429 são estados diferentes de desempenho
baixo. `verdict=no` é um limiar de FPS em 1080p High, não uma validação de DirectX,
instruções, SO ou inicialização. A conclusão de montagem continua separada disso.

A RAM pode alterar o desempenho dependendo do jogo e configuração, como mostram os
[testes da Kingston](https://www.kingston.com/unitedkingdom/en/blog/gaming/overclocking-ram-more-fps).
Não criar correção percentual universal. Número de pentes não confirma canais ativos;
perfil anunciado não garante a taxa em uso. Memória ocupada pelo SO/outros programas
e uso por vídeo integrado também precisam de ressalva, sem supor detecção pelo navegador.

Priorizar requisitos oficiais com fonte/data e validar um adaptador de leitura da
própria FPSHQ antes de contratar outro serviço. Não inferir “atende” de descrições
genéricas nem tratar requisito estimado como oficial. A API documentada do
[System Requirements Lab](https://docs.systemrequirementslab.com/api/api-quickstart-guide.html)
usa credenciais/token e consulta análises de testes de usuários; não foi comprovada
uma API anônima gratuita equivalente para builds hipotéticas. Nenhum fallback foi
habilitado. Implementação e cenários de teste estão em `pendencias-produto.md`.

### Criação e controles compartilhados

Em Minhas builds, **Criar build** abre uma escolha entre montagem manual e formulário
inteligente, sem criar build antes da escolha e respeitando a quota. A LLM ainda não
está conectada. `navigation-controls.css` e `ui.js` padronizam voltar e fechar sem
alterar os destinos ou a lógica de histórico. Os menus dos cards usam Popover API
quando disponível, evitando o backdrop root do próprio card, com blur de 36px e
fallback. A exigência de sessão para os recursos de montagem está apenas registrada
em `pendencias-produto.md`, não implementada nesta etapa.
O botão de três pontos dos cards usa `dots.json` por `iconeAnimado("dots")`, com
hover/foco e reversão na saída. O HTML de fallback usa o mesmo marcador; movimento
reduzido ou falha no carregamento mantém um SVG estático de três pontos e o aria-label.

A [API da UL](https://support.benchmarks.ul.com/support/solutions/articles/44002238427-api-documentation)
é alternativa contratada e exige chave/segredo e assinatura; qualquer integração dela
deve passar pelo backend, sem expor credenciais no JavaScript.

Os controles `data-page-back` usam `js/components/navigation-back.js` para retornar
à entrada anterior do navegador, com a URL completa da build/categoria. O texto e a
descrição da seta acompanham o destino real. A Navigation API identifica o histórico;
nos navegadores sem ela, usa-se `document.referrer`. Acesso direto e origem externa
usam o `href` original como destino alternativo dentro do site. O formulário distingue
esse retorno do botão **Etapa anterior**, que só muda a pergunta atual.

`js/components/navigation-config.js` contém os links e a política de sessão. Visitantes
veem Entrar e Criar conta no perfil; usuários autenticados veem Builds, Configurações
e Sair. O hamburger contém Início, Montar build, Minhas builds, Builds prontas e Perfil.
A página de login não redireciona visitantes para ela mesma. Falhas de
consulta da sessão mantêm o menu de visitante disponível.

O tooltip não reescreve textos idênticos, e seu MutationObserver ignora as próprias
mutações e os frames Lottie. Isso evita o ciclo que congelava cliques. No cadastro,
validação, checkbox e envio inicializam independentemente do carregamento do Lottie.

## Responsividade

`styles/responsividades/r-site.css` centraliza espaçamentos, logo/footer,
autenticação, modais e áreas seguras do dispositivo. `--page-gutter` controla
as margens laterais e `--page-top` reserva espaço para a logo.
Os arquivos `r-*.css` mantêm os ajustes próprios de cada página.
Eles são importados **depois** de `ui-system.css`, para os estilos gerais não
sobrescreverem os breakpoints. O protótipo `testes.html` mantém seus ajustes locais.

O menu flutuante é usado em todas as larguras. Editor e formulário passam para uma coluna
quando falta espaço; catálogo, builds e a página Sobre nós reduzem suas grades.
Login e cadastro têm altura livre, e os modais são limitados pela altura visível
com rolagem interna. Campos no mobile usam pelo menos 16px, sem reduzir a tela
inteira com `scale()`. O detalhamento de compatibilidade abre no fluxo no mobile.

No formulário, opções e campos de rede rolam dentro da sua área, preservando os
botões de navegação. Em telas baixas na horizontal, o cartão ganha altura e a página
pode rolar, em vez de espremer ou esconder os campos. O resumo expandido do editor
deixa de ser fixo para não prender os controles abaixo da tela. Menus dos cards de
build abrem para baixo e limitam sua altura ao espaço disponível; a
posição é recalculada ao rolar ou redimensionar. Botões bloqueados mantêm a largura
mobile mesmo com o wrapper de tooltip, e prévias de importação quebram nomes longos.

Testes: `node --test frontend/tests/*.test.mjs` (lógica de montagem, arquivos,
planejamento, acessibilidade e regressões).
Ao alterar layouts, confira 320, 390, 600, 768, 1024 e 1440px, landscape e os
estados abertos (menus, modais, senha e modelos de peças).

## Próximo passo no backend

Nenhuma arquitetura foi alterada. Apenas a chamada de atualização de preços em
`app.py` foi comentada, conforme solicitado.

Antes da integração:

1. A rota `peca_bp` precisa ser registrada; o service atual referencia classes antigas
   como `MemoriaRam` e `Armazenamento`, enquanto os modelos usam `MemoriaRAM`, `SSD` e `HD`.
2. Definir o JSON de catálogo com IDs reais, imagens e ofertas separadas por loja.
3. Revisar `Build.to_dict()`: a segunda definição atual sobrescreve a versão que inclui peças.
4. Implementar as operações de build com dono, visibilidade e tranca verificados no servidor.
5. Revalidar compatibilidade e quantidades no Python antes de persistir.

## Glass e verificação

`styles/componentes/glass.css` aplica a base de glass aos cards de serviços, builds,
configurações e novos componentes. A página Sobre nós usa os mesmos cards compartilhados. Ajuste `--glass-background`
para a transparência e `--glass-blur` para o desfoque do fundo.

Testes da lógica: `node --test frontend/tests/build.test.mjs`.
