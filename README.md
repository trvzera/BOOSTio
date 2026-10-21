<div align="center">
  <img src="./frontend/imgs/logoBOOSTio.gif" alt="BOOSTio" width="360" height="90">
  <h1>BOOSTio</h1>
  <p>Planeje, monte e evolua seu computador em um só lugar.</p>
  <p><strong>Python · Flask · SQLAlchemy · JavaScript · HTML · CSS</strong></p>
  <p>
    <a href="#sobre">Sobre</a> ·
    <a href="#funcionalidades">Funcionalidades</a> ·
    <a href="#builds-prontas">Builds prontas</a> ·
    <a href="#desempenho-esperado">Desempenho esperado</a> ·
    <a href="#estado-do-projeto">Estado do projeto</a>
  </p>
</div>

## Sobre

A **BOOSTio** ajuda a escolher componentes de computador considerando objetivo,
orçamento e peças já possuídas. Reúne montagem manual, formulário inteligente,
compatibilidade, comparação de builds, preços e consultas de desempenho.

Este é meu projeto de software anual e final do curso no **Colégio Cotemig**,
em desenvolvimento ativo. A [página Sobre nós](frontend/pages/sobre.html)
apresenta a proposta da plataforma.

> **EN:** BOOSTio is a PC-building platform for planning configurations within a
> budget, reusing existing hardware and comparing components. It includes
> account-based builds, ready-made configurations, LLM-assisted assembly and
> expected gaming/rendering performance from public benchmark sources.

## Funcionalidades

Os **20 requisitos do produto**:

1. **Criar conta e fazer login** — cadastro, autenticação, logout e sessão.
2. **Cadastrar o setup atual** — definir ou remover uma build como seu computador atual.
3. **Pesquisar peças e compatibilidade** — catálogo por categoria e avisos durante a montagem.
4. **Montar por formulário** — geração assistida por LLM considerando uso, orçamento e peças próprias; sugestões com conflitos técnicos conhecidos são rejeitadas antes de salvar.
5. **Salvar configurações** — montagens persistidas na conta, inclusive incompletas.
6. **Excluir configurações** — exclusão respeitando o proprietário e a tranca da build.
7. **Comparar configurações salvas** — comparação de duas ou três builds; comparação de desempenho ainda parcial.
8. **Compartilhar por link** — visibilidade controlada e links de builds públicas; páginas internas exigem sessão.
9. **Buscar melhorias do setup** — sugestões para todas as categorias, com prévia e aplicação das trocas; ganhos de desempenho e ofertas atualizadas ainda precisam de consolidação.
10. **Ver configurações prontas** — dez modelos para públicos e necessidades diferentes, sem periféricos.
11. **Editar configurações** — alterar componentes, nome, descrição e orçamento da build.
12. **Consultar preços pelo site** — preços cadastrados, data de atualização quando disponível e acesso às lojas; monitoramento contínuo ainda em evolução.
13. **Ver compatibilidade e consumo** — diagnóstico Python diferencia conflito, dados não verificados e ausência de conflitos nas regras disponíveis; validação técnica completa ainda parcial.
14. **Incluir periféricos no orçamento** — etapa própria para inclusão e reaproveitamento, com tetos separados para o PC e os periféricos; sobras não são transferidas entre eles.
15. **Registrar budget no perfil** — valor e autorização aplicados ao formulário e à nova montagem manual, sem modificar builds existentes.
16. **Baixar JSON e CSV** — exportação da build para guardar localmente.
17. **Alterar visibilidade** — tornar a build pública ou privada.
18. **Duplicar builds** — cópia independente, respeitando o limite da conta.
19. **Definir nome e descrição** — identificação e edição dos detalhes da configuração.
20. **Importar JSON e CSV** — validação do arquivo e criação de uma configuração na conta.

**E-mail verificado e até três builds por conta.** As regras valem para criação manual, formulário,
importação, cópia de modelo e duplicação. Builds trancadas não podem ser editadas
nem excluídas antes de serem destrancadas.

Visitantes podem acessar a página inicial, termos, contato, sobre e páginas da
conta necessárias para cadastro, login e recuperação de senha. Formulário,
montagem, catálogo, perfil, builds prontas e laboratório exigem login.

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
anúncio, o link leva ao produto exato. **Pichau e Mercado Livre** são alternativas
de busca pelo modelo, sem garantia de oferta equivalente ou de preço confirmado.

Preço cadastrado não significa cotação em tempo real. Estoque, frete e condições
de compra devem ser conferidos na loja. A ficha da peça distingue dados da conta
de exemplos demonstrativos e informa a última atualização do preço quando cadastrada.

A BOOSTio **não vende, entrega ou processa pagamentos** dos produtos. Os links
direcionam a lojas de terceiros, responsáveis pela venda e pelo atendimento.

## Desempenho esperado

Ao selecionar **Testar build**, o usuário escolhe o tipo de consulta:

- **Jogos · FPSHQ:** jogo, resolução e qualidade gráfica, com FPS médio e 1% low
  quando disponíveis. Falhas e ausência de dados não geram FPS inventados.
- **Blender · Renderização:** dados públicos de CPU ou GPU, com mediana em
  amostras por minuto, versão do Blender, método de renderização e quantidade de resultados.

Essas consultas **não executam um benchmark no computador do usuário**. RAM,
VRAM, drivers, temperatura, energia, cena e programas em segundo plano podem
influenciar o desempenho real. Pontuações de CPU e GPU no Blender não são somadas
e não representam um tempo garantido de renderização.

Fontes: [FPSHQ](https://fpshq.com/pt/api/) e
[Blender Open Data](https://opendata.blender.org/about/).

## Estado do projeto

Autenticação, budget, catálogo e gerenciamento de builds estão implementados no
backend. Montagem manual, formulário, exportação, importação e modelos prontos
fazem parte da experiência atual.

Ainda estão em evolução a validação completa de compatibilidade física no
servidor, identificação de peças próprias, requisitos mínimos dos jogos,
monitoramento agendado de preços e comparação de desempenho nas mesmas condições.
A disponibilidade de cada consulta depende de sua fonte externa. A FPSHQ apresentou
timeouts nas consultas de FPS e jogos em 21/10/2026; o Blender respondeu e teve seu
resultado validado pelo serviço Python. Isso não comprova indisponibilidade global
da FPSHQ nem estabilidade permanente das fontes.

A geração pela LLM já revalida conflitos conhecidos no catálogo, incluindo socket,
DDR, slots, potência e medidas explícitas. Especificações ausentes continuam não
verificadas; a configuração não recebe garantia de compatibilidade completa.

O percentual para periféricos é um **limite máximo, não uma meta de gasto**.
Com R$ 5.000 e 20%, o PC e os acessórios de rede têm teto de R$ 4.000 e os
periféricos, de R$ 1.000. Se eles custarem menos, a sobra fica com o usuário;
não aumenta o teto do PC. O Python confere os subtotais pelos preços do catálogo
antes de salvar a sugestão.

**Projeto acadêmico em desenvolvimento — funcionalidades implementadas não
equivalem a homologação em produção.**
