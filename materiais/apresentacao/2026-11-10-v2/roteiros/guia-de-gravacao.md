# Guia de gravação e inserção dos vídeos

Grave o sistema real em 16:9, preferencialmente 1920×1080. Use uma conta de demonstração verificada, com espaço para salvar builds, e aumente o zoom até os rótulos ficarem legíveis. Desative notificações. Os resultados precisam ser os produzidos pelo sistema; corte esperas sem substituir a execução por telas montadas.

## Vídeo principal — slide 13

Arquivo: `13-demonstracao-1m50.mp4`. Duração total: **110 segundos**, já incluídos nos 6min30 do pitch. Preferência: MP4 H.264, sem música. Giovanni pode narrar durante a reprodução.

### 0:00–0:35 · RF04 · Montagem inteligente

- Começar nas últimas perguntas, com as anteriores já preenchidas.
- Confirmar objetivo, orçamento e peças já possuídas, se aplicável.
- Enviar e mostrar a configuração realmente retornada.
- Se cortar a espera, preservar o clique de envio e a resposta do mesmo fluxo.

### 0:35–1:00 · RF13 · Compatibilidade e consumo

- Preparar uma combinação cuja regra e dados técnicos sejam conhecidos.
- Executar a ação que dispara o diagnóstico e aproximar o aviso com seu motivo.
- Mostrar também o consumo estimado.
- Não apresentar dados insuficientes como confirmação. Evitar uma troca isolada sem explicar o diagnóstico.

### 1:00–1:25 · RF07 · Comparação

- Abrir duas builds reais e selecionar a comparação.
- Deixar os dois resultados visíveis e apontar uma diferença concreta.
- Depois de gravar, substituir no roteiro o trecho entre colchetes pelo resultado observado.
- Preço: usar a referência da última consulta, sem frete. Consumo: sempre estimativa.

### 1:25–1:50 · RF08 · Compartilhamento

- Na conta proprietária, tornar a configuração pública e copiar o link.
- Abrir o mesmo link em uma janela sem login.
- Mostrar a configuração e a ausência/bloqueio da edição da original.
- Se houver tempo, tornar privada e atualizar a janela sem login para mostrar o bloqueio.
- O foco é o controle de acesso, além da abertura da página.

## Trechos curtos — slides 3 a 7

Todos com 6–8 segundos, sem áudio. Reaproveite recortes do vídeo principal quando possível. Não acrescente esses segundos ao tempo da fala: a reprodução acontece enquanto Arthur apresenta o caso.

- Slide 3: `03-rf04-formulario.mp4` — últimas respostas e resultado da geração.
- Slide 4: `04-rf13-compatibilidade.mp4` — editor, regra e consumo estimado.
- Slide 5: `05-rf07-comparacao.mp4` — duas builds lado a lado.
- Slide 6: `06-rf08-compartilhamento.mp4` — build pública sem login e sem edição da original.
- Slide 7: `07-rf10-prontas.mp4` — aplicar um filtro e abrir uma configuração pronta.

GIF pode substituir esses cinco trechos. Prefira MP4 quando houver texto pequeno, para preservar a nitidez. Se o GIF repetir, avance o slide no tempo previsto.

## Evidências complementares

- Slide 12: `12-rede-api.mp4`, 8–12s. Mostrar uma ação de negócio, seu endereço em `api.boostio.com.br`, status e parte do JSON. Manter visível a origem do site. Não abrir a aba com cookies, Authorization ou outros dados de sessão. O health 200 já mostrado no slide é uma checagem real, mas não comprova todas as funções.
- Slide 16: `16-readme.mp4`, 6–8s. Percorrer o README até a seção dos requisitos. Fazer uma rolagem curta e parar para permitir leitura.
- Slides 14 e 15: vídeo opcional. A evidência textual já foi gerada em uma base temporária com o código real. Se gravar, executar `scripts/conferir-evidencia.py` em ambiente com as dependências do backend, nunca apontando para a base de produção.

## Google Apresentações

A apresentação editável está em:
https://docs.google.com/presentation/d/1v7uBdnImOjQyGoJw894cq6zYIyeRh4UGZs4FQOSNMck/edit

Anexe os GIFs nesta conversa com o nome da função ou o número do slide. Eles serão inseridos nos espaços preparados, preservando a proporção. Para a demonstração principal, mantenha também um MP4 de 1min50. As notas do apresentador já contêm as falas e os tempos.

Se inserir manualmente, remova somente o retângulo e os textos do espaço de mídia, use Inserir > Imagem para o GIF e confira a animação no modo de apresentação. Os vídeos podem ser selecionados do Google Drive pelo menu Inserir > Vídeo. Verifique a reprodução na conta e no computador usados no pitch.

## Alternativa no PowerPoint

1. Instalar as fontes da pasta `Fontes` antes de abrir o arquivo, se necessário.
2. No slide, selecionar e remover o retângulo e os textos do espaço “VÍDEO A INSERIR”. Preservar título, objetivo e rodapé.
3. Inserir o vídeo do arquivo local e posicioná-lo no mesmo espaço. Para GIF, inserir como imagem.
4. Manter proporção 16:9 e ajustar sem distorcer. As posições exatas estão em `manifesto.json` (canvas 1600×900).
5. Configurar início automático. Nos trechos curtos, sem áudio; no vídeo principal, sem repetição. Usar avanço manual dos slides durante o ensaio.
6. Salvar uma nova cópia com a mídia incorporada e testar do começo ao fim no computador da apresentação. Levar também o MP4 principal separado como alternativa.

O PDF é uma versão estática: não reproduz vídeos nem anima GIFs. Depois de inserir as gravações no PowerPoint, exportar outro PDF para atualizar suas imagens de capa. O PDF entregue agora exibe os espaços de mídia, sem simular os vídeos.

## Ensaio

- Arthur termina em 1:15; Gustavo Azevedo, em 2:35; Gustavo Horta, em 3:30.
- O vídeo de Giovanni termina em 5:20; Kayky encerra em 6:30.
- Os 30 segundos restantes são margem para transições. Não usá-los para acrescentar uma quinta demonstração.
- Se uma integração falhar, gravar uma execução válida antes do pitch; não apresentar uma tela de exemplo como resultado homologado.
