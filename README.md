<div align="center">
  <img src="./frontend/imgs/logoBOOSTio.gif" alt="BOOSTio" width="100%">
  <h1>BOOSTio</h1>
  <p>Planeje, monte e evolua seu computador em um só lugar.</p>
  <p>
    <strong>Python · Flask · SQLAlchemy · JavaScript · HTML · CSS</strong><br>
    Projeto acadêmico · Colégio Cotemig · Em desenvolvimento
  </p>
  <p>
    <a href="#sobre">Sobre</a> ·
    <a href="#funcionalidades-implementadas">Funcionalidades</a> ·
    <a href="#diagrama-de-classes">Diagrama de classes</a> ·
    <a href="#builds-prontas">Builds prontas</a> ·
    <a href="#peças-e-preços">Peças e preços</a> ·
    <a href="#desempenho-esperado">Desempenho esperado</a> ·
    <a href="#estado-do-projeto">Estado do projeto</a>
  </p>
</div>

---

## Sobre

A **BOOSTio** ajuda a escolher componentes de computador considerando objetivo,
orçamento e peças já possuídas. Reúne montagem manual, formulário inteligente,
compatibilidade, comparação de builds, preços e consultas de desempenho.

Desenvolvida como projeto de software anual e final do curso no **Colégio Cotemig**,
a plataforma acompanha o planejamento do primeiro computador e as melhorias de
um setup existente. Conheça a proposta na [página Sobre nós](frontend/pages/sobre.html).

<details>
  <summary>English overview</summary>

BOOSTio is a PC-building platform for planning configurations within a budget,
reusing existing hardware and comparing components. It includes account-based
builds, ready-made configurations, LLM-assisted assembly and expected
gaming/rendering performance from public benchmark sources.

</details>

## Funcionalidades Implementadas

### Casos de uso com API e persistência

Os casos abaixo possuem interface, chamada HTTP, tratamento no backend, Service
e acesso às Models. Consultas leem o banco; alterações persistem os dados.
Os nomes identificam ações reais, não apenas telas ou rotas.

| Nº | Caso de uso | API Flask | Service responsável |
| --- | --- | --- | --- |
| 01 | Cadastrar conta | `POST /usuarios/` | `CriarUsuarioService` |
| 02 | Fazer login por e-mail e senha | `POST /auth/entrar` | `EntrarUsuarioService` |
| 03 | Atualizar os dados do perfil | `PUT /usuarios/{id}` | `AtualizarUsuarioService` |
| 04 | Excluir a conta por desativação lógica | `DELETE /usuarios/{id}` | `DeletarUsuarioService` |
| 05 | Salvar budget e autorização de uso | `PUT /usuarios/{id}/budget` | `AtualizarBudgetUsuarioService` |
| 06 | Solicitar código de verificação de e-mail | `POST /email/verificar/enviar/{id}` | `EnviarEmailService` |
| 07 | Confirmar o e-mail pelo código recebido | `POST /email/verificar/conferir/{id}` | `VerificarCodigoEmail` |
| 08 | Solicitar recuperação de senha | `POST /usuarios/esqueci-senha` | `EnviarEmailRecuperarService` |
| 09 | Redefinir senha com token válido | `POST /usuarios/redefinir-senha` | `RedefinirSenhaService` |
| 10 | Consultar o catálogo de peças e preços | `GET /build/catalogo` | `ListarCatalogoBuildService` |
| 11 | Criar uma build manual | `POST /build/manual` | `CriarBuildManualService` |
| 12 | Gerar uma build pelo formulário inteligente | `POST /build/` | `CriarBuildService` e `LLMService` |
| 13 | Listar as builds da conta | `GET /build/` | `ListarBuildService` |
| 14 | Abrir uma build salva | `GET /build/{id}` | `BuscarBuildService` |
| 15 | Atualizar uma build e seus componentes | `PUT /build/{id}` | `AtualizarBuildService` |
| 16 | Duplicar uma build | `POST /build/{id}/duplicar` | `DuplicarBuildService` |
| 17 | Excluir uma build | `DELETE /build/{id}` | `ExcluirBuildService` |
| 18 | Definir ou remover o setup atual | `POST /build/{id}/setup-atual` | `DefinirSetupAtualService` |
| 19 | Visualizar uma build pública por link | `GET /build/{id}/publica` | `BuscarBuildPublicaService` |
| 20 | Salvar uma cópia de build pública no perfil | `POST /build/{id}/copiar-publica` | `CopiarBuildPublicaService` |

