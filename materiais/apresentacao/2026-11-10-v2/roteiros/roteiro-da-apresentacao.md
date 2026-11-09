# BOOSTio · Roteiro da apresentação · 3A2

Versão revisada em 09/11/2026 para a apresentação de 10/11/2026.

Google Apresentações: https://docs.google.com/presentation/d/1v7uBdnImOjQyGoJw894cq6zYIyeRh4UGZs4FQOSNMck/edit

**17 slides · 6min30 no total · vídeo principal de 1min50 incluído · margem de 30s até 7min.**

## Como usar este roteiro

Os slides são apoio visual. Falar com a banca, usando as telas, os diagramas e os GIFs para demonstrar o que está sendo explicado. Não ler os textos do slide nem os nomes completos da equipe. As falas abaixo são uma base natural para ensaiar; os comandos entre colchetes são ações de demonstração, não frases para ler.

## Divisão das falas

- Arthur Ferreira Raymundo: slides 1–7, 0:00–1:15 (1min15).
- Gustavo Azevedo Oliveira: slides 8–10, 1:15–2:35 (1min20).
- Gustavo Lopes Horta: slides 11–12, 2:35–3:30 (55s).
- Giovanni de Castro Morais Trivellato: slide 13, 3:30–5:20 (1min50).
- Kayky Luiz Ferreira de Paula da Silva: slides 14–17, 5:20–6:30 (1min10).

O tempo é um planejamento de ensaio, não uma duração de fala medida. Reproduzir os trechos curtos durante a fala. A narração do slide 13 acompanha o vídeo e não acrescenta outros 110 segundos.

## 01. BOOSTio · 0:00–0:20 · 20s

**Arthur Ferreira Raymundo**

Boa tarde! Somos Arthur, Gustavo Azevedo, Gustavo Horta, Giovanni e Kayky, da turma 3A2. A BOOSTio ajuda quem vai montar ou melhorar um computador a escolher as peças de acordo com o uso, o orçamento e o que já possui.

## 02. O diferencial da BOOSTio · 0:20–0:35 · 15s

**Arthur Ferreira Raymundo**

Quem monta o primeiro PC precisa decidir onde investir e quais peças combinam. A plataforma reúne sugestão por uso e orçamento, reaproveitamento de peças, diagnóstico e comparação. Nosso público inclui estudantes, jogadores e profissionais.

## 03. Montagem inteligente · 0:35–0:43 · 8s

**Arthur Ferreira Raymundo**

O formulário transforma uso, orçamento e peças já possuídas em uma sugestão de configuração.

## 04. Compatibilidade e consumo · 0:43–0:51 · 8s

**Arthur Ferreira Raymundo**

O diagnóstico mostra conflitos e consumo estimado. Dados insuficientes deixam a verificação pendente.

## 05. Comparação de builds · 0:51–0:59 · 8s

**Arthur Ferreira Raymundo**

Duas builds lado a lado mostram diferenças de peças, preço e consumo estimado.

## 06. Compartilhamento de configurações · 0:59–1:07 · 8s

**Arthur Ferreira Raymundo**

O link público permite consultar sem login. Só o proprietário pode alterar a configuração original.

## 07. Configurações prontas · 1:07–1:15 · 8s

**Arthur Ferreira Raymundo**

Os modelos prontos são pontos de partida para escolher e personalizar conforme a necessidade.

## 08. Modelo de domínio · 1:15–1:45 · 30s

**Gustavo Azevedo Oliveira**

Este é um recorte do domínio revisado no código. Usuario possui configurações. Build referencia modelos do catálogo, como Processador, que herda de Peca. BuildSalva guarda o estado em JSON e pode existir sem uma Build original. Ofertas concentram preço e disponibilidade; a referência à peça usa categoria e ID. O conteúdo JSON não cria relações SQL com cada componente.

## 09. Recuperação de dados · 1:45–2:10 · 25s

**Gustavo Azevedo Oliveira**

A consulta do histórico começa com categoria e ID da peça. O Controller chama o Service, que procura a oferta ativa no Repository. Este consulta Oferta via SQLAlchemy e banco. O Service também lê o histórico diretamente na Model. O Controller devolve JSON.

## 10. Entrada de dados · 2:10–2:35 · 25s

**Gustavo Azevedo Oliveira**

