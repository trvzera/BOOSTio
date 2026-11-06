# Associação inteligente entre lojas

O núcleo está em `services/catalogo_service/associacao_inteligente_service.py`. Ele recebe um `ProdutoNormalizado`, não uma resposta de API. Nenhum domínio MLB, atributo Mercado Livre, token ou chamada HTTP participa do cálculo. Adaptadores de cada loja traduzem seus dados para esse contrato.

## Organização

- `AssociacaoInteligenteService`: coordena funções de identificadores, marca, título, modelo e especificações e decide a associação.
- `CompararNomesService`: normalização comercial e semelhança somente para triagem; preserva números, sufixos, RGB, Wi-Fi, revisões e edições.
- `ConferirEspecificacoesService`: compara os campos essenciais de cada categoria e os dados explícitos extraídos do título.
- `ClassificarPendenciasService`: classifica a fila de qualquer loja com dados normalizados ou um normalizador injetado.
- `ValidarFichaTecnicaService`: requisitos dos models e fontes antes de cadastrar um componente novo.
- `ConsultarBaseHardwareService`: consulta complementar em snapshot técnico local, sem rede.
- `ImportarCatalogoService`: transação compartilhada, reconsulta de duplicatas e persistência de ofertas.
- `ConsultarBenchmarkCatalogoService`: consulta local compartilhada dos CSVs existentes.

A pasta `mercadolivre_service` mantém coleta, OAuth, tradução de atributos e pequenas fachadas compatíveis com os comandos existentes. `NormalizarProdutoService` é o adaptador Mercado Livre. A API de uma futura loja deverá produzir `ProdutoNormalizado` e consultar sua oferta atual antes de chamar a importação comum. Não foram inventados endpoints para lojas ainda não integradas.

## Pontuação e decisão

A pontuação é uma heurística explicável, **não uma probabilidade estatística**:

| Evidência | Pontos máximos |
|---|---:|
| Marca | 10 |
| Modelo comercial | 35 |
| Título | 15 |
| Especificações essenciais | 40 |

Marca explícita vale 10; marca identificada somente no título vale 8. Modelo exato ou uma identidade técnica equivalente (como a família e o SKU de CPU) pode valer 35. Semelhança textual parcial serve à triagem e nunca permite associação automática sozinha. MPN ou GTIN comprovado oferece uma via conclusiva a partir de 95 pontos, mantendo os bloqueios por contradições.

- **Acima de 80:** associação automática se houver um único candidato forte, busca completa e margem de pelo menos 10 pontos para o segundo.
- **De 60 a 80, inclusive:** avaliação.
- **Abaixo de 60:** descarta a associação à peça existente; tenta complemento/cadastro de produto novo conforme requisitos. Dados insuficientes continuam em quarentena para enriquecimento/revisão, sem publicar um componente incompleto.

60 e 80 exatos ficam em avaliação. Dois candidatos acima de 80, busca truncada ou identificador já cadastrado com ficha contraditória reduzem a decisão global para avaliação. O score individual não autoriza escolher arbitrariamente entre duplicatas. A decisão guarda percentual, versão, parcelas, evidências e conflitos. Apenas os dez melhores candidatos são persistidos; todos os candidatos carregados são avaliados antes desse recorte.

Sem MPN/GTIN, a confirmação exige modelo comercial exato e especificações essenciais comprovadas. Campos ausentes, categoria apenas sugerida, anúncio sem estado conhecido ou revisão/variante não confirmada limitam a pontuação a 80. Uma contradição técnica, de marca, de modelo ou de identificador leva a zero, mesmo quando outros campos coincidem. Isso evita compensar um socket ou modelo errado com pontos de palavras parecidas.

## Especificações e variantes

CPU: socket, núcleos e threads, preservando família, geração e sufixos. RAM: capacidade total, DDR, frequência com unidade comparável, módulos, latência e formato DIMM/SO-DIMM. Placa-mãe: modelo, socket, DDR e formato. GPU: modelo comercial da montadora e memória; o chip isolado não comprova uma edição de placa. Armazenamento: modelo, capacidade e interface/tipo; HD também exige rotação. Fonte: modelo, potência e formato. As categorias sem perfil suficiente continuam em avaliação sem identificador conclusivo.

