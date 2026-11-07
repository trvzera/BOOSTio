# Administração

Dashboard em `/admin` (`frontend/pages/admin.html`), só para contas com o papel de administrador. Hoje tem
uma seção, **Pendências**; novas seções entram em `frontend/js/admin/secoes.js` (id, rótulo e função que a
inicia) com um bloco `data-admin-secao` correspondente no HTML.

## Quem é administrador

A coluna `usuario.administrador` (falsa por padrão). Não existe rota pública para alterá-la: só pelo terminal
do servidor, e a conta precisa estar ativa e com e-mail verificado. Promover ou remover encerra as sessões
dessa conta (ela entra de novo e passa a ver o novo papel).

```sh
# Na VPS, a partir do checkout do projeto
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app usuario-promover-admin --email pessoa@exemplo.com
# também: usuario-remover-admin --email ...   e   usuario-listar-admins
```

Banco existente precisa da coluna antes (faça backup):

```sh
python -m flask --app app usuarios-admin-preparar            # simula
python -m flask --app app usuarios-admin-preparar --aplicar  # adiciona usuario.administrador
```

`banco-preparar` (SQLite) já aplica isso. No MySQL, rode `usuarios-admin-preparar --aplicar` na janela de
atualização, antes de subir o código novo: sem a coluna, o login quebra.

## Como a proteção funciona

- O link "Administração" aparece no menu do perfil só para administradores (`/auth/me` devolve `administrador`).
- A página começa oculta e só aparece depois de confirmado o papel. Quem não é administrador vê "página não encontrada" (404), sem flash do painel nem título de administração. Visitante sem login vai para o login.
- **O que protege de verdade é o servidor:** toda rota `/admin/*` usa `@login_required` e `@apenas_administrador`
  (401 sem login, 403 sem o papel) e as ações de escrita exigem o token CSRF como no resto do site.

## Pendências

Lista os anúncios de `produto_pendente` (por padrão `em_revisao`), com filtros de situação, loja e categoria.

| Rota | O que faz |
| --- | --- |
| `GET /admin/pendencias` | Lista com `status`, `loja`, `categoria`, `limite` e `depois_id` (cursor). |
| `GET /admin/pendencias/<id>` | Detalhe com os candidatos (peça, pontuação, conflitos e o que falta comprovar). |
| `POST /admin/pendencias/<id>/aceitar` | `{"peca": "categoria:id"}`: cria a oferta e o vínculo. |
| `POST /admin/pendencias/<id>/candidatos/descartar` | `{"peca": "categoria:id"}`: tira só aquela peça da lista de candidatas (fica registrado e um novo matching não a recoloca). |
| `POST /admin/pendencias/enviar-ia` | `{"ids": [1, 2], "decidir": false}`: a IA analisa até 20 pendências por pedido, numa só requisição (sempre refaz); com `decidir: true` também aceita ou rejeita as de alta confiança. |
| `POST /admin/pendencias/<id>/rejeitar` | `{"motivo": "..."}` (opcional, até 200 caracteres). |

Regras do aceite:

- Só vale para uma das peças candidatas daquela pendência, sem conflito, aprovada e da mesma categoria.
- Usa o mesmo caminho de gravação da busca automática: trava da coleta, peça inalterada desde a análise e
  anúncio que não pertence a outra peça. Só a decisão automática de "confirmada" é dispensada, porque quem
  decidiu foi uma pessoa; o `administrador_id` e a data ficam em `evidencias.revisao_manual`.
- **Shopee e Mercado Livre podem ser aceitos pelo painel.** No Mercado Livre o servidor reconsulta o
  catálogo e o anúncio na API da loja (poucas requisições, antes da transação) e confere que continua
  disponível como oferta nova do mesmo vendedor. Depois grava o vínculo do catálogo com a peça (critério
  `revisao_manual`), a oferta e o histórico, e fecha a pendência, tudo numa transação. Catálogo já ligado a
  outra peça, peça que mudou desde a análise ou anúncio que saiu do ar recusam o aceite. Se o Mercado Livre
  não responder, o painel recebe 502 e nada é gravado.
- Pendência já aceita ou rejeitada não é reaberta (nem pelas buscas seguintes).

## Sugestão da IA nas pendências

Para não analisar tudo à mão, a IA pode recomendar a peça de cada pendência aberta:

```bash
cd backend
python -m flask --app app admin-pendencias-sugerir --limite 20            # só conta o que analisaria
python -m flask --app app admin-pendencias-sugerir --limite 20 --aplicar  # chama a IA e grava
```

- Por padrão a IA **só sugere**. Com `--decidir` (ou o botão "Deixar a IA decidir" no painel) ela também
  **aceita** quando indica uma peça e **rejeita** quando conclui que nenhuma serve, em ambos os casos só com
  confiança de pelo menos 90 (`--confianca-minima`, de 50 a 100). Abaixo disso a pendência fica para uma pessoa.
  O aceite usa o mesmo caminho seguro do painel (reconsulta o anúncio e valida a peça); se ele falhar, a
  pendência continua aberta. A decisão fica registrada com `origem: "ia"`. **Rejeição não pode ser desfeita.**
- Sem `--decidir`, nada é aceito ou rejeitado pela IA: a recomendação (peça, confiança de 0 a 100,
  justificativa curta, modelo e versão do prompt) fica em `evidencias.sugestao_ia` da pendência.
- Entram só pendências que têm candidata aprovada e sem conflito. A resposta é validada: a peça indicada
  precisa ser uma das candidatas e a confiança, um inteiro de 0 a 100; caso contrário conta como falha.
- Pendência já analisada, com as mesmas candidatas e o mesmo anúncio, não gasta IA de novo (`--refazer` força).
- O texto do anúncio vai como dado, com instrução de ignorar ordens contidas nele; mesmo assim, o painel
  continua sendo quem aceita, e o aceite reconsulta o anúncio e valida a peça.
- Usa `GEMINI_API_KEY`; o modelo pode ser trocado com `IA_ANALISE_MODELO`. Não consome a cota diária de
  gerações dos usuários.
- No painel aparece a etiqueta "IA sugere (92%)" na pendência e a marca "Sugerida pela IA" na candidata,
  com a justificativa. `--loja` e `--categoria` filtram o lote.

No painel, cada pendência tem uma caixa de seleção, e há "Selecionar todas" e o botão **Enviar para a IA (n)**.
O painel envia em grupos de 20 (uma requisição à IA por grupo) e mostra o andamento; ao final recarrega a lista com as etiquetas da IA.

### Requisições à IA

O plano gratuito do Gemini limita as requisições por minuto, então as pendências vão **juntas**: até 20 por
requisição (`IA_ANALISE_LOTE`, padrão 20). A resposta traz uma entrada por pendência e cada uma é validada
separadamente: item ausente ou inválido fica sem sugestão e não estraga os demais. Se a resposta inteira
falhar (JSON cortado, por exemplo), o lote é dividido ao meio e reenviado. Para reduzir o risco de uma
resposta longa demais, mantenha o lote em torno de 20.
