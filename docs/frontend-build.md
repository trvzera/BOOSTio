# Editor de build e efeitos de scroll

Abra pelo Live Server:

- `frontend/pages/configuracao-build.html`: editor vazio.
- `frontend/pages/configuracao-build.html?id=build-demo-1`: configuração de exemplo.
- `frontend/pages/pecas.html?categoria=processador`: catálogo por categoria.
- `frontend/pages/peca.html?id=SEED-CPU-02`: ficha técnica e lojas.
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
O footer de todas as páginas que usam `loading.js` recebe o mesmo reveal automaticamente.

## Estado local e pontos de integração

`js/build/catalogo.js` centraliza o carregamento do catálogo e as informações das lojas.
A futura API pode substituir `carregarCatalogo()`, mantendo o mesmo formato:
id estável, categoria, imagem, preço, consumo e campos técnicos da peça.
O campo `imagem` já é suportado; ausências exibem um placeholder.

`js/build/estado.js` guarda os rascunhos e a lista demonstrativa de builds no localStorage.
Salvar no perfil nesta versão significa salvar neste navegador. Não há gravação na conta
do Flask nem sincronização entre dispositivos. Dados do formulário entram como peças
próprias sem preço; o usuário precisa selecionar o modelo para a validação técnica.

Links compartilhados carregam a configuração por IDs de catálogo e quantidades, e abrem
uma cópia. A visibilidade e a tranca são controles locais de interface, não autorização
do servidor. Links já enviados não podem ser revogados por esse protótipo.

RAM é uma lista em `componentes.memoria_ram`; o formato antigo com um objeto é migrado
automaticamente. Cada entrada tem `id` e `quantidade` de kits. Todos os módulos de todos
os kits contam nos slots e na capacidade máxima da placa-mãe. Novos modelos precisam
ter o mesmo DDR e frequência; misturar marcas/modelos gera aviso de estabilidade.
Duplicação e remoção são individuais. Para trocar outras peças, remova a atual primeiro.

`js/build/compatibilidade.js` verifica socket, DDR, slots, capacidade, formato do gabinete,
altura do air cooler, suporte declarado a water cooler, M.2 e potência da fonte.
Dados genéricos como “Intel/AMD” produzem aviso para conferir o socket no fabricante.
BIOS, dimensões da GPU, conectores e disponibilidade não são plenamente validados.
O consumo exclui monitor e periféricos externos e é apenas uma estimativa da seed.
Não há potência recomendada. Fonte abaixo do consumo é erro; igual ao consumo gera aviso
de ausência de margem. Fans são obrigatórias. Air cooler e water cooler ficam em uma categoria;
cooler separado é obrigatório somente quando o processador não inclui cooler.
Periféricos são opcionais e podem ser ativados pelo checkbox do editor.
O checkbox mantém o mesmo elemento e a mesma instância Lottie durante a atualização
dos cards, permitindo concluir a animação nos dois sentidos.
SSD e HD aparecem juntos em **SSD / HD**, um grupo obrigatório: basta um dos dois.
As peças continuam armazenadas como `ssd` e `hd`, preservando rascunhos existentes.
Placa de vídeo é obrigatória quando o processador selecionado não tem vídeo integrado;
enquanto faltar, o status da build permanece incompleto.
O catálogo é filtrado automaticamente pelas verificações quando a build já possui peças.
O botão da página de produto também revalida a seleção antes de adicionar.

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
As demais páginas usam preto com fade de 480 ms. Apenas o fluxo editor → catálogo →
peça usa fade mais curto: 280 ms antes de o catálogo estar disponível e 180 ms depois.
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

`js/header.js` renderiza a logo de 100px no topo esquerdo e o perfil no topo direito.
O perfil permanece disponível antes e depois do login; os seus links não usam setas.
O botão usa `profile.json` no tamanho original de 60px. Hover e foco abrem o dropdown;
clicar fixa o menu aberto. Uma ponte entre botão e painel evita fechar durante o movimento
do cursor, e Escape, clique fora ou um segundo clique fecham o menu.
O hamburger flutuante fica oculto até a autenticação. Em `testes.html`, o atributo
`data-menu-preview` permite verificar o hamburger mesmo sem login.
Os painéis usam glass, itens compactos, `inert` quando fechados, Escape e clique fora
para fechar. Abrir um painel fecha o outro. Navegações usam páginas.

Os controles `data-page-back` usam `js/components/navigation-back.js` para retornar
à entrada anterior do navegador, com a URL completa da build/categoria. O texto e a
descrição da seta acompanham o destino real. A Navigation API identifica o histórico;
nos navegadores sem ela, usa-se `document.referrer`. Acesso direto e origem externa
usam o `href` original como destino alternativo dentro do site. O formulário distingue
esse retorno do botão **Etapa anterior**, que só muda a pergunta atual.

`js/components/navigation-config.js` contém os links e a política de sessão. Visitantes
veem Entrar e Criar conta no perfil; usuários autenticados veem Builds, Configurações
e Sair. O hamburger contém Início, Montar build, Suas builds e Perfil.
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
quando falta espaço; catálogo, builds e desenvolvedores reduzem suas grades.
Login e cadastro têm altura livre, e os modais são limitados pela altura visível
com rolagem interna. Campos no mobile usam pelo menos 16px, sem reduzir a tela
inteira com `scale()`. O detalhamento de compatibilidade abre no fluxo no mobile.

Testes: `node --test frontend/tests/*.test.mjs` (34 verificações de lógica e regressão).
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
configurações, desenvolvedores e novos componentes. Ajuste `--glass-background`
para a transparência e `--glass-blur` para o desfoque do fundo.

Testes da lógica: `node --test frontend/tests/build.test.mjs`.
