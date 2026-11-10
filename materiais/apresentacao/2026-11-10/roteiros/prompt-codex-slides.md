# Prompt para o Codex — montar os slides da BOOSTio (pitch 10/11/2026)

Cole este documento inteiro no Codex, na raiz do repositório BOOSTio. Ele descreve cada slide, o texto, a posição dos GIFs e as regras de honestidade. Não invente funcionalidades: tudo aqui vem do README e do código.

## 0. Objetivo e restrições

- Gerar `BOOSTio-Pitch-3A2.pptx` (editável), `slide-01.png` a `slide-20.png` e um PDF de prévia com os 17 slides do pitch. Os slides 18–20 são de apoio e ficam **ocultos**.
- Tamanho 1280×720 (16:9). Tempo total planejado: **390 s (6min30)**; limite da banca: 7 min.
- Base técnica: `materiais/apresentacao/2026-11-10/scripts/autor-slides.mjs` (função `build(p)`) e `scripts/gerar-slides.mjs <pasta-de-saida>`. Preferir editar esses arquivos a recriar do zero. Rodar com o Node do runtime: `~/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node scripts/gerar-slides.mjs <saida>`.
- Identidade: fundo preto `#000000`, cartões `#101114`, azul `#007BFF`, branco, cinza `#A1A1A6`, texto escuro `#16181D`, linhas `#D5D8DE`. Fonte **Lexend** (instalar o `.ttf`; o repositório só tem `frontend/fonts/Lexend[wght].woff2`, converter com fontTools+brotli). Logo oficial em `materiais/brand/LOGO1V2-PNG_00000.png`.
- Texto do slide curto: o integrante **não lê** o slide; fala com a banca usando o GIF. No máximo 3 linhas de apoio por slide, corpo ≥ 24 px, títulos 43 px.
- Cada slide leva **notas do apresentador** com `TEMPO: Ns`, a fala sugerida e as fontes (arquivos do repositório). Exportar também `roteiros/notas-slides.json`.

## 1. Convenção do espaço para GIF

Enquanto os GIFs não existem, desenhar um quadro:

- retângulo `#0B0C0F`, linha tracejada azul `#007BFF` (branca no slide azul), 1,3 px;
- texto central azul "ESPAÇO PARA O GIF" (24 px, negrito) e, abaixo, o nome do arquivo em cinza (20 px);
- manter proporção **16:9** sempre que possível; a função `gif(s,label,x,y,w,h)` do `autor-slides.mjs` já faz isso.

Quando o arquivo chegar (`materiais/apresentacao/2026-11-10/assets/gifs/<nome>.gif`), trocar o quadro por `s.images.add({path, fit:'contain', alt})` **na mesma posição e tamanho**, sem borda. Se o GIF não animar no PPTX exportado, anexar o MP4 original e avisar. Antes de inserir, conferir que o GIF realmente anima e que o texto da tela fica legível; sem áudio, notificações, cookies, tokens, e-mails ou dados pessoais.

## 2. Slides (pitch, 17)

### Slide 1 — Abertura · 20 s · Arthur
- Fundo preto. Logo (300 px de largura) em (64,55).
- Título 74 px: "Menos dúvidas.\nMais desempenho." em (64,230).
- Subtítulo 29 px cinza: "Planejamento de computadores por objetivo e orçamento".
- Linha azul em y=555; "3A2   Colégio Cotemig" (22 px azul); nomes da equipe em duas linhas, 17 px (não ler em voz alta).
- Fala: nome do projeto, turma, integrantes e uma frase sobre propósito e público.

### Slide 2 — Problema e público · 10 s · Arthur
- Fundo azul `#007BFF`. Três perguntas 62 px: "Qual peça escolher? / Vai ser compatível? / Cabe no orçamento?".
- Rodapé: "Primeiro PC e upgrade" (31 px preto) e "Para estudar, jogar, criar ou trabalhar".
- Público: estudantes, jogadores, criadores de conteúdo e profissionais.

