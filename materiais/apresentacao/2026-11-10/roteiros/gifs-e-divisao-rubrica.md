# Ajuste à rubrica do professor e avaliação dos GIFs — 09/11/2026

Referência: repositório `gleisonbt/RoteiroApresentacaoPS2026`, arquivo `Roteiro_Apresentacao_Projeto_Rubrica.md`.
Esta nota substitui, onde houver conflito, a divisão e a lista de funções de `roteiro-do-pitch.md`
(que ainda descreve 20 slides e RF09 no vídeo).

## Divisão revisada (17 slides, 6min30)

| Integrante | Slides | Tempo | Bloco da rubrica |
|---|---|---|---|
| Arthur Ferreira Raymundo | 1–7 | 1min15 | Abertura (20s) + projeto, público e 5 casos de uso (55s) |
| Gustavo Azevedo Oliveira | 8–10 | 1min20 | Domínio (35s) + 2 fluxogramas com Repository (55s, comprimir para ~45s) |
| Gustavo Lopes Horta | 11–12 | 55s | Arquitetura e separação frontend/API |
| Giovanni de Castro Morais Trivellato | 13 | 1min50 | Demo: 4 funções não CRUD (limite 2min) |
| Kayky Luiz Ferreira de Paula da Silva | 14–17 | 1min10 | ORM, SQL no Repository, README/bônus, encerramento |

Os cinco casos de uso passam a ser RF04, RF13, RF07, **RF08** e RF10 (RF09 sai dos slides 3–7).

## Avaliação dos temas dos GIFs

| GIF | Veredito | Observação |
|---|---|---|
| 03 Montagem (RF04) | Bom | Função de negócio, não CRUD. Mostrar a configuração realmente gerada. |
| 04 Compatibilidade (RF13) | Bom | Mostrar regra + motivo + consumo; dado ausente como "pendente". |
| 05 Comparação (RF07) | Bom | Deixar 2s parados na diferença. |
| 06 Compartilhamento (RF08/RF17) | Aceitável, com cuidado | Sozinho parece só "alterar um campo" (CRUD). Na demo, destacar o controle de acesso: link abre sem login, é somente leitura, e tornar privada bloqueia. Só assim conta como função não CRUD. |
| 07 Configurações prontas (RF10) | Fraco como demo | É listar + filtrar. Serve como caso de uso (slide 7), **não** deve entrar na contagem das 4 funções do vídeo. |
| 12 Comunicação com API | Corrigir | O roteiro cita `api.boostio.com.br`, mas `config-publica.js` está vazio (mesma origem) e a checagem de 08/11 não achou API em `boostio.com.br/api`. Gravar com o endereço realmente usado (localhost:5000 ou o domínio confirmado) e ocultar cookies/tokens. |
| 16 README | Bom | Mostrar RF e escopos; não ler os 20 itens. |

**Sugestão de seleção da demo:** RF04, RF13, RF07 e RF08 (como no roteiro revisado) é válida; RF09
(melhorias, com antes/depois e aplicação persistida) é uma função mais claramente "não CRUD" e pode
substituir RF08 se o ensaio do controle de acesso não ficar convincente.

## O que ainda falta (não alterado nesta tarefa)

- `notas-slides.json` e `scripts/autor-slides.mjs` ainda geram 20 slides; regenerar o PowerPoint/PDF para 17.
- Gravar o MP4 de 1min50 e os 7 GIFs; nenhum arquivo de vídeo/GIF existe em `materiais/`.
- Fluxogramas ainda mostram o Repository tracejado (BuscarBuildService e CriarBuildManualService acessam `BuildSalva` direto).
- Bônus de consentimento não está registrado no servidor; não reivindicar.
