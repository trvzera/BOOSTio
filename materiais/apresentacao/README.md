# Apresentações

Cada data reúne os arquivos de origem de uma apresentação.

## 2026-11-10 — Pitch BOOSTio / CMI

- `2026-11-10/roteiros/`: roteiro, notas dos slides, preparação da rubrica e ideias
  para o CMI. Esta é a fonte principal dos textos.
- `2026-11-10/assets/`: capturas e registro de sua origem. As telas usam dados
  demonstrativos, conforme `origem-telas.json`.
- `2026-11-10/scripts/`: auxiliares usados para capturar telas, montar os slides
  e preparar o pacote. Dependem das ferramentas do ambiente de geração.

O empacotador recebe `--exports /caminho/dos/slides-exportados`, com o PowerPoint
e as vinte imagens dos slides. Ele prepara uma nova versão na área de exportações,
sem substituir o pacote já existente.

Os pacotes de distribuição ficam em
`materiais/exportacoes/apresentacao/BOOSTio-Pitch-CMI/` e os intermediários de
10/11 em `materiais/exportacoes/apresentacao/2026-11-10/build/`. Ambos estão na
área de exportações locais, ignorada pelo Git.

O pacote já existente foi preservado. Os roteiros de origem devem ser revisados
antes de gerar uma nova versão; organizar os arquivos não atualiza o conteúdo
embutido no PowerPoint ou no PDF.

## Vídeo das funcionalidades — pendente

A demonstração deve mostrar o sistema em funcionamento: navegação, cliques e
resultados reais, em vez de apenas capturas estáticas. O roteiro reserva 1min50
para quatro funcionalidades não CRUD, dentro do limite de dois minutos.

Falta gravar, editar, incorporar o vídeo ao PowerPoint e incluir uma cópia MP4
offline no pacote final. Testar a reprodução no computador da apresentação;
PDFs e imagens exportadas dos slides não substituem o vídeo.

Acompanhar a preparação no
[checklist da rubrica](2026-11-10/roteiros/pendencias-da-rubrica.md#checklist-atualizado--09112026)
e as cenas no [roteiro do pitch](2026-11-10/roteiros/roteiro-do-pitch.md).
