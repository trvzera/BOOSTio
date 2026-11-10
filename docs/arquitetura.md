# Arquitetura do backend: regra do professor e desvios do projeto

Atualizado em 09/11/2026. Referência: https://github.com/gleisonbt/projeto-flask-sqlalchemy

## A regra (copiada do repositório do professor)

```text
Frontend -> Controller -> Service -> Model -> Banco
                             \-> Repository (só consulta que não é CRUD) -> Banco
```

| Camada | Faz | Não faz |
|---|---|---|
| **Model** (`db.Model`) | colunas; o CRUD da própria tabela (`salvar`, `atualizar`, `deletar`, `listar_todos`, `buscar_por_id`, `buscar_por_email`) com `commit`; `to_dict` | regra de caso de uso; importar service |
| **Service** (um por caso de uso, `executar`) | valida os dados, aplica a regra, chama a Model (ou o Repository) | `request`, `jsonify`, consulta SQL direta |
| **Repository** | só consulta que não é CRUD: relatório, filtro complexo, várias tabelas, ranking, stored procedure | regra de negócio; importar service |
| **Controller** (Blueprint) | lê a requisição, chama **um** service, devolve JSON e status; `except ValueError` → 400, `except SQLAlchemyError` → `db.session.rollback()` e 500; 404 quando o service devolve `None` | consulta ao banco, regra |

Na prática: **CRUD simples fica na Model**, **regra fica no Service**, **consulta especial fica no Repository**.

## Importante: o plano anterior foi desfeito

A primeira versão desta auditoria dizia que Model não pode consultar nem gravar e que o `rollback` deveria sair dos controllers. Isso é o contrário do que o professor ensina (a Model tem `salvar`/`deletar` com `commit` e o controller faz o `rollback`). A fase 1 feita nessa linha foi revertida e **o projeto volta a seguir o modelo do professor**: `ModeloBase.salvar/deletar` e o `rollback` nos controllers ficam.

## O que já está de acordo

- Controllers, services por caso de uso, models e repositories existem e têm o papel acima.
- Model com consultas (`Usuario.buscar_por_email`, `Peca.listar_publicadas`…) e com `commit` está **correto** nessa arquitetura.
- Controller captura `ValueError`/`SQLAlchemyError` e faz `rollback`, como no exemplo.

## O que foge da regra (a corrigir)

1. **Service consultando o banco direto** (quase resolvido em 09/11/2026): as consultas (`.query`) dos services passaram para métodos das Models (`Peca.buscar_por_codigo`, `Oferta.buscar_por_anuncio`, `Usuario.gravar_google_sub`, `ProdutoPendente.listar_ids_e_candidatos`…). Commit, rollback, add e flush continuam nos services (uma transação por caso de uso). Restam SQL puro em `migrar_ofertas_kabum_service` (migração de dados antigos) e um `UPDATE` por tabela refletida em `importar_benchmarks_service`.
2. ~~Model importando service ou repository~~ (resolvido em 09/11/2026): `Peca.cadastrar_ausentes`, `PlacaRede.atualizar_links_antigos`, `IdentidadeFabricante.registrar/para_matching` e `RevisaoIdentidadePeca.aplicar` viraram services; `MODELOS_PECAS` foi para `models/` e `validar_url_shopee` para `utils/`. Nenhum model importa `services` ou `repositories`.
3. ~~Repository importando service e com regra de negócio~~ (resolvido em 09/11/2026): os 8 arquivos que decidiam o que gravar (`importacao_buildcores`, `importacao_catalogo`, `catalogo_tecnico`, `dataset_pecas`, `enriquecimento_buildcores`, `especificacoes_peca`, `reavaliacao_montagem`, `ofertas`) passaram para `services/` com nome `gravar_*_service`. Em `repositories/` ficaram só os de acesso (fila, tokens, ofertas da KaBuM, identificadores, controle do catálogo, saúde, migração de links), e nenhum importa `services`.
4. ~~Controller com lógica de protocolo~~ (resolvido em 09/11/2026): a leitura do `state` do OAuth foi para `estado_oauth_service` e a validação do `Retry-After` da IA para `espera_ia_service`. Os controllers só traduzem as exceções em resposta HTTP.
5. ~~Código morto: `controllers/peca_controller.py`~~ (removido em 09/11/2026, com o `MostrarPecasService` e seus testes).
6. **Arquivos que não são Model dentro de `models/`**: `medidas_fisicas`, `imagens_referencia`, `campos_tecnicos` (regra e dados de domínio) e `preco_oferta` (colunas calculadas injetadas).
7. **Dados em `services/`**: `dados_seed.py` (1.247 linhas) e os arquivos `pecas_*` que ele junta. Mantidos onde estão por enquanto: mover só um deles separaria a seed de seus dados e não muda a arquitetura.
8. **Front-end**: não auditado; conferir se `forms.js`, `melhorias.js`, `configuracao-build.js` e `configuracoes.js` misturam regra com tela.

## Ordem sugerida

1. (feito) Código morto (`peca_controller`).
2. (feito) Models que importam service/repository.
3. (feito) Repositories que importam service e têm regra.
4. (feito) Services que consultam direto.
5. (feito) Lógica de protocolo nos controllers.
6. Arquivos de domínio em `models/` (item 6).

Cada passo em um commit, sem mudar resposta da API, esquema, seed nem DDL, com a suíte inteira passando.
