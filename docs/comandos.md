# Comandos da BOOSTio

Todos rodam a partir de `backend/`: `python -m flask --app app <comando>`. Na VPS, dentro do Docker, os
scripts de `deploy/` já fazem isso. A maioria **simula por padrão** e só grava com `--aplicar`. Os comandos
`*-preparar` criam ou ajustam tabelas, são seguros para repetir e pedem backup em banco já existente.

## 1. Os do dia a dia (atualizar preços e ofertas)

| Comando | Para que serve |
| --- | --- |
| `precos-atualizar` | Atualiza preço e estoque da **KaBuM** (um anúncio por vez). Agendado por `deploy/atualizar_precos.sh`. |
| `mercadolivre-ofertas-atualizar` | Atualiza as ofertas do **Mercado Livre** das peças. Script: `deploy/atualizar_ofertas_mercadolivre.sh`. |
| `marketplaces-enfileirar-ofertas` | Põe na fila uma tarefa de ofertas por peça, para **Mercado Livre ou Shopee**. Uma categoria por vez. |
| `marketplaces-worker` | Executa a fila acima (processo que fica rodando). `--uma-vez` processa uma tarefa por loja e termina. |
| `marketplaces-fila-resumo` | Mostra quantas tarefas estão pendentes, em andamento, concluídas ou com falha. |
| `marketplaces-fila-reativar` | Libera uma loja bloqueada (ex.: credencial vencida) depois de você corrigir o problema. |
| `shopee-descobrir` | Procura anúncios novos na Shopee por termo. Com `--gravar-catalogo --permitir-novos` pode cadastrar peça nova. |
| `pecas-imagens` | Baixa a foto principal das peças que têm link da KaBuM e ainda não têm imagem. |

## 1b. Administradores

| Comando | Para que serve |
| --- | --- |
| `usuario-promover-admin --email ...` | Torna a conta administradora e encerra as sessões dela. |
| `usuario-remover-admin --email ...` | Retira o papel. |
| `usuario-listar-admins` | Mostra quem é administrador. |

## 2. Preparar o banco (normalmente uma vez por versão)

| Comando | Para que serve |
| --- | --- |
| `banco-preparar` | Cria as tabelas e aplica as migrações em SQLite/banco novo. Não coleta preço. |
| `banco-atualizar-mysql` | Migração de benchmarks para um MySQL existente (simula; `--aplicar` grava). Script: `deploy/atualizar_banco_mysql.sh`. |
| `ofertas-kabum-migrar` | **Novo:** copia link, preço e estoque da KaBuM das peças para a tabela de ofertas. Script: `deploy/migrar_ofertas_kabum.sh`. |
| `marketplaces-fila-preparar` | Cria as duas tabelas da fila de marketplaces. |
| `mercadolivre-ofertas-preparar` | Cria as tabelas de ofertas do Mercado Livre. |
| `mercadolivre-vinculos-preparar`, `mercadolivre-identidades-preparar`, `mercadolivre-autorizacao-preparar` | Criam as tabelas de vínculos, de MPNs revisados e de autorização do Mercado Livre. |
| `integracoes-tokens-preparar` | Cria a tabela de tokens das integrações. |
| `historico-precos-preparar` | Cria a tabela do histórico antigo de preços. |
| `catalogo-preparar` | Prepara as tabelas do catálogo automatizado (pendências, validação das peças). |
| `catalogo-tecnico-preparar` | Ajusta as tabelas de peças para aceitar ficha técnica sem preço. |
| `dataset-pecas-preparar` | Prepara a importação do dataset público de peças. |
| `preferencias-preparar` | Cria a tabela de preferências do usuário. |
| `usuarios-admin-preparar` | Adiciona `usuario.administrador` (simula; `--aplicar` grava). Ver [admin.md](admin.md). |
| `precos-migrar`, `migrar-budget` | Migrações antigas de SQLite (links; orçamento do usuário). |

## 3. Cadastrar e importar peças

