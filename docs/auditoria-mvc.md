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

1. **Service consultando o banco direto** (`db.session`/`Model.query`) em 19 arquivos, em vez de chamar a Model ou o Repository: `completar_pecas_icecat`, `autorizar_conta`, `descobrir_produtos`, `processar_catalogo`, `importar_produto`, `aprovar_em_lote`, `preencher_especificacoes`, `importar_benchmarks`, `atualizar_preferencias_uso`, `vincular_google`, `configurar_acesso`, `salvar_peca`, `restaurar_links_kabum`, `migrar_ofertas_kabum`, `importar_base_tecnica`, `revisar_ficha`, `converter_referencias_gpu`, `preencher_fichas_originais`, `pendencias_acionaveis`.
2. **Model importando service ou repository** (10 pontos, quase todos `import` dentro de função para fugir de ciclo): `revisao_identidade_peca`, `identidade_fabricante`, `oferta`, `peca`, `placa_rede`. A Model não deve conhecer service; a regra sobe para o service.
3. **Repository importando service** (25 pontos) e com regra de negócio (`importacao_buildcores`, `ofertas`, `identificadores_peca`, `especificacoes_peca`, `catalogo_tecnico`, `dataset_pecas`, `enriquecimento_buildcores`, `importacao_catalogo`). Repository só consulta; a decisão vai para o service.
4. **Controller com lógica de protocolo**: `auth_controller` lê o `state` do OAuth (`parse_qs`) na rota; `build_controller` trata 429/`Retry-After` da IA dentro da rota. Isso vai para o service.
5. ~~Código morto: `controllers/peca_controller.py`~~ (removido em 09/11/2026, com o `MostrarPecasService` e seus testes).
6. **Arquivos que não são Model dentro de `models/`**: `medidas_fisicas`, `imagens_referencia`, `campos_tecnicos` (regra e dados de domínio) e `preco_oferta` (colunas calculadas injetadas).
7. **Dados em `services/`**: `dados_seed.py` (1.247 linhas) e os arquivos `pecas_*` que ele junta. Mantidos onde estão por enquanto: mover só um deles separaria a seed de seus dados e não muda a arquitetura.
8. **Front-end**: não auditado; conferir se `forms.js`, `melhorias.js`, `configuracao-build.js` e `configuracoes.js` misturam regra com tela.

## Ordem sugerida

1. (feito) Código morto (`peca_controller`).
2. Models que importam service/repository (item 2): mover a regra para o service.
3. Repositories que importam service e têm regra (item 3).
4. Services que consultam direto (item 1): passar a chamar Model/Repository.
5. Lógica de protocolo nos controllers (item 4).
6. Arquivos de domínio em `models/` (item 6).

Cada passo em um commit, sem mudar resposta da API, esquema, seed nem DDL, com a suíte inteira passando.
