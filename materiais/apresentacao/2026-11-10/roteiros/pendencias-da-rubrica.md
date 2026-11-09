# Preparação técnica para a apresentação

Revisão de código e preparação de slides em 08/11/2026. Este documento orienta a equipe. Não representa alterações já aplicadas ao backend.

## Checklist atualizado — 09/11/2026

Esta revisão registra o que falta preparar e o que ainda exige adequação no código.
Não foi localizado vídeo em `materiais/`; gravações que a equipe mantenha em outro
local ainda precisam ser incorporadas e conferidas no pacote final.

- [ ] **Gravar as funcionalidades em funcionamento, com cliques e resultados reais,
  em vez de apresentar apenas prints.** Preparar um vídeo de 1min50, limitado a dois
  minutos, para o bloco de demonstração. Mostrar quatro funções não CRUD do README;
  a seleção atual do roteiro é RF04, RF13, RF07 e RF09. Confirmar no ensaio se esses
  quatro cenários estão prontos antes de gravar. Se a equipe preferir compartilhar
  uma build (RF08), revisar a seleção e as falas antes da edição.
- [ ] Editar esperas sem falsificar respostas ou resultados; incluir legendas
  curtas identificando cada funcionalidade. Preparar conta de demonstração e
  ocultar dados pessoais, códigos, tokens e configurações privadas.
- [ ] Incorporar o vídeo ao PowerPoint, manter uma cópia MP4 disponível offline
  junto da entrega e testar reprodução, áudio e legibilidade no computador usado
  na apresentação. A prévia em PDF e as imagens dos slides não reproduzem o vídeo.
- [ ] Adequar os fluxos de entrada e recuperação de builds à camada Repository,
  preservando permissões, quota, transações e regras; revisar os dois fluxogramas,
  os slides e as falas depois da implementação. A consulta e a criação manual
  inspecionadas ainda chamam `BuildSalva` diretamente.
- [ ] Capturar uma requisição real frontend → API e evidências de CRUD com ORM
  e de uma consulta de negócio em Repository, com resultado conhecido. Ter telas,
  diretórios ou apenas `SELECT 1` não substitui essas evidências.
- [ ] Para reivindicar o bônus de termos, registrar no servidor a decisão do
  usuário, a versão do documento e a data, incluindo o primeiro acesso por Google.
  O cadastro inspecionado ainda envia somente nome, e-mail e senha.
- [ ] Atualizar e conferir o PowerPoint, suas notas e o pacote exportado após
  concluir os itens anteriores. Ensaiar os cinco integrantes com o vídeo final,
  mantendo a apresentação inteira em até sete minutos.

**Integrações:** a interface de FPS foi reativada no commit `8cad746`. Isso não
comprova disponibilidade contínua do provedor nem funcionamento da versão instalada
na VPS; homologar o ambiente escolhido para a banca antes de demonstrar integrações.
O vídeo planejado não depende de FPS ou Blender.

## 1. Repository nos casos de uso de negócio

O roteiro da avaliação exige Controller, Service, Repository e Model nos fluxos de entrada e recuperação.

**Observado:** BuscarBuildService chama `BuildSalva.buscar()` e CriarBuildManualService chama `BuildSalva.validar_estado()` e `BuildSalva.criar_limitada()`. O CRUD convencional está nas Models. Existem Repositories para saúde, migração de links e armazenamento de tokens. Ter essas classes não comprova a participação da camada nas duas rotinas de build.

**Adequação prioritária:** extrair o acesso a dados desses dois fluxos para um Repository, manter as regras no Service e as entidades nas Models, preservar sessão, transações, verificação de proprietário, limite e e-mail verificado. O nome de uma classe futura deve ser decidido na implementação. Os slides não afirmam que ela já existe.

**Após adequar:** atualizar slides 9, 10, 11, 14 e 15 e suas falas. Incluir uma consulta de negócio com entradas e resultado conhecidos, em vez de depender apenas de `SELECT 1`.