| Comando | Para que serve |
| --- | --- |
| `pecas-popular` | Carga inicial do catálogo (seed); com `--atualizar-precos` consulta a KaBuM em seguida. |
| `pecas-complementares` | Adiciona fans, periféricos e gabinetes revisados, sem mexer em preços. |
| `peca-links` | Define ou remove o link da KaBuM de uma peça. |
| `pecas-restaurar-links` | Repõe links conhecidos da seed onde a peça está sem link. |
| `buildcores-baixar` / `buildcores-importar` / `buildcores-cruzar` | Baixa, importa e cruza fichas técnicas do BuildCores com o catálogo. |
| `dataset-pecas-baixar` / `dataset-pecas-importar` | Baixa e importa o dataset público de peças (só ficha técnica). |
| `catalogo-tecnico-importar` / `-listar` / `-revisar` | Importa fichas técnicas em JSON, lista o que existe e revisa/aprova. |
| `benchmarks-importar` | Preenche benchmarks de CPU/GPU nas peças já cadastradas. |

## 4. Descoberta e importação do Mercado Livre (etapas em sequência)

| Comando | Para que serve |
| --- | --- |
| `mercadolivre-descobrir` | Busca anúncios no Mercado Livre e guarda como pendências. |
| `mercadolivre-classificar` | Compara cada pendência com o catálogo e decide: confirmada, ambígua ou rejeitada. |
| `mercadolivre-enriquecer` | Completa a ficha técnica das pendências (Icecat, fabricante, base técnica). |
| `mercadolivre-importar-pendencias` | Cria a oferta (e a peça, se permitido) a partir das pendências aprovadas. |
| `catalogo-worker` / `catalogo-worker-reiniciar` | Rodam essas quatro etapas sozinhas, em ciclo e com retomada; o segundo zera o ponto de retomada. |
| `mercadolivre-vincular` | Registra à mão a associação entre uma peça e um produto do catálogo do Mercado Livre. |
| `mercadolivre-vinculos-importar`, `mercadolivre-identidades-importar` | Aplicam manifestos revisados de vínculos e de MPNs. |

## 5. Conectar o Mercado Livre (configuração)

| Comando | Para que serve |
| --- | --- |
| `mercadolivre-conectar` | Gera um link de uso único (10 min) para autorizar a conta. Não compartilhe. |
| `mercadolivre-tokens-configurar` | Registra o par de tokens OAuth sem mostrá-lo. |
| `mercadolivre-tokens-transferir` | Move tokens de um arquivo antigo para o banco. |
| `mercadolivre-validar` | Confere configuração, tabelas e tokens, sem rede e sem gravar. |

## 6. Qualidade e diagnóstico (só leitura, ou simulam)

| Comando | Para que serve |
| --- | --- |
| `catalogo-auditar` | Valida o catálogo e os arquivos locais. |
| `catalogo-planejar`, `catalogo-planejar-pecas` | Geram o plano de pesquisas (por categoria/marca ou por peça). |
| `catalogo-montagem-reavaliar` | Reavalia se cada peça tem o mínimo técnico para montar build. |
| `catalogo-especificacoes-preencher`, `catalogo-fichas-originais` | Completam e conferem fichas usando dados já coletados. |
| `catalogo-gpus-converter-referencias`, `catalogo-identificadores-separar` | Correções pontuais de GPUs genéricas e de códigos (MPN, referência, ID da loja). |
| `icecat-consultar`, `icecat-indice-preparar` | Consulta uma ficha do Icecat para diagnóstico; monta o índice local. |
| `fabricantes-consultar` | Consulta páginas oficiais de fabricantes e mostra as evidências. |

## Como escolher

- **Quero preço atualizado:** `precos-atualizar` (KaBuM) e fila + worker (Mercado Livre e Shopee).
- **Subi uma versão nova:** os `*-preparar` / scripts de `deploy/`, com backup.
- **Quero peças novas:** seção 3, ou `shopee-descobrir` / `catalogo-worker`.
- **Algo está estranho:** seção 6, que não altera dados.
