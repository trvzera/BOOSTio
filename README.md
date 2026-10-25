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

As **20 funcionalidades obrigatórias do projeto**, na ordem dos requisitos
definidos para a entrega e a apresentação em vídeo, com o status e o escopo atual
de cada uma.

**Resumo do produto: 20 funcionalidades obrigatórias implementadas no escopo descrito.**

- ✅ **Implementado:** fluxo disponível no código do projeto.

Os status descrevem a implementação atual, não a homologação em produção.
As limitações de cada funcionalidade estão indicadas na última coluna. E-mail
depende do SMTP configurado; a geração inteligente depende da disponibilidade e
da cota da LLM.
Operações locais não são apresentadas como novos casos de uso de backend:
exportação JSON/CSV gera o download no navegador; comparação e prévia de melhorias
têm cálculos no JavaScript sobre builds carregadas da API. Aplicar melhorias,
importar e copiar modelos prontos utilizam os fluxos de criação ou atualização
de builds no backend para persistir a configuração na conta.

| Nº | Requisito | Status | Escopo atual |
| --- | --- | --- | --- |
| 01 | O sistema deve permitir ao usuário criar sua conta e fazer login | ✅ **Implementado** | Cadastro, autenticação, logout e sessão. Código de e-mail enviado ao iniciar a verificação e conferido ao completar seis dígitos; vínculo Google explícito no perfil, com confirmação de identidade. |
| 02 | O sistema deve permitir ao usuário cadastrar seu setup atual | ✅ **Implementado** | Definir ou remover uma build como computador atual. |
| 03 | O sistema deve permitir ao usuário pesquisar compatibilidade e peças | ✅ **Implementado** | Catálogo por categoria e diagnóstico durante a montagem, com as limitações do requisito 13. |
| 04 | O sistema deve permitir ao usuário montar seu setup atual através de formulário | ✅ **Implementado** | Geração por LLM com orçamento, peças próprias identificadas pelo catálogo, preferências opcionais de gabinete/cor, ventilação obrigatória (contando fans inclusas) e uma revisão automática de saídas inválidas antes de salvar. |
| 05 | O sistema deve permitir ao usuário salvar configurações de computadores feitas | ✅ **Implementado** | Builds persistidas na conta, inclusive incompletas, com salvamento automático e avisos de falha. |
| 06 | O sistema deve permitir ao usuário excluir configurações salvas no perfil | ✅ **Implementado** | Exclusão com verificação de proprietário e tranca. |
| 07 | O sistema deve permitir ao usuário comparar configurações salvas | ✅ **Implementado** | Duas ou três builds: preços, componentes, consumo e renderização no Blender. FPS é uma ampliação pendente, não uma condição da comparação atual. |
| 08 | O sistema deve permitir ao usuário compartilhar suas configurações por link | ✅ **Implementado** | Builds públicas podem ser vistas sem login, somente leitura. Testar exige sessão; salvar uma cópia privada exige também e-mail verificado e vaga na conta. |
| 09 | O sistema deve permitir ao usuário buscar melhorias do seu setup | ✅ **Implementado** | RAM: acrescentar ou substituir pentes conforme a placa-mãe. SSD/HD: expandir quantidades mantendo os atuais, respeitando conexões/baias conhecidas, ou substituir sem regressões verificáveis. Orçamento obrigatório para aplicar; CPU/GPU e outras categorias dependem de métricas confiáveis. |
| 10 | O sistema deve permitir ao usuário ver configurações prontas | ✅ **Implementado** | 16 modelos sem periféricos, referências revisadas no catálogo, filtro de budget e preço crescente. A cópia respeita e-mail verificado e limite da conta. |
| 11 | O sistema deve permitir ao usuário editar e modificar configurações salvas | ✅ **Implementado** | Alteração de componentes, nome, descrição e orçamento; desfazer a última alteração de montagem enquanto o editor estiver aberto. |
| 12 | O sistema deve permitir ao usuário verificar o preço da peça direto pelo site, sem precisar consultar em diversas abas | ✅ **Implementado** | Preços cadastrados, data quando disponível e links das lojas. Antes da compra, o catálogo é reconsultado e diferenças/indisponibilidade são mostradas. Não inclui frete nem garante o valor no checkout. |
| 13 | O sistema deve permitir ao usuário ver todas as informações de compatibilidade e consumo de energia do setup que está montando | ✅ **Implementado** | Diagnóstico da build, consumo estimado e fichas técnicas com socket, memória, slots, conexões, medidas, fans e radiador conforme os dados cadastrados. A página da peça organiza especificações e fontes por assunto. Dados ausentes são sinalizados, não aprovados por suposição; ampliar a cobertura de modelos permanece uma melhoria de catálogo. |
| 14 | O sistema deve permitir ao usuário adicionar ao setup periféricos, que muitas vezes não pensado anteriormente, acaba estourando o orçamento | ✅ **Implementado** | Inclusão e reaproveitamento com tetos separados para PC e periféricos. |
| 15 | O sistema deve permitir ao usuário registrar em seu perfil o seu budget, assim fica registrado o seu dinheiro disponível para comprar e futuras melhorias | ✅ **Implementado** | Valor e autorização usados no formulário e em novas montagens manuais, sem alterar builds existentes. |
| 16 | O sistema deve permitir ao usuário baixar a build em JSON e CSV para ter o arquivo local | ✅ **Implementado** | Exportação para guardar a configuração localmente. |
| 17 | O sistema deve permitir ao usuário alterar a visibilidade da build | ✅ **Implementado** | Alternância entre pública e privada. |
| 18 | O sistema deve permitir ao usuário duplicar a sua build | ✅ **Implementado** | Cópia independente, respeitando o limite da conta. |
| 19 | O sistema deve permitir ao usuário definir um nome e descrição para a build | ✅ **Implementado** | Identificação e edição dos detalhes da build. |
| 20 | O sistema deve permitir ao usuário importar builds por meio de arquivos CSV ou JSON | ✅ **Implementado** | Validação do arquivo e criação de uma configuração na conta. |