Fontes: `backend/services/build_service/buscar_build_service.py`, `criar_build_manual_service.py`, `backend/models/build_salva.py`, `backend/repositories/saude_repository.py` e seção Arquitetura do README.

## 2. Demonstração real em até dois minutos

O roteiro propõe geração, diagnóstico de compatibilidade, comparação e melhorias. São quatro resultados funcionais além de operações isoladas de cadastro, consulta ou alteração. A gravação deve mostrar a ação e o resultado em cada caso.

As capturas presentes nos slides usam a interface real com respostas simuladas da API e catálogo demonstrativo. Não houve gravação de execução real da LLM, de persistência ou de demonstração de produção nesta tarefa.

**Preparar:** vídeo de até 1min50, login e e-mail verificado, duas builds, vaga para uma terceira, uma regra de compatibilidade com dados conhecidos e uma expansão de RAM válida. Conferir a resposta do backend e o resultado persistido. Não depender de FPS para esta gravação; a disponibilidade do provedor exige homologação no ambiente da apresentação.

## 3. Frontend consumindo API

`frontend/js/config.js` define a base e os módulos `frontend/js/api/` usam `fetchComErro()`. A separação de código existe.

**Preparar a evidência:** capturar no Network uma requisição real à API e seu JSON. Mostrar os processos/origens locais ou o roteamento publicado. Separação frontend/API pode existir atrás de um mesmo domínio e proxy. Não usar somente uma imagem de diretórios como prova de consumo HTTP.

Checagem HTTP por HEAD em 08/11/2026:

- `https://boostio.com.br/`: 200, HTML.
- `https://boostio.com.br/health`: 404, HTML.
- `https://boostio.com.br/api/health`: 404, HTML.
- `https://boostio.com.br/auth/me`: 404, HTML.

Isso confirma resposta da página pública e não confirmou a API nessas rotas. Não determina se a API está hospedada em outro domínio ou rota. Conferir o endereço real de produção antes de reivindicar esse bônus.

## 4. ORM e SQL

`ModeloBase.salvar()` e `deletar()` usam a sessão SQLAlchemy. `BuildSalva` implementa persistência ORM, filtros e transações. `SaudeRepository` usa SQL explícito para `SELECT 1`.

**Preparar:** evidência de criar, ler, atualizar e excluir em banco temporário e uma consulta de negócio na camada Repository com resultado conferido. O `SELECT 1` é evidência de conectividade, não de consulta de negócio completa. Os trechos de código do deck são reais, mas não substituem a evidência de execução.

## 5. Bônus de consentimento

O cadastro tem checkbox de termos. A função `criarUsuario(nome, email, senha)` envia somente esses três campos à API, e a criação da conta não registra versão dos termos, decisão ou data de aceite nos arquivos inspecionados.

**Conclusão para o pitch:** não marcar consentimento persistido como bônus já concluído. A mera presença da checkbox não comprova o registro exigido. Se a equipe implementar o registro, conferir a decisão no banco e atualizar o material.

Fontes: `frontend/pages/signin.html`, `frontend/js/pages/signin.js`, `frontend/js/api/usuario/criarUsuario.js`, `backend/services/usuario_service/criar_usuario_service.py` e `backend/models/usuario.py`.

## 6. Coerência de documentação

O README descreve integrações implementadas. `frontend/pages/sobre.html` ainda informa que montagem automática e benchmarks aguardam integrações. Revisar essa mensagem para refletir o escopo real antes de mostrá-la à banca ou ao público.

O diagrama do slide 8 é um recorte das Models atuais. O diagrama versionado de montagem está como apoio, não como representação exaustiva de todas as entidades recentes de ofertas e integrações.

## Ordem sugerida de trabalho

1. Adequar os dois fluxos à camada Repository e conferir regressões.
2. Confirmar a API que será usada na banca e na feira.
3. Gravar a demo real e capturar as evidências de ORM, SQL e Network.
4. Confirmar bônus individualmente e atualizar as falas e diagramas.
5. Ensaiar o conjunto em 6min30 com os cinco integrantes.
