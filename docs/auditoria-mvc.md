# Auditoria de arquitetura MVC do backend

Data: 09/11/2026. Só diagnóstico: nenhum código foi alterado.

## Como foi feita

- Contagem de linhas, funções, consultas ao banco, commits e importações entre camadas em todo o `backend/`.
- Leitura completa dos models com mais regra (`peca`, `oferta`, `usuario`, `codigo`, `build`) e das assinaturas dos demais.
- Leitura de amostras de controllers, repositories e services.
- **Não** li linha a linha os 198 arquivos de `services/` nem o front-end. Esses pontos estão marcados como "a confirmar" e entram na primeira fase de cada etapa da mudança.

## Regra que o projeto deve seguir (proposta)

| Camada | Pode | Não pode |
|---|---|---|
| **Model** | colunas, relacionamentos, constraints, índices | consultar, gravar, validar regra de negócio, formatar resposta, importar service ou repository |
| **Repository** | consultar e gravar (`add`, `flush`, `filter`, `update`) | regra de negócio, importar service, `commit` ou `rollback` |
| **Service** | regra de negócio, validação, `commit` e `rollback` (uma transação por caso de uso), chamar repositories | `request`, `jsonify`, HTTP |
| **Controller** | ler a requisição, chamar **um** service, montar a resposta HTTP | consultar banco, regra, `rollback` |
| **View (front)** | telas e chamadas à API | regra de negócio duplicada |

## Números atuais

| Camada | Arquivos | Linhas | Problema medido |
|---|---|---|---|
| models | 47 | 2.744 | 106 métodos de classe/estático, 198 linhas com `query`/`db.session`, 39 `commit`, 10 importações de services/repositories |
| repositories | 16 | 1.267 | 25 importações de services, regra de negócio dentro, 10 `commit` |
| services | 198 | 15.487 | 18 arquivos usam `db.session`/`query` direto, 8 `commit` |
| controllers | 9 | 960 | 19 `db.session.rollback()` copiados, mapeamento de erros repetido |

## 1. Models com lógica (o problema mais grave)

### Padrão que se repete
- **Consulta dentro do model**: `Usuario.buscar_por_email`, `Peca.listar_publicadas`, `Build.listar_por_usuario`, `ProdutoPendente.listar_para_admin`, etc. Isso é papel de repository.
- **`commit` dentro do model**: `ModeloBase.salvar/deletar`, `Usuario.atualizar_*`, `Codigo.emitir`, `Build.criar_gerada`. Quem decide a transação deve ser o service.
- **Regra de negócio dentro do model**: validações, limites, transições de estado.
- **Apresentação dentro do model**: `to_dict`, `to_catalogo`, `para_exibicao`. Formatar resposta não é papel do model.
- **Model importa service/repository** (dependência invertida e circular).

### Arquivo por arquivo

