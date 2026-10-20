# Qualidade do frontend — 20/10/2026

## Escopo e método

Revisão das 15 páginas de `frontend/pages/` e do laboratório `frontend/testes.html`,
depois de trazer a `main` (`71f91b4`) para `front-end`, por fast-forward, sem conflitos.

Medição local com Lighthouse 13.5.0, Chrome 155 headless e perfil móvel com throttling
simulado. As rotas de conta/catálogo/builds foram simuladas em servidor temporário
para avaliar as interfaces sem usar dados pessoais, gerar builds pagas ou coletar preços.
Os mesmos fixtures foram usados antes e depois. O JavaScript, CSS, fontes e animações
do projeto foram servidos normalmente; não foram removidos para aumentar a nota.

Os números abaixo são de uma execução antes e uma depois, não uma mediana nem dados
reais de usuários. Performance pode variar com máquina, rede, CDN e cache. Estas
notas não medem a latência das integrações reais nem substituem a auditoria em produção.

## Resultado por página

Na rodada final, **todas as 16 telas tiveram acessibilidade 100 e boas práticas 100**.
SEO ficou em 100 nas páginas públicas: início, Sobre nós, Termos e Builds prontas.
As demais receberam `noindex` intencional e ficaram em 63 no Lighthouse: perfil,
montagens pessoais, recuperação de senha e laboratório não devem ser indexados.
`noindex` não é controle de acesso; a autorização dos dados continua sendo do backend.

Performance móvel, antes → depois:

- Início: 73 → 78.
- Login: 78 → 73.
- Cadastro: 69 → 70.
- Recuperar senha: 72 → 80.
- Redefinir senha: 72 → 70.
- Formulário: 67 → 71.
- Minhas builds: 66 → 67.
- Configurações da conta: 67 → 76.
- Builds prontas: 69 → 78.
- Editor da build: 41 → 66.
- Catálogo de peças: 42 → 69.
- Detalhes da peça: 66 → 69.
- Sobre nós: 70 → 81.
- Termos: 75 → 79.
- Erro: 78 → 80.
- Laboratório: 64 → 68.

Não houve ganho uniforme em performance: login e redefinição oscilaram para baixo
nessa execução. Não foram alterados fluxos ou tipografia para perseguir esses números.
O maior ganho consistente observado foi reduzir o salto de layout do editor e do
catálogo: CLS de aproximadamente **0,804 para 0,050**, reservando espaço para o conteúdo.

## Ajustes aplicados

- Títulos/descrições individuais, MIME correto do favicon e política de indexação.
- Atalho de teclado antes da logo, conteúdo principal focável e um único h1 na home.
- Rótulos reais nos campos, autocomplete e formulários de senha sem fallback GET.
- Mensagens de erro anunciadas, foco visível e navegação do carrossel por botões.
- Modais fechados inertes, nome acessível, foco inicial, Tab contido e retorno de foco.
- Menus de builds fechados fora da navegação, Escape, estado do dots sincronizado,
  identificação da barra de progresso e papéis ARIA compatíveis com seus conteúdos.
- Colagem nativa de códigos preservada; suporte a colagem completa/parcial e autofill.
- Contraste dos Termos e de botões destrutivos, sem trocar a paleta principal.
- Fontes Lexend/Poppins antecipadas e dimensões intrínsecas das imagens declaradas.
- Posters dos vídeos, carregamento sob demanda, pausa acessível, respeito a movimento
  reduzido/economia de dados e animações de menus ocultos adiadas até a abertura.
- Camada de vídeo da home isolada, com controles fixos compostos acima do fundo,
  evitando falha de pintura que ocultava textos/logo no Chrome com movimento reduzido.
- Loader original preservado, sem deixar uma camada preta quando JavaScript está desativado.

## Validação e limites

- Testes Node: `node --test frontend/tests/*.test.mjs`.
- Testes Python: `PYTHONPATH=backend python -m pytest backend/tests`.
- Verificação no Chrome de overflow, erros de execução, skip link e foco em 320,
  768 e 1440 px; modais/menus por teclado, colagem de códigos e modo sem JavaScript.
  As baterias de celular/desktop e tablet somaram 211 verificações, com repetição
  dos cenários de interação para conferir também a largura intermediária.
- Conferência visual da home móvel e teste com movimento reduzido.

Uma nota automatizada 100 não comprova acessibilidade integral. Ficam pendentes
leitor de tela real (VoiceOver/NVDA), ampliação/alto contraste e testes assistivos manuais.

CSS compartilhado por imports, intro e identidade visual foram mantidos. Empacotamento
de produção, compressão, cache com invalidação, HTTPS, cabeçalhos de segurança, domínio,
canonical/sitemap e respostas HTTP de erro dependem da definição da hospedagem.
Não foram adicionados canonical ou URLs sociais com um domínio presumido.

Referências: [Lighthouse](https://developer.chrome.com/docs/lighthouse/overview),
[pontuação de acessibilidade](https://developer.chrome.com/docs/lighthouse/accessibility/scoring)
e [indexação de páginas](https://developer.chrome.com/docs/lighthouse/seo/is-crawlable).
