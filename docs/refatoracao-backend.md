# Refatoração incremental do backend

Base: código local anterior à reorganização, incluindo importadores, requisitos
mínimos e melhorias de associação que ainda não estavam commitados. O primeiro
commit preserva essa base; não representa mudanças de algoritmo da refatoração.
Snapshots externos, bancos, credenciais e anexos não fazem parte desse commit.

Etapas: 1 base de comparação; 2 controllers funcionais; 3 regras OAuth Google;
4 estado de builds; 5 contexto/catálogo/custos/prompts; 6 seleção de plataforma;
7 validações; 8 geração/aparência/persistência; 9 apresentação de peças;
10 ofertas/enriquecimento; 11 descoberta/worker/seed; 12 limpeza; 13 verificação.

Contratos congelados: hashes de quatro prompts, dados da seed e DDL de todas as
tabelas/índices para SQLite e MySQL. Testes de comportamento existentes continuam
obrigatórios. A comparação não chama IA nem APIs externas.

## Resultado e limites da reorganização

Execução concluída em 06/11/2026. As mudanças são locais, sem push ou implantação.
A comparação começa em `6a9b1c4`, que preservou o trabalho anterior à refatoração.
Não houve alteração de frontend, esquema, migrations, configuração de implantação,
credenciais ou dados de produção nesta reorganização.

A estrutura continua MVC, com os repositories concretos que o projeto já usava.
Não foram introduzidas interfaces, classes base de services, injeção de dependência
por framework ou uma camada genérica de acesso ao banco.

```text
backend/
  controllers/                       funções de rota; HTTP, sessão e decorators
  models/                            tabelas, relacionamentos e acesso aos dados
  repositories/
    ofertas_repository.py            aplicação transacional de ofertas/histórico
    especificacoes_peca_repository.py preenchimento atômico de lacunas
    identificadores_peca_repository.py migração e reassinatura de identidades
  services/
    build_service/
      criar_build_service.py         coordena o pedido e o salvamento
      contexto_build_service.py      consulta fichas das peças próprias
      catalogo_geracao_service.py     catálogo e disponibilidade para geração
      custos_build_service.py        divisão do orçamento e subtotais
      seletor_inteligente_service.py  coordena a seleção inteligente
      selecionar_plataforma_service.py sockets, DDRs, cotas e sobras
      prompt_build_service.py        prompts originais e diagnóstico de correção
      gerar_candidata_service.py     chamada à IA, correção e aceitação
      ajustar_aparencia_service.py   alternativas de aparência com revalidação
      salvar_build_gerada_service.py prepara o estado que será persistido
      erros_build.py                erro estruturado de geração
      constantes_build.py           campos e categorias compartilhados
    validacoes_service/
      validar_pedido_build_service.py entradas da geração
      validar_estado_build_service.py estado editável de builds salvas
      validar_build_gerada_service.py integridade, preços, orçamento e restrições
      avaliar_compatibilidade_service.py diagnóstico técnico da combinação
      encaixe_fisico.py              dimensões, slots e encaixe
      armazenamento.py              interfaces, baias e conexões de discos
      conectores.py                 conexões necessárias
      requisitos_armazenamento_service.py capacidade mínima solicitada
    catalogo_service/
      pendencias_montagem_service.py requisitos técnicos das peças
      ler_plano_catalogo_service.py leitura e validação do plano do worker
    mercadolivre_service/
      descobrir_produtos_service.py coordenação da descoberta
      paginacao_descoberta_service.py páginas, cursor e filtro do grupo
      processar_catalogo_service.py agendamento, exclusão mútua e progresso
    peca_service/
      popular_pecas_service.py       execução da carga inicial
      dados_seed.py                 dados estáticos e composição da seed
    usuario_service/
      validar_retorno_google_service.py regras do retorno OAuth
  utils/
    ofertas_catalogo.py             representação da cotação legada no catálogo
```