| Model | O que está errado | Para onde vai |
|---|---|---|
| `base.py` | `salvar()` e `deletar()` fazem `commit` | sai; o service faz o `commit` |
| `peca.py` (240 linhas, 27 funções) | 15 consultas (`consulta_publicavel`, `consulta_catalogo`, `listar_publicadas`, `lote_para_*`, `buscar_por_nome`, `listar_disponiveis_ate`…), `cadastrar_ausentes` (regra de cadastro + `commit`), `to_catalogo` (apresentação), `situacao_catalogo` e `publicavel` (regra), `__init__` com regra e importação de utils, `definir_imagem` com `commit`, importa `ofertas_kabum_repository` | consultas → `repositories/peca_repository.py`; regras e `cadastrar_ausentes` → services de peça; `to_catalogo` → apresentador em services |
| `oferta.py` (223) | `identidades_kabum_ambiguas`, `registrar_identidade_kabum`, `anexar_a_catalogo` (consulta + regra), `verificar_esquema_mercado_livre` (inspeciona o banco), `shopee_validada` (regra), `para_exibicao` (apresentação), importa services | repository de ofertas + services + apresentador |
| `produto_pendente.py` (217, 35 acessos ao banco) | 12 consultas/gravações, `registrar_descobertos`, `registrar_matching`, `registrar_enriquecimento`, `rejeitar` (regra + gravação) | repository de pendências + services de pendência |
| `build.py` (177) | `criar_gerada` (valida as regras da build e grava), `to_dict`, 3 consultas | validação → service; consultas → repository; `to_dict` → apresentador |
| `build_salva.py` (166, 24 acessos) | `criar_limitada`, `migrar_geradas`, `verificar_espaco`, `definir_setup_atual`, `excluir_com_original`, `gravar_estado`, `to_dict`, importa todos os models de peça | repository + services |
| `usuario.py` (127) | `atualizar_dados` (regra de troca de e-mail e senha), `desativar`, `alterar_administrador`, `vincular_google_legado`, 6 consultas, tudo com `commit` | repository + services de usuário |
| `codigo.py` (107) | `emitir`, `confirmar_email`, `verificar_limite_envio` (limite de envio é regra de negócio), `registrar_tentativa` | repository + service de e-mail |
| `token_recuperacao.py` (92) | `emitir`, `redefinir_senha`, hash do token | repository + service |
| `token_integracao.py` (141) | cifra/decifra token com `Fernet` e `current_app`, `ler_estado`/`gravar_estado` com controle de versão | cifra → service; estado → repository |
| `identidade_fabricante.py` (105) | `registrar` (regra + importa repository), `localizar`, `para_matching` | repository + service |
| `vinculo_mercado_livre.py` (79) | `registrar_revisado`, `aplicar_revisado` (regra), `tabela_preparada` (inspeciona o banco) | repository + service |
| `revisao_identidade_peca.py` (70) | `aplicar` (regra + importa repository e services) | service |
| `consulta_preco.py`, `historico_preco.py`, `estado_catalogo.py`, `ficha_tecnica_catalogo.py`, `autorizacao_mercado_livre.py`, `execucao_descoberta.py`, `placa_rede.py` | consultas, `reservar/confirmar/ignorar`, `transicionar`, `registrar_observacao` (arredondamento de preço), `criar/consumir`, importam repositories | repository + service de cada tema |
| `preco_oferta.py` | `instalar_precos_derivados` injeta colunas calculadas (`column_property`) nos models de peça | mantém só o que for coluna calculada de SQL; o resto vai para repository |
| `medidas_fisicas.py`, `imagens_referencia.py`, `campos_tecnicos.py` | não são models: são regras e dados de domínio dentro de `models/` | mover para `services/` ou `utils/` |
| `placa_mae`, `memoria_ram`, `placa_rede`, `processador` e demais peças | quase só colunas (corretos), exceto `placa_rede` | manter |

## 2. Repositories com lógica

- **Regra de negócio** (não deveriam ter):
  - `importacao_buildcores_repository.py` (214 linhas): pontuação, guardas de GPU, comparação de fichas. Isso é service.
  - `ofertas_repository.py` (203): regras de ofertas, vínculos e desativação.
  - `identificadores_peca_repository.py`, `especificacoes_peca_repository.py`, `catalogo_tecnico_repository.py`, `dataset_pecas_repository.py`, `enriquecimento_buildcores_repository.py`, `importacao_catalogo_repository.py`: decidem o que gravar, não só gravam.
- **Dependência invertida**: 25 importações de `services` e `utils` dentro de repositories (um repository não pode conhecer um service).
- **Nomes que mentem**: `ofertas_kabum_repository`, `fila_marketplace_repository` e `mercado_livre_token_repository` são os mais próximos do padrão certo (consultam e gravam). Os demais precisam ser divididos em repository (acesso) + service (regra).
- Faltam repositories para o que hoje está nos models: peça, oferta, usuário, código, token, build, build salva, pendência.

## 3. Services

- 18 arquivos acessam `db.session`/`query` direto, sem passar por repository (por exemplo `migrar_ofertas_kabum_service`, `aprovar_em_lote_service`, `vincular_google_service`, `salvar_peca_service`, `importar_benchmarks_service`).
- 8 `commit` espalhados: o padrão certo (um commit por caso de uso) existe só em parte.
- Arquivos grandes que misturam várias responsabilidades (a confirmar na leitura): `prompt_build_service` (472), `seletor_inteligente_service` (367), `sugerir_pendencia_service` (256), `encaixe_fisico` (254), `ajustar_orcamento_build_service` (237), `avaliar_compatibilidade_service` (230). Eles são regra mesmo (lugar certo), mas podem ser quebrados em passos menores.
- `dados_seed.py` (1.247 linhas) é dado, não serviço: deveria ficar em `data/`.

## 4. Controllers

