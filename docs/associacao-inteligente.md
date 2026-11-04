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