Na criação manual, o frontend envia o estado da configuração. criar_build_manual chama o Service, que valida o JSON e aplica o orçamento. BuildSalva verifica e-mail e limite da conta, persiste e confirma a transação. O Controller retorna 201. Entrada inválida retorna 400; limite, 409; falha de banco faz rollback. Neste fluxo, a gravação ainda não passa por Repository.

## 11. Arquitetura e organização · 2:35–3:00 · 25s

**Gustavo Lopes Horta**

O frontend tem páginas, estilos e módulos de consumo da API. No backend, funções em Controllers recebem HTTP; Services executam as regras; Repositories concentram consultas específicas, como a oferta ativa. Models representam os dados e ainda executam parte do CRUD. Por isso, a estrutura existe, mas nem todos os fluxos usam Repository.

## 12. Frontend e API separados · 3:00–3:30 · 30s

**Gustavo Lopes Horta**

A interface está em boostio.com.br e a API em outro domínio, api.boostio.com.br. O navegador envia HTTP e recebe JSON. Nesta checagem, o health respondeu 200 com status ok e permitiu a origem do frontend. O vídeo de Network deve mostrar também uma ação de negócio, o status e a resposta, com cookies e tokens ocultos.

## 13. Demonstração funcional · 3:30–5:20 · 110s

**Giovanni de Castro Morais Trivellato**

00:00–00:35 — Aqui confirmamos as últimas respostas do formulário e enviamos a solicitação. A configuração retornada considera o objetivo, o orçamento e as peças informadas. [Mostrar o resultado real.]

00:35–01:00 — Agora o editor aplica uma regra a componentes com dados conhecidos. [Apontar o motivo exibido.] O consumo é uma estimativa; verificações sem dados ficam pendentes.

01:00–01:25 — Na comparação, estas duas builds diferem em [peça, preço ou consumo observado]. [Apontar a diferença real, sem decorar um valor inventado.]

01:25–01:50 — Tornamos esta build pública e copiamos o link. Abrindo sem login, a configuração fica disponível para consulta, sem alterar a original. [Mostrar os controles de edição ausentes/bloqueados. Se couber, tornar privada e mostrar o bloqueio de acesso.]

## 14. Persistência com ORM · 5:20–5:37 · 17s

**Kayky Luiz Ferreira de Paula da Silva**

O SQLAlchemy persiste as entidades pela sessão. Em SQLite temporário, conferimos criação, leitura, atualização e exclusão com o código real. A oferta 12 foi alterada e removida. São dados de demonstração, sem acessar a produção.

## 15. Consultas na camada Repository · 5:37–5:55 · 18s

**Kayky Luiz Ferreira de Paula da Silva**

buscar_ativa filtra categoria, peça, loja e estado ativo, escolhendo o maior ID. Nos dados de demonstração, retornou a oferta 12 e excluiu a inativa e a de outra categoria. A consulta ORM fica no Repository.

## 16. Tecnologias e documentação · 5:55–6:20 · 25s

**Kayky Luiz Ferreira de Paula da Silva**

A API usa Python, Flask e SQLAlchemy; o frontend, HTML, CSS e JavaScript. MySQL persiste os dados; Redis apoia os limites de requisição; Docker separa os serviços. O README documenta vinte requisitos e seus escopos. A hospedagem foi verificada; IA funcional e consentimento exigem suas próprias evidências.

## 17. Encerramento · 6:20–6:30 · 10s

**Kayky Luiz Ferreira de Paula da Silva**

A BOOSTio ajuda a planejar o próximo computador com escolhas compatíveis com o uso e o orçamento. Vocês podem conhecer o projeto em boostio.com.br. Obrigado!

## Ajustes antes do ensaio

- Inserir os vídeos/GIFs reais. Os espaços estão preparados, sem gravações simuladas.
- No bloco de comparação da demo, substituir a indicação entre colchetes pelo resultado observado na gravação.
- A escrita manual ainda acessa a Model, sem Repository. Não apresentar essa adequação como concluída.
- Preços são da última consulta e não incluem frete; consumo é estimativa.
- Só reivindicar IA funcional após a execução real; consentimento precisa de registro no servidor.
- Notas técnicas e fontes de cada slide estão nas notas do apresentador e em notas-slides.json.
- Consultar materiais-pendentes.md e guia-de-gravacao.md para as mídias.
