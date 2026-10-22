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
    <a href="#funcionalidades">Funcionalidades</a> ·
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

## Funcionalidades

Os **20 requisitos do produto**, com o status de cada funcionalidade e seu escopo atual.

**Resumo: 16 implementadas · 4 parciais.**

- ✅ **Implementado:** fluxo disponível no código do projeto.
- 🟡 **Parcial:** já possui partes implementadas, mas ainda há pontos a concluir.

Os status descrevem a implementação atual, não a homologação em produção.
As limitações de cada funcionalidade estão indicadas na última coluna.

| Nº | Requisito | Status | Escopo atual |
| --- | --- | --- | --- |
| 01 | Criar conta e fazer login | ✅ **Implementado** | Cadastro, autenticação, logout e sessão. |
| 02 | Cadastrar o setup atual | ✅ **Implementado** | Definir ou remover uma build como computador atual. |
| 03 | Pesquisar peças e compatibilidade | ✅ **Implementado** | Catálogo por categoria e diagnóstico durante a montagem, com as limitações do requisito 13. |
| 04 | Montar por formulário | ✅ **Implementado** | Geração por LLM com orçamento, ventilação cadastrada e uma revisão automática de saídas inválidas antes de salvar. |
| 05 | Salvar configurações | ✅ **Implementado** | Builds persistidas na conta, inclusive incompletas, com salvamento automático. |
| 06 | Excluir configurações salvas | ✅ **Implementado** | Exclusão com verificação de proprietário e tranca. |
| 07 | Comparar configurações salvas | 🟡 **Parcial** | Preços, componentes, consumo e renderização no Blender de duas ou três builds; comparação de FPS ainda pendente. |
| 08 | Compartilhar configurações por link | ✅ **Implementado** | Links de builds públicas e controle de visibilidade; páginas internas exigem sessão. |
| 09 | Buscar melhorias do setup | 🟡 **Parcial** | Prévia e aplicação com bloqueio de regressões de RAM/SSD/HD. Trocas de CPU/GPU e demais categorias aguardam critérios comparáveis; sem dados, não são liberadas como melhorias. |
| 10 | Ver configurações prontas | ✅ **Implementado** | 16 modelos sem periféricos, ordenados do menor para o maior preço cadastrado. |
| 11 | Editar configurações salvas | ✅ **Implementado** | Alteração de componentes, nome, descrição e orçamento. |
| 12 | Consultar preços das peças pelo site | 🟡 **Parcial** | Preços cadastrados, data de atualização quando disponível e links das lojas; monitoramento contínuo em evolução. |
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
  são públicos. Formulário, montagem, catálogo, perfil, builds prontas e laboratório exigem login.
- **Criação:** e-mail verificado e limite de **três builds por conta**, incluindo
  montagem manual, formulário, importação, cópia de modelo e duplicação.
- **Tranca:** uma build trancada não pode ser editada nem excluída antes de ser destrancada.

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

> A BOOSTio **não vende, entrega ou processa pagamentos** dos produtos. Os links
> direcionam a lojas de terceiros, responsáveis pela venda e pelo atendimento.

## Desempenho esperado

Ao selecionar **Testar build**, o usuário escolhe o tipo de consulta:

### Jogos · FPSHQ

Escolha de jogo, resolução e qualidade gráfica, com **FPS médio** e **1% low**
quando disponíveis. Falhas e ausência de dados não geram FPS inventados.

A FPSHQ apresentou timeouts nas consultas de FPS e jogos em **21 e 22/10/2026**.
Isso não comprova indisponibilidade global; a consulta depende da resposta do provedor.

Nas builds salvas, **Verificar requisitos** consulta as fichas oficiais revisadas e
compara a capacidade de RAM da própria configuração, pelo Python, mesmo com a FPSHQ
indisponível. A consulta de FPS é interrompida na interface se a RAM confirmada fica
abaixo do mínimo. Memória própria sem identificação permanece não verificada.
CPU, GPU, VRAM, sistema e demais requisitos ainda precisam de validação; RAM suficiente
não aprova o computador completo e nenhum FPS é calculado por essa verificação.

### Blender · Renderização

Dados públicos de CPU ou GPU, com **mediana em amostras por minuto**, versão do
Blender, método de renderização e quantidade de resultados. O retorno foi validado
pelo serviço Python em **21/10/2026**, sem garantia de disponibilidade permanente.

A comparação de builds consulta esses dados ao clicar em **Comparar renderização**.
CPU e GPU são analisadas separadamente; só há classificação quando todas as builds
exibidas têm resultados da mesma versão do Blender e do mesmo método de renderização.

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
Comparam somente a capacidade de RAM, sem aprovar o PC completo,
inventar requisitos recomendados ausentes ou ajustar FPS por uma fórmula.
Equivalência de CPU/GPU, VRAM, sistema, espaço livre e demais exigências ainda
precisam ser validados e vinculados aos componentes reais da build.

## Estado do projeto

Autenticação, budget, catálogo e gerenciamento de builds estão implementados no
backend. Montagem manual, formulário, exportação, importação e modelos prontos
fazem parte da experiência atual.

Ainda estão em evolução a validação completa de compatibilidade física no
servidor e a consolidação dos dados usados pelas sugestões e consultas:

- **Compatibilidade:** regras de encaixe e capacidade de fans implementadas no Python e no frontend; ampliar medidas confiáveis por modelo, conectores e interferências. Dados ausentes permanecem não verificados.
- **Peças próprias:** identificar modelos para avaliar suas especificações reais.
- **Jogos:** vincular requisitos mínimos e recomendados ao hardware da build.
- **Preços:** consolidar o monitoramento agendado e a atualização do catálogo.
- **Desempenho:** concluir a comparação de FPS e tratar a instabilidade das fontes externas.

A geração pela LLM já revalida conflitos conhecidos no catálogo, incluindo socket,
DDR, slots, potência e medidas explícitas. Especificações ausentes continuam não
verificadas; a configuração não recebe garantia de compatibilidade completa.

Saídas inválidas da IA recebem **uma tentativa automática de correção**, com o erro
da validação e as regras originais. A nova resposta é validada por completo antes
de persistir. Isso cobre falhas como GPU obrigatória ausente, JSON inválido, IDs,
quantidades, orçamento e conflitos conhecidos; não garante solução quando o catálogo
ou o orçamento não permitem a montagem. Falhas de transporte e cotas recebem mensagens próprias.

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