A árvore destaca os arquivos reorganizados; os demais serviços especializados
continuam presentes. Os nomes existentes foram mantidos quando já expressavam uma
responsabilidade própria. O tamanho de listas estáticas e dos textos de prompt não
motivou fragmentação artificial. `Peca.to_catalogo()` permanece como serializador,
incluindo a extensão de `Fan`, para preservar esse contrato interno. Operações
atômicas de autenticação continuam nos Models, com suas proteções de concorrência.

## Fluxo da build e pontos que exigem atenção

1. A rota conserva seus decorators, código de resposta e contrato JSON.
2. O serviço de geração mantém o bloqueio por usuário e as condições originais de
   troca de provedor. O coordenador valida o pedido e consulta os limites da conta.
3. O catálogo tradicional ou o seletor inteligente prepara os candidatos. A seleção
   de plataformas conserva cotas por socket/DDR, redistribuição de vagas, preferências
   e tratamento das peças próprias. Os algoritmos de orçamento e ranking permanecem.
4. O prompt é construído com as mesmas instruções. A IA retorna a candidata; rede e
   ventilação são completadas nos mesmos momentos do fluxo anterior.
5. A candidata passa pela validação de integridade, orçamento e compatibilidade.
   O ajuste de aparência revalida cada alternativa. A capacidade mínima de
   armazenamento é conferida depois, como antes.
6. Quando aplicável, o reparo de orçamento tenta economizar e chama a validação
   completa para cada alternativa. Se não resolver, permanece a correção pela IA,
   com o limite anterior de tentativas e o diagnóstico estruturado.
7. A revisão opcional de investimento conserva a primeira resposta válida. Uma
   tentativa posterior inválida não elimina essa alternativa aprovada.
8. O estado é preparado e persistido com as mesmas transações e regras de limite.
   Builds manuais continuam permitindo estados incompletos; não receberam as
   exigências exclusivas da geração por IA.

O seletor não importa mais `CriarBuildService`: ambos reutilizam `gerar_candidata`.
A organização distingue geração, ajuste e validação sem deslocar verificações de
uma etapa para outra. Guardas repetidas na persistência foram preservadas quando
protegem chamadas diretas. O nome do logger do gerador foi mantido para conservar
os filtros operacionais existentes.

## Ofertas, fichas e rotinas administrativas

Os repositories movidos mantêm refresh, locks, comparação de assinaturas, commit,
rollback e confirmação opcional no mesmo ponto. O callback que reconfirma a
identidade continua dentro da transação. Não foi alterada a política de associação,
publicação, duplicidade ou criação de histórico. A renovação de tokens não foi
modificada.

Descoberta e paginação foram separadas sem mudar limites, offsets, cursores,
tratamento de 206/404/429 ou orçamento de requisições. O worker conserva agenda,
exclusão mútua, fases e retomada. Os comandos Flask existentes continuam sendo os
pontos de execução. A seed continua com os mesmos dados e preços.

## Remoções e evidências

A busca por referências abrangeu código, testes, comandos e nomes textuais do
repositório, além da revisão dos registros de rotas e chamadas indiretas.

| Removido | Evidência e operação preservada |
| --- | --- |
| `Peca.atualizar_preco` | Sem chamadores; atualização real usa `aplicar_cotacao`. Duas referências em diagramas foram atualizadas. |
| `Peca.buscar_mais_barata_por_part_number` | Sem referências além da declaração. |
| `Codigo.marcar_como_usado` | Sem chamadores; confirmação utiliza a operação atômica `confirmar_email`. |
| `TokenRecuperacao.marcar_como_usado` | Sem chamadores; recuperação utiliza `redefinir_senha`. |
| `ListarUsuariosService` | Sem importação, rota ou registro de execução. Era o único consumidor de `Usuario.listar_todos`, também removido. |
| Classes dos controllers | Rotas convertidas em funções; endpoints e decorators preservados e testados. |

