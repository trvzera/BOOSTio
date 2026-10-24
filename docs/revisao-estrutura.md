# Revisão de estrutura e arquivos locais

Revisão de 24/10/2026, sem apagar o banco ou reescrever o histórico Git.

## Código e dados necessários — manter versionados

- **`backend/`**: entrada Flask/WSGI, controllers, Models, Services, Repositories,
  comandos, migrations e dados de catálogo. Os caches dentro dela são ignorados.
  Migrations continuam necessárias para bancos existentes; não são lixo de build.
- **`frontend/pages`, `js`, `styles`**: páginas, comportamento e estilos de runtime.
- **`frontend/data`**: catálogo demonstrativo, medidas e vínculos de imagens.
  `medidas-fisicas.json` e `imagens-referencia.json` também são lidos pelo Python.
  O Docker da API passa a copiar esses dois arquivos explicitamente.
- **`frontend/imgs`, `fonts`, `svgs`, `lottie`, `video`**: recursos visuais do site.
  Fotos de produtos ocupam cerca de 25 MB, mas são usadas pela aplicação; não foram
  tratadas como cache descartável. As fontes locais são especialmente importantes
  para evitar páginas com tipografia diferente ou dependência de Google Fonts.
- **`backend/tests` e `frontend/tests`**: regressões automatizadas e fixtures;
  pertencem ao repositório. Relatórios e caches dos testes são ignorados.
- **`frontend/testes.html`**: laboratório intencional do produto, não um relatório
  gerado. Continua versionado e com a proteção de acesso existente.
- **`docs/`**: documentação técnica e diagrama da entrega. O arquivo pessoal
  `pendencias-produto.md` mantém a regra de ignore existente; não ignorar a pasta
  inteira. O diagrama final e sua fonte DOT foram preservados aqui antes de
  retirar `output` do rastreamento.
- **`deploy/`, Dockerfiles e `compose.yaml`**: configurações de publicação.
- **`requirements.txt`, `package.json`, `package-lock.json`**: dependências e
  versões reproduzíveis. O Lottie do site atualmente vem de CDN; não há import
  de `node_modules` pelo navegador.
- **`.vscode/settings.json`**: configuração compartilhada útil do Live Server.
  Não foi descartada junto com caches pessoais do editor.

## Gerados ou locais — fora do rastreamento

- **`node_modules/`**: dependências reinstaláveis. Antes desta revisão havia
  313 arquivos / aproximadamente 25,4 MB versionados nessa pasta.
- **`materiais/exportacoes/`** (antes `output/`): exportações de Instagram, ZIP, prévias e diagrama gerado.
  Aproximadamente 34,6 MB; originais permanecem no computador e no histórico Git.
  O diagrama final foi promovido para `docs/diagrama-classes.png`, com fonte DOT.
- **`.DS_Store`**: metadados do Finder. O arquivo que estava versionado foi
  retirado do índice, sem apagar a cópia local.
- **`database/` e `instance/`**: dados locais. SQLite, backups com extensão de
  banco e arquivos WAL/SHM/journal não devem ir ao PR. Nenhum banco foi excluído.
- **`.env` e `.env.*`**: segredos e configuração local, exceto exemplos
  explicitamente nomeados `.env.example` ou `.env.sample`, que devem ser sanitizados.
- **`venv`, `.venv`, caches Python/Node, coverage, logs e relatórios Playwright**:
  não são código-fonte; novas regras evitam que entrem por acidente.
- **`.cursor/`**: metadados locais do editor neste workspace, atualmente sem
  conteúdo necessário ao site.

Adicionar ao `.gitignore` não remove arquivos já rastreados. Por isso, as três
primeiras entradas desta seção foram retiradas apenas do índice com
`git rm --cached`, preservando o disco. São cerca de **60 MB a menos na árvore
versionada atual**, antes de considerar o diagrama final preservado em `docs`.
O histórico antigo continua com esses arquivos: não houve limpeza destrutiva de
commits nem redução equivalente de `.git`.

## Material histórico — preservado para decisão da equipe

- **`materiais/brand/`**: originais da marca. Não são dependência do site atual, mas são
  material autoral; podem ser arquivados fora da branch de produção depois.
- **`materiais/esbocos-site/`**: imagens do primeiro layout, candidatas a arquivo.
- **`materiais/termos-historicos/`**: PDF de uma versão histórica dos termos; não confundir com a
  página de termos usada no site.
- **`materiais/anotacoes/`**: notas pessoais pequenas; conteúdo não foi apagado.
- **`frontend/imgs/devs/`**: foto remanescente da antiga página da equipe. Não há
  referência direta atual, mas é imagem pessoal e foi preservada.
- **`backend/models/setup.py`**: Model legada ainda importada pelo pacote de
  Models. Removê-la sem revisar registro de tabelas e banco pode afetar dados.
- **`backend/controllers/peca_controller.py`**: blueprint legado fora do app
  principal, mas preservado por contratos/testes. Remoção exige decisão de API.
- **`backend/repositories/base.txt`**: placeholder vazio; candidato a remoção
  futura, sem impacto relevante no tamanho do repositório.

Essas pastas históricas foram excluídas do contexto Docker quando não fazem parte
do runtime. Não foram apagadas nem retiradas do Git automaticamente.

## Conferência

Os testes verificam que arquivos locais são ignorados e que fontes, testes,
catálogo, imagens e diagrama continuam elegíveis para versionamento. Também
verificam a declaração de cópia dos manifestos no Dockerfile da API. Não houve
build de imagem Docker nesta máquina, porque o executável Docker não está instalado.
