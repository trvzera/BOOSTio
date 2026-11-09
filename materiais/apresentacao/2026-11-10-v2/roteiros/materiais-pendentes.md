# Materiais que faltam para fechar a apresentação

1. **Vídeo principal de 1min50**, com execução real: RF04 (35s), RF13 (25s), RF07 (25s) e RF08 (25s). No compartilhamento, mostrar a mudança para público e a abertura sem login, somente para leitura.
2. **Cinco trechos de 6–8s**, um para cada caso dos slides 3–7. Os quatro primeiros podem ser recortes do vídeo principal; gravar também a tela de configurações prontas (RF10). Podem ser MP4 ou GIF.
3. **Trecho de Network de 8–12s**: ação no site, requisição à API, status e resposta JSON. Ocultar cookies, tokens e informações pessoais.
4. **Trecho do README de 6–8s**, mostrando os 20 requisitos e seus escopos. Não é necessário ler a lista na apresentação.

Os oito espaços correspondentes já estão preparados no PowerPoint. A lista de nomes dos arquivos está em `../midias/manifesto.json`, e o passo a passo em `guia-de-gravacao.md`. Ainda não há vídeos incorporados.

O CRUD e a consulta do Repository já têm evidência executada com as Models reais em SQLite temporário. Gravar essa execução é opcional; os slides 14 e 15 mostram o resultado textual real.

**Pendência técnica separada dos materiais:** a criação manual ainda grava por `BuildSalva.criar_limitada()`, sem Repository. O slide e as notas mostram o fluxo real; a adequação exigida pela rubrica continua pendente. A leitura de `HistoricoOferta.listar()` também é direta. Se o código mudar antes da apresentação, atualizar os fluxogramas.

**Bônus:** reivindicar IA funcional somente após conferir a execução real; para consentimento, falta evidência de decisão registrada no servidor. A checagem pública de hospedagem respondeu HTTP 200 em 09/11/2026, mas não substitui a demonstração das funções de negócio.