### Slides 3 a 7 — cinco casos de uso · 9 s cada · Arthur
Layout igual nos cinco (fundo preto):
- título 43 px no topo (64,52);
- número grande azul 78 px em (64,180);
- frase-objetivo 31 px branca em (64,309), largura 340;
- descrição 24 px cinza em (64,477), largura 325;
- **GIF em (435,196), 780×439**.

| Slide | Título | Número | Frase-objetivo | Descrição | GIF |
|---|---|---|---|---|---|
| 3 | Montagem inteligente (RF04) | 01 | Respostas do usuário geram uma configuração | Objetivo e orçamento viram uma seleção de peças validada. | `03-montagem.gif` |
| 4 | Diagnóstico de compatibilidade (RF13) | 02 | Conflitos aparecem durante a montagem | O usuário confere peças, consumo estimado e pendências. | `04-compatibilidade.gif` |
| 5 | Comparação de configurações (RF07) | 03 | Duas ou três builds, lado a lado | O usuário compara peças, valores e consumo estimado. | `05-comparacao.gif` |
| 6 | Compartilhamento por link (RF08/RF17) | 04 | Quem recebe o link consulta, sem alterar | O usuário torna a build pública e envia o link; o visitante só visualiza. | `06-compartilhamento.gif` |
| 7 | Melhorias do setup (RF09) | 05 | Prévia antes e depois antes de aplicar | O usuário informa um valor e o sistema sugere a expansão compatível. | `07-melhorias.gif` |

#### O que cada GIF deve mostrar (6–8 s, 1920×1080, só o necessário na tela)
1. **03-montagem.gif**: últimas respostas do formulário (objetivo e orçamento) → enviar → configuração realmente gerada, com peças e total. Cortar espera de rede, manter ação e resultado reais. O diálogo "Como você quer criar sua build?" (Formulário inteligente / Montagem manual) pode abrir o GIF. Funcionalidade: `frontend/pages/formulario.html`, `backend/services/build_service/gerar_build_service.py`. A IA depende de provedor LLM: confirmar que respondeu no ensaio antes de afirmar.
2. **04-compatibilidade.gif**: no editor (`configuracao-build.html`), selecionar uma combinação com dados técnicos conhecidos (ex.: padrão de RAM da placa-mãe, slots); mostrar a regra aplicada, o motivo e terminar no consumo estimado em watts. Dados ausentes aparecem como "pendente/não verificado", nunca como "compatível". Fonte: `frontend/js/build/compatibilidade.js`, `backend/services/build_service/avaliar_compatibilidade_service.py`.
3. **05-comparacao.gif**: em "Minhas builds" clicar em **Comparar builds**, escolher duas builds e parar com as duas lado a lado e uma diferença de preço, peça ou consumo por **≥ 2 s**. O cálculo básico roda no navegador (`frontend/js/build/comparacao.js`). "Comparar renderização" (Blender) é opcional e **não** deve ser prometido. Menor preço ou consumo não comprova maior desempenho.
4. **06-compartilhamento.gif**: build pública + link → abrir o link em janela **sem login** → tela somente leitura (o visitante não vê o orçamento nem altera a original). Se couber, tornar privada e mostrar que o link deixa de funcionar. Esta é a evidência de **controle de acesso**; sem ela o item parece só uma edição de campo. Fonte: README (RF08, RF17), `backend/models/build_salva.py`, `frontend/js/api/build/builds.js`.
5. **07-melhorias.gif**: abrir "Buscar melhorias" em uma build, informar quanto investir, escolher RAM (ou SSD/HD) válida, mostrar capacidade antes/depois, custo e respeito aos slots/conexões, clicar **Aplicar trocas** e mostrar o resultado salvo. Não prometer ganho de FPS nem recomendar CPU/GPU. Fonte: `frontend/js/build/melhorias.js`, `melhorias-ram.js`, `melhorias-discos.js`.

Se a equipe preferir "Builds prontas" no slide 7, usar `07-configuracoes-prontas.gif` (aplicar filtro por objetivo/orçamento e abrir um modelo); esse caso **não conta** entre as quatro funções não CRUD da demo.