`models/especificacoes_peca.py` e `models/identificadores_peca.py` foram movidos para
repositories, não descartados. Os cinco módulos técnicos de validação foram
movidos para `validacoes_service`, com suas referências atualizadas. Não foram
removidos migrations, comandos, modelos usados por registro SQLAlchemy, o
controller de peças ou helpers usados por diagnósticos administrativos.

## Commits por etapa

| Etapa | Commit | Conteúdo |
| --- | --- | --- |
| 1 | `6a9b1c4` | Preservação da base e caracterização |
| 2 | `02a5e47` | Controllers funcionais |
| 3 | `493039a` | Regras do retorno Google |
| 4 | `523ad3f` | Validação e edição do estado salvo |
| 5 | `d98a74a` | Contexto, catálogo, custos e prompts |
| 6 | `281d3e2` | Seleção de plataformas |
| 7 | `db27d94` | Pasta dedicada às validações |
| 8 | `722176e` | Geração, aparência e persistência |
| 9 | `e273eb9` | Requisitos técnicos fora do Model |
| 10 | `9004f52` | Persistência de ofertas e enriquecimento |
| 11 | `7c474a0` | Seed, paginação e plano do worker |
| 12 | `b5977cb` | Remoção comprovada de código e imports |
| 13 | Commit deste relatório | Verificação integrada e documentação |

## Verificações realizadas

Comando executado a partir de `backend/`:

```sh
ICECAT_INDICE= FABRICANTES_HABILITADOS=false ../venv/bin/python -m pytest -q
```

Resultado integrado após a limpeza: **1.781 testes aprovados, 18 ignorados,
20 subtestes aprovados e 235 avisos**, em aproximadamente 30 segundos.
Também foram executados grupos de testes a cada extração: controllers/usuários,
builds, catálogo, Mercado Livre, preços, inicialização e contratos.

As correções dos testes acompanharam os novos locais de importação e de mocks;
não foram alteradas expectativas de preço, compatibilidade, segurança ou respostas
HTTP para acomodar mudanças de comportamento. A remoção de `self` de uma função
exigiu ajustar o índice observado pelo spy, conservando a mesma build esperada.

A caracterização verifica hashes dos quatro prompts, do conteúdo completo da seed
e do DDL de tabelas e índices para SQLite e MySQL. Os hashes de referência não foram
atualizados para aceitar diferenças. A suíte inclui contratos de rotas, autenticação,
recusas, fallback de provedor, reparo de orçamento, peças próprias, cotas, aparência,
armazenamento mínimo, concorrência simulada, importação e idempotência.

Não houve chamada real à IA, coleta de anúncios, importação no banco do usuário
ou execução na VPS. Integrações que dependem de serviços externos e de MySQL
configurado foram ignoradas pelos testes. DDL compatível não substitui um teste de
concorrência em MySQL real. Os avisos de APIs legadas das dependências permanecem;
a atualização dessas dependências está fora desta refatoração.

## Manutenção e riscos restantes

- Alterações futuras na montagem devem preservar ordem, mutações da candidata,
  mensagens usadas no diagnóstico e o fallback da primeira resposta válida.
- O prompt e a validação já possuíam margens distintas em certas orientações de
  potência. Não houve mudança nessa política durante a reorganização.
- Não comparar respostas de duas chamadas externas à IA como prova de equivalência:
  usar a mesma resposta gravada e o mesmo catálogo nos testes.
- Alguns métodos de Models continuam contendo guardas transacionais e validações
  locais. Removê-las indiscriminadamente enfraqueceria chamadas diretas; esta etapa
  priorizou separar responsabilidades sem alterar atomicidade ou proteção.
- O código de fornecedores, matching e reparo mantém a complexidade necessária.
  Não foi reescrito para reduzir linhas nem houve alteração dos critérios de match.
- Antes da implantação, executar as integrações com uma base MySQL descartável e
  serviços de teste configurados. Não apontar a suíte para o banco de produção.
- `benchmarks/` e `.codex-attachments/` continuam fora dos commits desta etapa.
