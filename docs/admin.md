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
- A página confere o papel e leva quem não for administrador à tela de erro 403.
- **O que protege de verdade é o servidor:** toda rota `/admin/*` usa `@login_required` e `@apenas_administrador`
  (401 sem login, 403 sem o papel) e as ações de escrita exigem o token CSRF como no resto do site.

## Pendências

Lista os anúncios de `produto_pendente` (por padrão `em_revisao`), com filtros de situação, loja e categoria.

| Rota | O que faz |
| --- | --- |
| `GET /admin/pendencias` | Lista com `status`, `loja`, `categoria`, `limite` e `depois_id` (cursor). |
| `GET /admin/pendencias/<id>` | Detalhe com os candidatos (peça, pontuação, conflitos e o que falta comprovar). |
| `POST /admin/pendencias/<id>/aceitar` | `{"peca": "categoria:id"}`: cria a oferta e o vínculo. |
| `POST /admin/pendencias/<id>/rejeitar` | `{"motivo": "..."}` (opcional, até 200 caracteres). |

Regras do aceite:

- Só vale para uma das peças candidatas daquela pendência, sem conflito, aprovada e da mesma categoria.
- Usa o mesmo caminho de gravação da busca automática: trava da coleta, peça inalterada desde a análise e
  anúncio que não pertence a outra peça. Só a decisão automática de "confirmada" é dispensada, porque quem
  decidiu foi uma pessoa; o `administrador_id` e a data ficam em `evidencias.revisao_manual`.
- **Hoje só a Shopee pode ser aceita pelo painel.** Para o Mercado Livre o aceite continua sendo
  `mercadolivre-vincular` (exige consulta à API do Mercado Livre); no painel o Mercado Livre pode ser visto
  e rejeitado.
- Pendência já aceita ou rejeitada não é reaberta (nem pelas buscas seguintes).