### Slide 8 — Modelo de domínio · 35 s · Gustavo Azevedo
- Fundo branco. Diagrama de classes (recorte coerente com `backend/models/`):
  - `Usuario` (nome, email, budget; `buscar_por_email()`) 1 — 0..* `Build` e 1 — 0..* `BuildSalva`;
  - `Build` (usuario_id, nome, quantidade_ram; `criar_gerada()`) referencia `Processador` (soquete, nucleo);
  - `BuildSalva` (usuario_id, build_original_id [0..1], estado: JSON; `criar_limitada()`), relação opcional com `Build`;
  - `Processador` herda de `Peca «abstract»` (fabricante, modelo, preco; `to_catalogo()`).
- Legenda: "Recorte do domínio de montagem" e "JSON contém componentes e quantidades". O limite de 3 builds é regra de negócio, não multiplicidade da relação.
- Apoio oculto (slide 18): `docs/diagrama-classes.png`.

### Slides 9 e 10 — Fluxogramas · 25 s e 20 s · Gustavo Azevedo
Fundo branco. Cinco caixas em linha com setas: Frontend → Controller → Service → Model → Banco, retorno em JSON.
- **Slide 9, recuperação**: `GET /build/{id}`; `BuscarBuildService` carrega e avalia; `BuildSalva.buscar()`; consulta ORM por proprietário.
- **Slide 10, entrada**: `POST /build/manual`; `CriarBuildManualService` valida estado e regras; `BuildSalva.criar_limitada()`; INSERT com ORM e commit (e-mail verificado e limite por conta).
- A rubrica exige o **Repository** nos dois fluxos. Hoje os Services chamam `BuildSalva` direto. Desenhar o Repository **tracejado** com a legenda "Contínuo: fluxo atual / Tracejado: adequação à rubrica". **Só desenhar o Repository em linha cheia depois de o código existir.** Se a equipe implementar, refazer os dois slides e as falas.

### Slide 11 — Arquitetura · 25 s · Gustavo Lopes
Duas colunas. Esquerda "Frontend": `frontend/pages`, `frontend/styles`, `frontend/js/api`. Direita "API Flask": `backend/controllers` (entrada HTTP), `backend/services` (regras e casos de uso), `backend/models` (entidades e ORM), `backend/repositories` (acesso específico). Nota: "CRUD de builds permanece nas Models".

### Slide 12 — Frontend e API separados · 30 s · Gustavo Lopes
- Esquerda: caixa "Navegador" (HTML+CSS, JavaScript) → seta "HTTP / JSON" → caixa "API Flask" (Controller e Service, Models / Repositories); legenda `fetchComErro(\`/build/${id}\`)`.
- **GIF em (410,196), 805×453: `12-comunicacao-api.gif`** (8–12 s): site + painel Network visíveis; executar uma ação (ex.: abrir uma build ou o histórico de preços); mostrar a requisição, o status e parte do JSON. Ocultar cookies, tokens e dados pessoais.
- **Atenção ao domínio:** `frontend/js/config-publica.js` está vazio (mesma origem). O roteiro antigo citava `api.boostio.com.br`, mas em 08/11 `boostio.com.br/api/health` respondeu 404. Mostrar o endereço **realmente usado** (local em `:5000` ou o domínio confirmado) e não afirmar API hospedada sem prova.

### Slide 13 — Demonstração funcional · 110 s · Giovanni
- Fundo azul. Título "4 funções em 1min50" (60 px) em (64,150); lista 28 px em (64,400): "RF04 Montagem inteligente / RF13 Compatibilidade e consumo / RF07 Comparar builds / RF08 Compartilhar com controle de acesso"; rodapé preto "Ação do usuário e resultado do sistema".
- **Vídeo/GIF em (690,150), 525×420: `13-demonstracao-1m50.mp4`** (incorporar o vídeo no PowerPoint e manter cópia MP4 offline).
- Cronometragem do vídeo: 0:00–0:35 RF04; 0:35–1:00 RF13; 1:00–1:25 RF07; 1:25–1:50 RF08. Legendas curtas no início de cada trecho ("RF04 · Montagem inteligente", etc.).
- Cada bloco precisa mostrar **ação e resultado**, não uma tela já aberta. Os GIFs 03–06 podem ser recortes desta gravação. Plano B robusto: trocar RF08 por RF09 (melhorias) se o controle de acesso não ficar convincente.
- Cadastro, listagem e cópia de build **não** contam como funções não CRUD.

