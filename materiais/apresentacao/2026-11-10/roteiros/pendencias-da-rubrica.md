# Preparação técnica para a apresentação

Revisão de código e preparação de slides em 08/11/2026. Este documento orienta a equipe. Não representa alterações já aplicadas ao backend.

## 1. Repository nos casos de uso de negócio

O roteiro da avaliação exige Controller, Service, Repository e Model nos fluxos de entrada e recuperação.

**Observado:** BuscarBuildService chama `BuildSalva.buscar()` e CriarBuildManualService chama `BuildSalva.validar_estado()` e `BuildSalva.criar_limitada()`. O CRUD convencional está nas Models. Existem Repositories para saúde, migração de links e armazenamento de tokens. Ter essas classes não comprova a participação da camada nas duas rotinas de build.

**Adequação prioritária:** extrair o acesso a dados desses dois fluxos para um Repository, manter as regras no Service e as entidades nas Models, preservar sessão, transações, verificação de proprietário, limite e e-mail verificado. O nome de uma classe futura deve ser decidido na implementação. Os slides não afirmam que ela já existe.

**Após adequar:** atualizar slides 9, 10, 11, 14 e 15 e suas falas. Incluir uma consulta de negócio com entradas e resultado conhecidos, em vez de depender apenas de `SELECT 1`.

Fontes: `backend/services/build_service/buscar_build_service.py`, `criar_build_manual_service.py`, `backend/models/build_salva.py`, `backend/repositories/saude_repository.py` e seção Arquitetura do README.

## 2. Demonstração real em até dois minutos

O roteiro propõe geração, diagnóstico de compatibilidade, comparação e melhorias. São quatro resultados funcionais além de operações isoladas de cadastro, consulta ou alteração. A gravação deve mostrar a ação e o resultado em cada caso.

As capturas presentes nos slides usam a interface real com respostas simuladas da API e catálogo demonstrativo. Não houve gravação de execução real da LLM, de persistência ou de demonstração de produção nesta tarefa.

**Preparar:** vídeo de até 1min50, login e e-mail verificado, duas builds, vaga para uma terceira, uma incompatibilidade conhecida e uma expansão de RAM válida. Conferir a resposta do backend e o resultado persistido. Evitar FPS, atualmente desativado na interface.

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