Essa lista descreve a implementação, não uma garantia de funcionamento de serviços
externos: e-mail depende do SMTP configurado e geração depende da disponibilidade
e cota da LLM. As ressalvas de arquitetura estão na seção [Arquitetura](#arquitetura).

### Cobertura dos 20 requisitos do produto

Os **20 requisitos do produto**, com o status de cada funcionalidade e seu escopo atual.

**Resumo do produto: 19 implementadas no escopo descrito · 1 parcial.**

- ✅ **Implementado:** fluxo disponível no código do projeto.
- 🟡 **Parcial:** já possui partes implementadas, mas ainda há pontos a concluir.

Os status descrevem a implementação atual, não a homologação em produção.
As limitações de cada funcionalidade estão indicadas na última coluna.
Operações locais não são apresentadas como novos casos de uso de backend:
exportação JSON/CSV gera o download no navegador; comparação e prévia de melhorias
têm cálculos no JavaScript sobre builds carregadas da API. Aplicar melhorias,
importar e copiar modelos prontos utilizam os casos de criação/atualização acima.

| Nº | Requisito | Status | Escopo atual |
| --- | --- | --- | --- |
| 01 | Criar conta e fazer login | ✅ **Implementado** | Cadastro, autenticação, logout e sessão. |
| 02 | Cadastrar o setup atual | ✅ **Implementado** | Definir ou remover uma build como computador atual. |
| 03 | Pesquisar peças e compatibilidade | ✅ **Implementado** | Catálogo por categoria e diagnóstico durante a montagem, com as limitações do requisito 13. |
| 04 | Montar por formulário | ✅ **Implementado** | Geração por LLM com orçamento, ventilação obrigatória (contando fans inclusas) e uma revisão automática de saídas inválidas antes de salvar. |
| 05 | Salvar configurações | ✅ **Implementado** | Builds persistidas na conta, inclusive incompletas, com salvamento automático e avisos de falha. |
| 06 | Excluir configurações salvas | ✅ **Implementado** | Exclusão com verificação de proprietário e tranca. |
| 07 | Comparar configurações salvas | ✅ **Implementado** | Duas ou três builds: preços, componentes, consumo e renderização no Blender. FPS é uma ampliação pendente, não uma condição da comparação atual. |
| 08 | Compartilhar configurações por link | ✅ **Implementado** | Builds públicas podem ser vistas sem login, somente leitura. Testar exige sessão; salvar uma cópia privada exige também e-mail verificado e vaga na conta. |
| 09 | Buscar melhorias do setup | ✅ **Implementado** | RAM: acrescentar ou substituir pentes conforme a placa-mãe. SSD/HD: expandir quantidades mantendo os atuais, respeitando conexões/baias conhecidas, ou substituir sem regressões verificáveis. Orçamento obrigatório para aplicar; CPU/GPU e outras categorias dependem de métricas confiáveis. |
| 10 | Ver configurações prontas | ✅ **Implementado** | 16 modelos sem periféricos, referências revisadas no catálogo, filtro de budget e preço crescente. A cópia respeita e-mail verificado e limite da conta. |
| 11 | Editar configurações salvas | ✅ **Implementado** | Alteração de componentes, nome, descrição e orçamento; desfazer a última alteração de montagem enquanto o editor estiver aberto. |
| 12 | Consultar preços das peças pelo site | ✅ **Implementado** | Preços cadastrados, data quando disponível e links das lojas. Antes da compra, o catálogo é reconsultado e diferenças/indisponibilidade são mostradas. Não inclui frete nem garante o valor no checkout. |
| 13 | Ver compatibilidade e consumo de energia | 🟡 **Parcial** | Medidas disponíveis, formatos, baias, fans e radiador; substituição explícita das fans do water cooler e painel de informações. Completar fichas técnicas e interferências físicas. |
| 14 | Incluir periféricos no orçamento | ✅ **Implementado** | Inclusão e reaproveitamento com tetos separados para PC e periféricos. |
| 15 | Registrar budget no perfil | ✅ **Implementado** | Valor e autorização usados no formulário e em novas montagens manuais, sem alterar builds existentes. |
| 16 | Baixar builds em JSON e CSV | ✅ **Implementado** | Exportação para guardar a configuração localmente. |
| 17 | Alterar a visibilidade da build | ✅ **Implementado** | Alternância entre pública e privada. |
| 18 | Duplicar builds | ✅ **Implementado** | Cópia independente, respeitando o limite da conta. |
| 19 | Definir nome e descrição | ✅ **Implementado** | Identificação e edição dos detalhes da build. |
| 20 | Importar builds em JSON e CSV | ✅ **Implementado** | Validação do arquivo e criação de uma configuração na conta. |

### Regras da plataforma

- **Acesso:** início, termos, contato, sobre, cadastro, login e recuperação de senha
  são públicos. Links de builds públicas também abrem sem login, em uma tela somente
  leitura. Formulário, editor, catálogo, perfil, builds prontas e laboratório exigem login.
- **Criação:** e-mail verificado e limite de **três builds por conta**, incluindo
  montagem manual, formulário, importação, cópia de modelo e duplicação.
- **Tranca:** uma build trancada não pode ser editada nem excluída antes de ser destrancada.
- **Compartilhamento:** o visitante não altera a build original nem acessa o budget
  ou os dados do proprietário. Testar exige login; uma cópia é privada e independente.
  Tornar a original privada interrompe novas consultas e cópias pelo link público.

### Como o orçamento é respeitado

O percentual para periféricos é um **teto, não uma meta de gasto**. O restante
define o limite do PC, incluindo acessórios de rede.

> Com **R$ 5.000** e uma reserva de **20%**, o PC tem teto de **R$ 4.000** e os
> periféricos, de **R$ 1.000**. Se os periféricos custarem menos, a sobra fica com
> o usuário: não aumenta o teto do PC.

O Python confere os subtotais pelos preços e quantidades do catálogo antes de
salvar a sugestão. O **frete não está incluído**: é importante reservar parte do
orçamento para a entrega.

## Builds prontas

16 pontos de partida para **estudos, home office, programação, jogos,
criação de conteúdo, modelagem no Blender e máquinas virtuais**, com plataformas
AM4, AM5 e Intel e diferentes níveis de investimento.

Os modelos não incluem monitor, teclado, mouse, headset ou outros periféricos.
Os totais e o filtro de orçamento usam os preços disponíveis no catálogo da conta.
Modelos sem todas as cotações ou com peças indisponíveis não aparecem como opções
dentro de um budget informado. A disponibilidade pode mudar após a revisão.

A cópia é uma base editável: peças ausentes ou indisponíveis são sinalizadas no
editor; não são substituídas por produtos parecidos nem registradas como peças
que o usuário já possui. Totais sem todas as cotações são parciais.

## Peças e preços

A maioria dos preços cadastrados vem da **KaBuM**. Quando existe vínculo com o
anúncio, o link leva ao produto exato. A **Pichau** é uma alternativa de busca
pelo modelo, sem garantia de oferta equivalente ou de preço confirmado.

Preço cadastrado não significa cotação em tempo real. Estoque, frete e condições
de compra devem ser conferidos na loja. A ficha da peça distingue dados da conta
de exemplos demonstrativos e informa a última atualização do preço quando cadastrada.

As fotos da API têm prioridade. Quando faltam, há **750 vínculos locais de referência**
por part number, categoria, fabricante e modelo exatos, sem depender do ID numérico
do banco. Peças sem correspondência ou com foto quebrada mantêm uma alternativa neutra;
isso não significa cobertura de imagens para todo o catálogo.

> A BOOSTio **não vende, entrega ou processa pagamentos** dos produtos. Os links
> direcionam a lojas de terceiros, responsáveis pela venda e pelo atendimento.

## Desempenho esperado

Ao selecionar **Testar build**, o usuário escolhe o tipo de consulta:

### Jogos · FPSHQ

Escolha de jogo, resolução e qualidade gráfica, com **FPS médio** e **1% low**
quando disponíveis. Falhas e ausência de dados não geram FPS inventados.

A FPSHQ apresentou timeouts nas consultas de FPS e jogos em **21 e 22/10/2026**.
Isso não comprova indisponibilidade global; a consulta depende da resposta do provedor.

Nas builds salvas, **Verificar requisitos** usa o catálogo Python para comparar RAM,
VRAM dedicada e capacidade/tipo de armazenamento quando há um mínimo oficial
estruturado. Funciona independentemente da FPSHQ e interrompe a consulta na interface
quando identifica capacidade abaixo do mínimo. Dados próprios não identificados
permanecem desconhecidos. Não soma VRAM de placas ou discos separados, nem afirma
quanto espaço livre existe. Equivalência de CPU/GPU, sistema e demais recursos
continuam pendentes: capacidades suficientes não aprovam o computador completo.

### Blender · Renderização

Dados públicos de CPU ou GPU, com **mediana em amostras por minuto**, versão do
Blender, método de renderização e quantidade de resultados. O retorno foi validado
pelo serviço Python e revalidado com consultas reais em **23/10/2026**, sem garantia
de disponibilidade permanente.

A comparação de builds consulta esses dados ao clicar em **Comparar renderização**.
CPU e GPU são analisadas separadamente; só há classificação quando todas as builds
exibidas têm resultados da mesma versão do Blender e do mesmo método de renderização.
O reconhecimento do Blender é independente dos slugs da API de FPS: nomes
comerciais como EAGLE, DUAL e SHADOW não impedem identificar o chip explícito.
Sufixos e variantes são preservados; modelos não identificados ou sem resultados
públicos são informados por build, sem substituir a peça nem inventar pontuação.

### Limites da estimativa

Essas consultas **não executam um benchmark no computador do usuário**. RAM,
VRAM, drivers, temperatura, energia, cena e programas em segundo plano podem
influenciar o desempenho real. Pontuações de CPU e GPU no Blender não são somadas
e não representam um tempo garantido de renderização.

Fontes: [FPSHQ](https://fpshq.com/pt/api/) e
[Blender Open Data](https://opendata.blender.org/about/).

### Laboratório de testes

No laboratório (`testes.html`), é possível comparar uma consulta FPS pelo Python
com uma consulta direta pelo JavaScript, sem cache local neste último caminho.
O diagnóstico informa tempo, HTTP recebido e falhas de transporte/validação;
não troca automaticamente de caminho nem altera a montagem real.

Os **requisitos dos cinco jogos padrão** usam fontes oficiais revisadas em 21/10/2026
e consulta autenticada pelo Python. O modal usa a RAM da build salva e do catálogo;
o laboratório mantém uma prévia com capacidade informada manualmente.
O laboratório compara RAM informada; a build salva também verifica as capacidades
adicionais descritas acima. Não inventamos requisitos recomendados ausentes nem
ajustamos FPS por uma fórmula. Equivalência de CPU/GPU, sistema, espaço livre e
demais exigências continuam sem validação completa.

## Estado do projeto

Autenticação, budget, catálogo e gerenciamento de builds estão implementados no
backend. Montagem manual, formulário, exportação, importação e modelos prontos
fazem parte da experiência atual.

Ainda estão em evolução a validação completa de compatibilidade física no
servidor e a consolidação dos dados usados pelas sugestões e consultas:

- **Compatibilidade:** regras de encaixe e capacidade de fans implementadas no Python e no frontend; ampliar medidas confiáveis por modelo, conectores e interferências. Dados ausentes permanecem não verificados.
- **Peças próprias:** identificar modelos para avaliar suas especificações reais.
- **Jogos:** ampliar equivalências e recursos de CPU/GPU e requisitos além das capacidades já verificadas.
- **Preços:** consolidar o monitoramento agendado e a atualização do catálogo.
- **Desempenho:** concluir a comparação de FPS e tratar a instabilidade das fontes externas.

A geração pela LLM já revalida conflitos conhecidos no catálogo, incluindo socket,
DDR, slots, potência e medidas explícitas. Especificações ausentes continuam não
verificadas; a configuração não recebe garantia de compatibilidade completa.

O manifesto atual possui 37 fichas revisadas, incluindo gabinetes, GPUs, fontes,
air/water coolers, placas-mãe, processador, RAM, SSDs e fan. Há limites físicos,
slots, perfis JEDEC/XMP, dimensões por capacidade de SSD, conexões RGB/PWM e
exceções físicas declaradas pelo fabricante do cooler. As fichas só complementam
cadastros com identidade correspondente; não representam todo o catálogo.
Parte dos gabinetes tem capacidade de fans detalhada. Os cards mostram fans
inclusas e posições totais separadamente; fábrica, kits adicionais e water cooler
dividem essa capacidade. Medidas externas não substituem a ficha de fixação.
As fichas novas guardam fonte oficial/data da consulta e só são aplicadas às identidades
exatas documentadas; apelidos internos também exigem o anúncio revisado. Sem alterar
o banco ou inferir dados de outra revisão. Modelos/links com variantes divergentes
continuam pendentes de revisão. Isso não certifica BIOS, QVL ou todas as
interferências físicas.

Saídas inválidas da IA recebem **uma tentativa automática de correção**, com o erro
da validação e as regras originais. A nova resposta é validada por completo antes
de persistir. Isso cobre falhas como GPU obrigatória ausente, JSON inválido, IDs,
quantidades, orçamento e conflitos conhecidos; não garante solução quando o catálogo
ou o orçamento não permitem a montagem. Falhas de transporte e cotas recebem mensagens próprias.

Em 23/10/2026, um teste isolado pelo fluxo completo do formulário gerou, revisou,
validou e persistiu uma configuração de estudos em banco temporário. Isso não
comprova todos os cenários de uso nem garante respostas válidas de um provedor externo.

## Arquitetura

- [Controllers](backend/controllers/): entrada HTTP, sessão e respostas da API.
- [Services](backend/services/): casos de uso, validações e integrações externas.
- [Models](backend/models/): entidades SQLAlchemy e operações de persistência.
- [Repositories](backend/repositories/): diretório reservado; não há uma camada
  implementada para duplicar CRUD das Models.
- [Frontend](frontend/): páginas HTML/CSS e módulos JavaScript que consomem a API.

**Adequação à atividade ainda pendente:** as controllers atuais são funções de
Blueprint, não classes. A política de fallback da IA e parte da solicitação de
recuperação de senha ainda são coordenadas nas controllers. Esses pontos precisam
ser ajustados para atender integralmente ao padrão exigido pela disciplina;
a organização em pastas, por si só, não significa conformidade completa.

## Diagrama de classes

O diagrama de classes do domínio está sendo finalizado para esta entrega.
O local previsto é `docs/diagrama-classes.png`; o arquivo e o link de visualização
ainda precisam ser incluídos antes da submissão. Ele deve refletir as Models
atuais, incluindo a diferença entre `Build` e `BuildSalva`, cujo estado é JSON.

## Validação da versão

Na revisão de **23/10/2026**, a suíte local aprovou **521 testes JavaScript** e
**583 testes Python**, além de **13 subtestes Python**. Os testes cobrem, entre
outros pontos, conta, permissões, budget, limite de builds, persistência,
compartilhamento, arquivos, compatibilidade e tratamento de falhas.

Os testes utilizam isolamento, bancos temporários e mocks quando necessário.
Não comprovam todas as combinações de hardware, a disponibilidade permanente de
SMTP/LLM/benchmarks ou o funcionamento do ambiente de produção. A demonstração
final deve conferir os fluxos reais com frontend e backend da versão entregue.

## Limites de requisições

O Flask-Limiter limita login, cadastro, recuperação de senha, verificação de e-mail
e geração de builds por IA por IP e, conforme a rota, por e-mail ou usuário.
Localmente usa armazenamento em memória. Em produção, configure
`RATELIMIT_STORAGE_URI` com uma URL `redis://` ou `rediss://` antes de iniciar o
backend; sem Redis configurado, a aplicação não inicia em modo `producao`.

Se houver um proxy reverso confiável, defina `TRUSTED_PROXY_HOPS` com o número
exato de proxies que enviam `X-Forwarded-For`. O padrão é `0`: a aplicação usa
o IP da conexão e ignora esse cabeçalho. Não habilite a opção para acesso direto
à aplicação, pois clientes poderiam falsificar o próprio IP.

---

<div align="center">
  <strong>Projeto acadêmico em desenvolvimento</strong><br>
  Funcionalidades implementadas não equivalem a homologação em produção.
</div>