### Regras da plataforma

- **Acesso:** início, termos, contato, sobre, cadastro, login e recuperação de senha
  são públicos. Links de builds públicas também abrem sem login, em uma tela somente
  leitura. Formulário, editor, catálogo, perfil, builds prontas e laboratório exigem login.
- **Criação:** e-mail verificado e limite de **três builds por conta**, incluindo
  montagem manual, formulário, importação, cópia de modelo e duplicação.
- **Tranca:** uma build trancada não pode ser editada nem excluída antes de ser destrancada.
- **Compartilhamento:** o visitante não altera a build original nem acessa o budget
  ou os dados privados do proprietário. A autoria mostra somente o nome de exibição,
  sem e-mail ou ID da conta; contas desativadas aparecem como “Conta desativada”.
  Testar exige login; uma cópia é privada e independente.
  Tornar a original privada interrompe novas consultas e cópias pelo link público.
- **Desativação da conta:** bloqueia o acesso, encerra sessões e libera o e-mail
  para novo cadastro, preservando registros. A recuperação será assistida pela
  equipe; o procedimento de identificação e restauração ainda precisa ser definido.

### Como o orçamento é respeitado

O percentual para periféricos é um **teto, não uma meta de gasto**. O restante
define o limite do PC, incluindo acessórios de rede.

> Com **R$ 5.000** e uma reserva de **20%**, o PC tem teto de **R$ 4.000** e os
> periféricos, de **R$ 1.000**. Se os periféricos custarem menos, a sobra fica com
> o usuário: não aumenta o teto do PC.

O Python confere os subtotais pelos preços e quantidades do catálogo antes de
salvar a sugestão. O **frete não está incluído**: é importante reservar parte do
orçamento para a entrega.

O formulário separa **tamanho do gabinete**, **estilo** e **cor**, com imagens de
exemplo sem preços ou ofertas e opções de “sem preferência”. Os tamanhos são
Mini, Mid e Full Tower; os estilos são sem vidro, vidro lateral, aquário
(frente/lateral) e panorâmico com três faces de vidro (frente/lateral/teto).
Ao escolher o tamanho, um exemplo mostra medidas externas, placas-mãe,
ventoinhas e radiador suportados. Esses dados são do modelo de referência,
não um padrão de todos os gabinetes daquele tamanho. São preferências flexíveis:
não autorizam exceder o orçamento nem ignorar medidas, ventilação ou estoque.
Na geração inteligente, a preferência de cor se aplica a **todas as peças e
periféricos novos**, incluindo gabinete, ventoinhas e resfriadores. A amostra de
produtos e os conjuntos de periféricos preservam opções da cor desejada sem
eliminar alternativas econômicas e padrões técnicos. O complemento automático
de fans também considera a cor, depois de verificar encaixe e orçamento.
Cor cadastrada tem prioridade; nomes com indicação de cor são referências
comerciais, não confirmação técnica da versão. RGB, switch, fotos e URLs não
comprovam a cor da carcaça. Peças próprias são preservadas; ausência da cor
preferida não impede usar uma alternativa adequada, sem exceder os tetos.
Características ausentes não são inventadas. O editor também mostra a
capacidade total de SSDs/HDs em GB/TB; quando faltam dados, identifica o subtotal
como parcial.