### Slide 14 — Persistência com SQLAlchemy · 15 s · Kayky
Código real (fonte monoespaçada Menlo 28 px) de `backend/models/base.py`:
```
def salvar(self):
    db.session.add(self)
    db.session.commit()

def deletar(self):
    db.session.delete(self)
    db.session.commit()
```
À direita "ModeloBase": id, criado_em, atualizado_em. Rodapé: "O CRUD convencional está implementado nas Models". A evidência de CRUD (criar, ler, atualizar, excluir) deve vir de um banco **temporário** antes de a fala afirmar que foi comprovada.

### Slide 15 — SQL no Repository · 15 s · Kayky
Código real de `backend/repositories/saude_repository.py`: `db.session.execute(text("SELECT 1"))`. Legenda: "SQL atual: verificação de conexão" e "A consulta de negócio em Repository ainda é uma pendência". `SELECT 1` prova conectividade, não consulta de negócio; quando houver Repository de builds, mostrar a consulta e o resultado conhecido.

### Slide 16 — Tecnologias e README · 30 s · Kayky
- Esquerda: "Python  Flask  SQLAlchemy" (branco), "HTML  CSS  JavaScript" (azul), "README: 20 requisitos com escopo e limitações", "Bônus só com evidência: IA em execução / API hospedada / consentimento persistido".
- **GIF em (690,196), 525×420: `16-readme.gif`** (6–8 s): abrir o README, rolagem curta pela tabela de requisitos, parar com os códigos RF e descrições legíveis. Não ler os 20 itens.
- Consentimento: o cadastro envia só nome, e-mail e senha (`frontend/js/api/usuario/criarUsuario.js`); **não** reivindicar o bônus.

### Slide 17 — Encerramento · 10 s · Kayky
Logo, "Seu próximo PC começa aqui" (77 px), "Menos dúvidas, mais desempenho." (azul), "Obrigado. boostio.com.br". Uma frase sobre o problema resolvido; nenhuma funcionalidade nova.

## 3. Slides de apoio (ocultos, `hidden=true`, tempo 0)

- **18 Apoio: domínio de montagem** — imagem `docs/diagrama-classes.png` em (64,145) 1150×515, fundo branco.
- **19 Apoio: preparação antes do pitch** — lista: Repository nos casos de uso; vídeo real de quatro funções; Network, ORM e SQL; bônus com evidência; ensaio completo em 6min30.
- **20 CMI: teste no MacBook** — fundo azul: "Qual seria o seu próximo PC?", "MacBook para experimentar", "NFC 01 Monte o seu PC / NFC 02 Acompanhe a Boostio".

## 4. Funcionalidades disponíveis (README) para trocar por mais impacto

Todas marcadas como implementadas, usar apenas com ensaio feito:
- RF04 montagem por formulário/IA · RF13 compatibilidade e consumo · RF07 comparação (preços, componentes, consumo; Blender opcional) · RF08 compartilhamento por link público, somente leitura · RF09 melhorias (RAM, SSD/HD) · RF10 configurações prontas (16 modelos, filtro de budget) · RF15 budget no perfil · RF17 visibilidade pública/privada.
- Preço/ofertas de peças e exportação JSON/CSV no navegador (conferir no README antes de citar).
- **Não prometer:** FPS (desativado), CPU/GPU como melhorias, homologação da LLM sem ensaio, API de produção sem prova, consentimento persistido.

## 5. Critérios de aceite

1. 17 slides visíveis + 3 ocultos; soma dos tempos visíveis = 390 s.
2. Cada slide de GIF tem o quadro na posição acima, com o nome exato do arquivo.
3. Nenhum texto sai do quadro, sobrepõe ou fica menor que 17 px (19–20 px nos rodapés).
4. Notas do apresentador em todos os slides; `notas-slides.json` sincronizado.
5. PNGs, PPTX e PDF regenerados; fazer backup dos arquivos anteriores antes de sobrescrever.
6. Revisar os PNGs um a um; se algum GIF não animar ou não ficar legível, reportar em vez de inserir.