- `db.session.rollback()` copiado 19 vezes e `except SQLAlchemyError` repetido em quase toda rota. É persistência dentro do controller. Solução: um único tratador de erro no `app.py`.
- O mapeamento de exceções para HTTP (`ValueError` → 400, `LookupError` → 404…) é repetido; só `admin_controller` tem o helper `_responder`. Deve ser um tratador único.
- `build_controller` (248 linhas) trata erros específicos da IA (429, `Retry-After`) dentro da rota: deve virar exceção própria do service, traduzida em um lugar só.
- `peca_controller.py` não está registrado no `app.py` (código morto).
- `auth_controller` faz leitura de `state` da URL do OAuth e `parse_qs` na rota: lógica de protocolo que deveria estar no service.

## 5. Migrations, commands e utils

- `migrations/` (625 linhas) e `commands/` (1.058): lugar certo para esquema e CLI. `commands/catalogo.py` e `marketplaces.py` têm laços e regras de enfileiramento (`_enfileirar_categoria`) que são de service. A confirmar.
- `utils/`: `codigos_peca`, `identidade_peca` e `validacoes` são regras de negócio disfarçadas de utilitário (devem ir para services); `csrf`, `decorators`, `limite_requisicoes`, `sockets`, `aparencia` são infraestrutura (ok).

## 6. Front-end (View)

- Estrutura boa: `api/` (chamadas), `pages/`, `components/`, `build/`.
- A confirmar: `pages/forms.js` (687 linhas), `build/melhorias.js` (482), `pages/configuracao-build.js` (435) e `pages/configuracoes.js` (367) provavelmente misturam DOM e regra. Não li.

## Plano de mudança (do mais simples ao mais arriscado)

Cada fase termina com todos os testes passando e sem mudar comportamento, esquema, DDL, seed nem resposta da API (os "contratos congelados" de `docs/refatoracao-backend.md`).

1. **(feita em 09/11/2026) Transação e erros**: um `errorhandler` para `SQLAlchemyError` e outro para `ValueError`/`LookupError`; remover os 19 `rollback` e os `except` repetidos dos controllers; remover `salvar/deletar` do `ModeloBase`. Baixo risco, ganho visível. Resultado: os `rollback` saíram dos controllers (`utils/transacao.py` desfaz a transação quebrada ao fim da requisição) e o `ModeloBase` não grava mais; as mensagens de erro de cada rota ficaram iguais.
2. **Usuário e e-mail**: `Usuario`, `Codigo`, `TokenRecuperacao` viram só colunas. Criar `usuario_repository`, `codigo_repository`, `token_recuperacao_repository` e mover as regras para os services que já existem.
3. **Builds**: `Build`, `BuildSalva` só colunas; `build_repository`; validação de `criar_gerada` vai para `validacoes_service`; `to_dict` vai para um apresentador.
4. **Peças**: `Peca` só colunas; `peca_repository` com as 15 consultas; `to_catalogo` e `situacao_catalogo` para service/apresentador; `cadastrar_ausentes` vira service. Maior fase (a classe é herdada por 15 tabelas).
5. **Ofertas e preços**: `Oferta`, `HistoricoPreco`, `ConsultaPreco`, `preco_oferta`.
6. **Pendências, identidade, vínculos, fichas, tokens de integração, estado do catálogo**.
7. **Repositories**: separar regra de acesso (`importacao_buildcores`, `ofertas`, `identificadores`, `especificacoes`, `catalogo_tecnico`…) e eliminar as 25 importações de services.
8. **Limpeza**: services que usam `db.session` direto passam a usar repository; `utils` de regra vão para services; `dados_seed.py` para `data/`; remover o `peca_controller` morto.

## Riscos e como controlar

- A suíte tem 131 arquivos de teste; muitos chamam métodos dos models (`Peca.cadastrar_ausentes`, `Usuario.buscar_por_email`…). Ao mover um método, os testes que o chamam são atualizados na mesma mudança.
- `Peca` e `ModeloBase` são herdados por 15+ tabelas: mudar a base afeta todas. Por isso a fase 4 é feita por último entre os models e com o DDL congelado como teste.
- Produção (MySQL) não muda: nenhuma fase altera esquema nem dados.
- Cada fase em um commit separado, para reverter só ela se preciso.

## Regra de simplicidade (para o código final)

- Um arquivo, uma responsabilidade; nome diz o que faz.
- Funções curtas, sem aninhamento profundo; mais linhas, mas cada uma óbvia.
- Sem `import` dentro de função para fugir de ciclo: se há ciclo, a responsabilidade está na camada errada.
- Um `commit` por caso de uso, sempre no service.