O uso escolhido no formulário explica **quais peças terão prioridade**. As páginas
do catálogo e da peça também apresentam uma descrição simples da função de cada
componente, mantendo as informações técnicas para quem quiser conferir os detalhes.

Avisos distinguem falta de conexão, demora e erro respondido pelo servidor.
Se a resposta de uma criação ou alteração se perder, orientamos conferir o
resultado antes de repetir. Falhar ao verificar a sessão não significa sair da
conta: é possível tentar novamente, mantendo o conteúdo privado bloqueado até a confirmação.

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
Na consulta pública de **24/10/2026**, respondeu **HTTP 302** para uma página externa
de hospedagem inativa, em vez do JSON da API. O Python não segue esse destino:
informa indisponibilidade e aplica uma pausa, preservando apenas cache previamente
validado com aviso de desatualização. É uma observação deste ambiente e momento,
não uma garantia sobre o estado permanente do provedor.
Busca, FPS e contrato OpenAPI apresentaram esse mesmo retorno na nova checagem.
HTML com HTTP 200 também é tratado como resposta inválida, nunca como FPS.
O teste direto no Chrome, sem cache da aplicação, também falhou em 24/10:
o navegador registrou bloqueio por ausência do cabeçalho de CORS. O endereço
consultado é o mesmo do primeiro protótipo. Isso não comprova a causa interna
da indisponibilidade nem descarta diferenças entre redes, mas a falha atual não
se limita à integração Python: nesta consulta, o serviço não entregou JSON.

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
pelo serviço Python e revalidado com consultas reais em **23 e 24/10/2026**. A última
consulta de CPU respondeu HTTP 200, sem garantia de disponibilidade permanente.

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
O diagnóstico informa tempo, HTTP recebido e falhas de transporte/validação.
Quando disponíveis, distingue o HTTP da BOOSTio do status e formato recebidos
da FPSHQ e informa se a tentativa apenas encontrou a pausa após uma falha anterior;
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
- **Peças próprias:** ampliar a identificação. O formulário já sugere modelos por categoria e reconhece correspondências exatas e únicas; nomes desconhecidos ou ambíguos continuam a confirmar, sem substituir variantes por aproximação.
- **Jogos:** ampliar equivalências e recursos de CPU/GPU e requisitos além das capacidades já verificadas.
- **Preços:** consolidar o monitoramento agendado e a atualização do catálogo.
- **Desempenho:** concluir a comparação de FPS e tratar a instabilidade das fontes externas.

A geração pela LLM já revalida conflitos conhecidos no catálogo, incluindo socket,
DDR, slots, potência e medidas explícitas. Especificações ausentes continuam não
verificadas; a configuração não recebe garantia de compatibilidade completa.

O manifesto atual possui 76 fichas técnicas, incluindo gabinetes, GPUs, fontes,
air/water coolers, placas-mãe, processador, RAM, SSDs, fans e periféricos. Há limites físicos,
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

A revisão mais recente amplia slots, limites de RAM e conexões M.2/SATA em
29 cadastros de placas-mãe. Também padroniza a leitura dos sockets no Python e
no JavaScript, preservando diferenças como AM3/AM3+ e LGA2011/LGA2011-3.
Coolers com versões ou kits de fixação diferentes continuam a confirmar;
não recebem aprovação automática. O detalhamento e as lacunas de pesquisa
estão em [Catálogo e especificações revisadas](docs/catalogo-e-especificacoes.md).

A base de cadastro inclui **1.542 produtos**, com sete novos modelos de fans,
periféricos e gabinete identificados por part number. Isso não significa que todos
tenham preço, estoque ou ficha completa confirmados. A auditoria aponta campos
técnicos ausentes por categoria; novas peças só entram nas sugestões após cotação
válida e disponibilidade. Veja as [fontes e os limites da revisão do catálogo](docs/catalogo-e-especificacoes.md).

