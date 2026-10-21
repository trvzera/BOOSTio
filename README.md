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

Os **20 requisitos do produto**, com o escopo disponível e os pontos em evolução.

**Disponível** indica um fluxo implementado. **Parcial** indica que ainda há partes
do recurso a concluir. Nenhum dos estados substitui a homologação em produção.

| Nº | Requisito | Situação | Escopo atual |
| --- | --- | --- | --- |
| 01 | Criar conta e fazer login | Disponível | Cadastro, autenticação, logout e sessão. |
| 02 | Cadastrar o setup atual | Disponível | Definir ou remover uma build como computador atual. |
| 03 | Pesquisar peças e compatibilidade | Disponível | Catálogo por categoria e diagnóstico durante a montagem, com as limitações do requisito 13. |
| 04 | Montar por formulário | Disponível | Geração por LLM conforme uso, orçamento e peças próprias; conflitos técnicos conhecidos são rejeitados antes de salvar. |
| 05 | Salvar configurações | Disponível | Builds persistidas na conta, inclusive incompletas, com salvamento automático. |
| 06 | Excluir configurações salvas | Disponível | Exclusão com verificação de proprietário e tranca. |
| 07 | Comparar configurações salvas | Parcial | Comparação de duas ou três builds; comparação de desempenho ainda em evolução. |
| 08 | Compartilhar configurações por link | Disponível | Links de builds públicas e controle de visibilidade; páginas internas exigem sessão. |
| 09 | Buscar melhorias do setup | Parcial | Prévia e aplicação de trocas em todas as categorias; ganhos de desempenho e ofertas atualizadas a consolidar. |
| 10 | Ver configurações prontas | Disponível | Dez modelos para diferentes públicos e orçamentos, sem periféricos. |
| 11 | Editar configurações salvas | Disponível | Alteração de componentes, nome, descrição e orçamento. |
| 12 | Consultar preços das peças pelo site | Parcial | Preços cadastrados, data de atualização quando disponível e links das lojas; monitoramento contínuo em evolução. |
| 13 | Ver compatibilidade e consumo de energia | Parcial | Diagnóstico Python de conflitos e dados não verificados; validação técnica e física completa a concluir. |
| 14 | Incluir periféricos no orçamento | Disponível | Inclusão e reaproveitamento com tetos separados para PC e periféricos. |
| 15 | Registrar budget no perfil | Disponível | Valor e autorização usados no formulário e em novas montagens manuais, sem alterar builds existentes. |
| 16 | Baixar builds em JSON e CSV | Disponível | Exportação para guardar a configuração localmente. |
| 17 | Alterar a visibilidade da build | Disponível | Alternância entre pública e privada. |
| 18 | Duplicar builds | Disponível | Cópia independente, respeitando o limite da conta. |
| 19 | Definir nome e descrição | Disponível | Identificação e edição dos detalhes da build. |
| 20 | Importar builds em JSON e CSV | Disponível | Validação do arquivo e criação de uma configuração na conta. |

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

Dez pontos de partida para **estudos, home office, programação, jogos,
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

A FPSHQ apresentou timeouts nas consultas de FPS e jogos em **21/10/2026**.
Isso não comprova indisponibilidade global; a consulta depende da resposta do provedor.

### Blender · Renderização

Dados públicos de CPU ou GPU, com **mediana em amostras por minuto**, versão do
Blender, método de renderização e quantidade de resultados. O retorno foi validado
pelo serviço Python em **21/10/2026**, sem garantia de disponibilidade permanente.

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

O laboratório também possui uma **prévia de requisitos dos cinco jogos padrão**,
com fontes oficiais revisadas em 21/10/2026 e consulta autenticada pelo Python.
Compara somente a capacidade de RAM informada, sem aprovar o PC completo,
inventar requisitos recomendados ausentes ou ajustar FPS por uma fórmula.
Equivalência de CPU/GPU, VRAM, sistema, espaço livre e demais exigências ainda
precisam ser validados e vinculados aos componentes reais da build.

## Estado do projeto

Autenticação, budget, catálogo e gerenciamento de builds estão implementados no
backend. Montagem manual, formulário, exportação, importação e modelos prontos
fazem parte da experiência atual.

Ainda estão em evolução a validação completa de compatibilidade física no
servidor e a consolidação dos dados usados pelas sugestões e consultas:

- **Compatibilidade:** completar dimensões, posições, conectores e demais regras físicas.
- **Peças próprias:** identificar modelos para avaliar suas especificações reais.
- **Jogos:** vincular requisitos mínimos e recomendados ao hardware da build.
- **Preços:** consolidar o monitoramento agendado e a atualização do catálogo.
- **Desempenho:** comparar configurações nas mesmas condições e tratar a instabilidade das fontes externas.

A geração pela LLM já revalida conflitos conhecidos no catálogo, incluindo socket,
DDR, slots, potência e medidas explícitas. Especificações ausentes continuam não
verificadas; a configuração não recebe garantia de compatibilidade completa.

---

<div align="center">
  <strong>Projeto acadêmico em desenvolvimento</strong><br>
  Funcionalidades implementadas não equivalem a homologação em produção.
</div>