CLOCK mínimo de CPUs híbridas pode representar outro grupo de núcleos; não é usado como contradição automática de identidade. SATA genérico não prova SATA III na via sem identificador. MT/s não vira MHz silenciosamente. Kits de RAM exigem quantidade consistente; combos de outras categorias ficam bloqueados. Informações ausentes não viram zero ou false.

A memória recebeu `formato` nullable: os registros atuais permanecem desconhecidos. A migração `catalogo-preparar` adiciona a coluna de modo aditivo em SQLite/MySQL. Não infere DIMM apenas porque a descrição não contém “notebook”. Faça a simulação e aplique a migração antes de iniciar o código novo sobre um banco antigo:

```bash
python -m flask --app app catalogo-preparar
python -m flask --app app catalogo-preparar --aplicar
```

## Complemento técnico

Foi incluído o snapshot `pc-builder-parts.json`, versão declarada 2.1.1, do [TechFuelHQ/iBlessi](https://github.com/iBlessi/pc-builder-parts), com a licença CC BY 4.0 e atribuição preservadas em `backend/data/hardware/`. São 126 registros, não uma promessa de cobertura do catálogo inteiro.

O adaptador consulta somente o arquivo local, escolhe uma correspondência única de marca/modelo e verifica as especificações disponíveis. Apenas linhas com URL de fonte e data válida participam do preenchimento; evidências incluem URL, referência, data, licença e SHA-256. A base só completa campos ausentes. Divergências entre fontes exigem avaliação. Os dados e datas são os declarados pelo publicador, não uma auditoria independente de todas as fichas.

Preço, estoque, notas editoriais, tiers e FPS não são extraídos dessa base. GPU genérica “NVIDIA AIB” não identifica uma placa ASUS/MSI/Gigabyte. Sem uma ficha completa, fontes por campo e identidade suficiente, nenhum componente novo é publicado. MPN não é obrigatório para um novo componente; nesse caso o campo permanece nulo e não criamos um código de fabricante fictício.

## Execução e testes

Os comandos existentes `mercadolivre-classificar`, `mercadolivre-enriquecer` e `mercadolivre-importar-pendencias` continuam funcionando, por padrão em simulação. A criação de novos continua optativa com `--permitir-novos`; sem `--aplicar`, nada é confirmado no catálogo.

Os testes incluem limites 60/80, diferentes lojas, correspondência por título sem MPN, conflitos fortes, DIMM/SO-DIMM, códigos divergentes, múltiplos candidatos, cadastro novo sem MPN e repetição sem duplicatas. Testes com respostas reais salvas são reprodução offline: não medem disponibilidade atual de endpoints nem cobertura de uma pesquisa ao vivo.

## Catálogo amplo — associação v7

`IndiceCandidatosService` carrega a categoria inteira pelo método
`Peca.iterar_para_matching`, em páginas de 500 IDs. O antigo corte nos primeiros
2.000 registros foi removido da classificação, importação, enriquecimento, verificação
de unicidade do Mercado Livre e importação de bases técnicas. O índice é compartilhado
entre lojas; não interpreta payloads do Mercado Livre.

A busca usa marca normalizada e MPN/GTIN para reduzir o conjunto antes do comparador:
marca explícita diferente pode ser eliminada, mas identificadores iguais continuam
na comparação para detectar contradições. Sem marca explícita, toda a categoria
participa. Nenhum recorte por similaridade textual descarta candidatos silenciosamente.
Os dez resultados do diagnóstico são apenas apresentação, não limite de busca.
`total_catalogo`, `descartados_por_marca` e `total_candidatos_avaliados` explicam o recorte.

A classificação mantém um snapshot de campos comparáveis por lote. Isso evita
consultas individuais quando a gravação de um diagnóstico expira os objetos ORM.
O snapshot não duplica os grandes documentos técnicos brutos. Não há cache global
persistente: a importação recarrega o índice e revalida dentro do bloqueio transacional.
As páginas do model são materializadas antes da consulta de identidades, evitando
consultas aninhadas durante um cursor MySQL não bufferizado.

Outras proteções da v7:

- Código comercial completo também pode ser reconhecido no título. GPUs preservam
  SKUs hifenizados, como `DUAL-RTX4060-O8G-EVO`, sem transformar o chip em edição comercial.
- Título e atributos são confrontados mesmo quando falta o campo correspondente na
  peça local. MPN igual não mascara uma contradição explícita.
- SO-DIMM cadastrado é reconhecido mesmo quando o modelo não contém essa palavra.
- `12 Gb/s` não vira capacidade de HD/SSD. Em kits, quantidade, capacidade dos módulos
  e total anunciado precisam concordar.
- Acessórios anunciados para uma CPU/GPU/RAM não são tratados como o componente.
- Mesmo modelo completo de CPU com ficha contraditória exige revisão e bloqueia
  cadastro novo. Código de linha, como A400, não comprova identidade de capacidade.
- `impedimentos` explicita identidade contraditória, busca incompleta ou candidatos
  sem margem suficiente. Continuam valendo >80, margem de dez pontos e ausência de conflitos.

### Medição local

Reprodução de 43 anúncios reais anteriormente armazenados contra a mesma cópia do
catálogo de 67.018 componentes, sem rede, enriquecimento externo ou gravação:

| Resultado | Antes | Depois |
|---|---:|---:|
| Confirmadas pelo algoritmo | 1 | 4 |
| Para avaliação | 28 | 13 |
| Associação rejeitada | 14 | 26 |
| Tempo observado | 13,82 s | 3,15 s |

Os tempos incluem carregamento do catálogo; dependem do ambiente e do cache de disco.
São classificações do algoritmo, não 43 associações rotuladas por revisão independente.
Portanto não medem precisão nem provam uma cobertura geral de 9,3% do catálogo.
Entre as contradições observadas, uma ficha intitulada i5-11400 informa três núcleos e
duas threads, enquanto o registro local tem seis e doze; esse caso fica para revisão.

Relatórios: `output/associacao-v7/antes.json`, `depois.json` e `testes.log`.
Testes novos verificam IDs após 2.000, duplicatas tardias, equivalência da decisão
indexada e exaustiva, ausência de consultas após expirar a sessão, kits, sufixos,
SO-DIMM, acessórios, unidades e contradições sem MPN. Nenhuma oferta foi criada nesta
avaliação. A aprovação das fichas importadas e as condições de uso de suas fontes
continuam separadas da associação.

### Revisão v8: equivalências e conjuntos

Taxas SATA explicitamente descritas como 1,5 / 3 / 6 Gbit/s são normalizadas
para SATA I / II / III. SATA 3 Gbit/s não equivale a SATA III. Uma geração e uma
taxa contraditórias não são convertidas em uma equivalência válida. Isso pode
revelar duplicatas locais antes ocultadas por grafias diferentes: nesses casos,
a decisão permanece ambígua, sem selecionar arbitrariamente um registro.

Anúncios de SSD/HD acompanhados explicitamente de caddy, adaptador, case ou
gabinete são barrados como conjuntos, mesmo com identificador da unidade correto.

Validação local desta revisão: 1.780 testes passaram, 18 foram ignorados e 20
subtestes passaram. Na reprodução das mesmas 43 respostas reais já salvas, o
controle anterior teve 4 confirmações, 13 ambiguidades e 26 rejeições; v8 teve
3 confirmações, 15 ambiguidades e 25 rejeições. A equivalência SATA revelou
ambiguidade adicional em um A400 e removeu um conflito em um SanDisk, sem evidência
suficiente para aprová-lo. Não houve aumento comprovado de cobertura nessa amostra.
As novas consultas/paginação foram testadas com respostas controladas, sem nova
varredura da API nem gravação de ofertas. É preciso uma nova simulação online
para medir seu ganho de recuperação de candidatos; os 43 casos não medem isso.