Saídas inválidas da IA recebem **uma tentativa automática de correção**, com o erro,
os subtotais calculados pelo servidor e as regras originais. A nova resposta é validada por completo antes
de persistir. Isso cobre falhas como GPU obrigatória ausente, JSON inválido, IDs,
quantidades, orçamento e conflitos conhecidos; não garante solução quando o catálogo
ou o orçamento não permitem a montagem. Falhas de transporte e cotas recebem mensagens próprias.

O planejamento fornece conjuntos de periféricos que cabem na reserva e preserva
opções de socket, DDR, recursos dos periféricos e faixas de preço no catálogo enviado
à IA. O prompt diferencia o conjunto mínimo viável de uma recomendação de qualidade
e considera referências visuais sem torná-las obrigatórias. Fans omitidas
podem ser completadas pelo Python somente quando encaixe e orçamento são conhecidos.
Pedidos exigentes com investimento alto subutilizado podem aproveitar a revisão
já prevista, sem exigir gasto mínimo ou novas tentativas ilimitadas. Detalhes e
resultados dos testes estão na [revisão da geração](docs/geracao-build.md).
Esses ajustes recentes foram validados com respostas controladas; novas chamadas
reais à LLM e o vínculo com o Google ainda precisam de homologação online.

Monitores **novos da geração inteligente** exigem painel confirmado IPS/VA,
incluindo Fast IPS e Fast VA. Para jogos, o planejamento destaca Hz e alternativas
de teclado mecânico com switch documentado quando couberem no conjunto. Para
edição/trabalho, destaca resolução e polegadas. Recursos ausentes não viram
garantia de precisão de cor ou qualidade. Itens próprios são preservados e o
catálogo manual não perde produtos. A integração AliExpress depende de acesso
aprovado e ainda não está ativa; veja o [escopo e as dependências](docs/integracoes-perifericos.md).

Em 23/10/2026, um teste isolado pelo fluxo completo do formulário gerou, revisou,
validou e persistiu uma configuração de estudos em banco temporário. Isso não
comprova todos os cenários de uso nem garante respostas válidas de um provedor externo.

## Arquitetura

- [Controllers](backend/controllers/): classes por recurso, responsáveis pela
  entrada HTTP, sessão, chamada aos Services e respostas da API.
- [Services](backend/services/): casos de uso, validações e integrações externas.
- [Models](backend/models/): entidades SQLAlchemy e operações de persistência.
- [Repositories](backend/repositories/): acesso especial ao banco na sonda de
  saúde e na migração de links. O CRUD convencional continua nas Models.
- [Frontend](frontend/): páginas HTML/CSS e módulos JavaScript que consomem a API.

As controllers utilizam métodos estáticos registrados nos Blueprints existentes,
sem compartilhar estado de requisição. A conversão preserva URLs, endpoints,
permissões, CSRF, limites de requisições e respostas. O fallback da IA é coordenado
por `GerarBuildService`; localizar a conta e solicitar recuperação ficam em
`SolicitarRecuperacaoSenhaService`. O envio de e-mail continua encapsulado em seu
Service específico, e o SQL especial fica nos Repositories.

## Diagrama de classes

O [diagrama de classes do domínio](docs/diagrama-classes.png) apresenta as Models,
suas heranças e relações, incluindo a diferença entre `Build` e `BuildSalva`,
cujo estado é JSON. A [fonte editável em DOT](docs/diagrama-classes.dot) também
está versionada. A imagem foi preservada dos arquivos de entrega já existentes;
não representa um diagrama de todos os Services e Controllers.

A [revisão de estrutura](docs/revisao-estrutura.md) explica o papel das pastas,
os recursos necessários ao site e os arquivos locais/gerados que não entram no PR.
Os originais da marca, esboços e anotações estão reunidos em [materiais](materiais/README.md).

## Validação da versão

Na revisão de **24/10/2026**, a suíte local aprovou **586 testes JavaScript** e
**781 testes Python**, além de **20 subtestes Python**. Os testes cobrem, entre
outros pontos, conta, permissões, budget, limite de builds, persistência,
compartilhamento, arquivos, compatibilidade e tratamento de falhas.
Há testes específicos para as sete classes de Controller e para preservar o
contrato das 35 rotas declaradas, incluindo o blueprint legado de peças, que
continua fora do registro do aplicativo principal. O catálogo ativo permanece
em `/build/catalogo`.

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
