# Laboratório de FPS local · BOOSTio

Branch: `experimento/fps-local`. Experimento separado do frontend, Flask, banco de
usuários e integrações FPSHQ/Blender. Não há chamadas de rede nem novas dependências.
O botão de jogos do site continua em desenvolvimento.

A investigação de **FPSHQ e HowManyFPS**, os retornos verificados e a preparação
para receber referências externas estão em [fontes.md](fontes.md). O normalizador
é offline e mantém essas referências separadas das medições usadas na calibração.

## Estado inicial

Ainda não temos medições. A base começa vazia e o modelo **não está calibrado**.
O código desta fase valida os dados e consulta referências medidas de uma
configuração exata. Não prevê FPS de hardware diferente e não usa pontuações
genéricas de CPU/GPU, requisitos mínimos ou respostas de LLM como benchmark.

Jogos iniciais: Valorant, Counter-Strike 2, Fortnite, Cyberpunk 2077 e
Red Dead Redemption 2. A primeira fase considera resolução nativa, sem ray tracing,
upscaling ou geração de quadros. Presets customizados precisam de um cenário que
documente os ajustes; não equivalem automaticamente a Alta/Ultra.

## Executar localmente

Na raiz do projeto, com Python 3.12 ou superior:

```bash
python3 experimentos/fps-local/laboratorio.py validar
python3 experimentos/fps-local/laboratorio.py consultar --consulta experimentos/fps-local/dados/consulta-exemplo.json
python3 -m unittest discover -s experimentos/fps-local -p 'test_*.py' -v
```

A consulta de exemplo contém apenas um **pedido**, não resultados. Com a base
vazia, a resposta será `dados-insuficientes`, com FPS nulo. Preencha versão e
cenário conforme a medição real antes de comparar resultados.

## Formato das medições

`dados/medicoes.json` tem `versao: 1` e uma lista `medicoes`. Cada registro contém:

- `id`: identificador único da captura.
- `configuracao`: os mesmos campos de `consulta-exemplo.json`. CPU e GPU devem
  identificar modelos/variantes exatos; capacidade, quantidade de pentes e taxa
  de transferência da RAM também fazem parte da correspondência.
- `fps_medio` e `duracao_s`: valores positivos da mesma captura.
- `fps_1_low`: valor medido ou `null`; quando presente, exige `metodo_1_low`.
- `fonte`: `tipo` (`propria` ou `autorizada`), `referencia` para a captura/origem,
  `permissao` com as condições de uso, `uso_confirmado: true`, `coletado_em`
  (`AAAA-MM-DD`), `sistema` e `driver_gpu`.

O preenchimento de permissão é um registro da revisão manual, não uma verificação
automática de licença. Referências não são acessadas pelo programa. Não importar
medições de sites ou vídeos sem verificar as condições de reutilização.

Configurações diferentes não são combinadas. Execuções correspondentes retornam
a mediana dos FPS médios e a faixa observada entre execuções. Essa faixa não é um
intervalo de confiança nem garantia de desempenho. O 1% low só é agregado quando
todas as execuções o informam com o mesmo método; nunca é deduzido do FPS médio.
Drivers e sistema ficam expostos na origem; a correspondência de configurações
não elimina a influência desses fatores nem confirma um protocolo homogêneo.

Os números em `test_laboratorio.py` são **sintéticos**, exclusivos dos testes de
software. Não entram na base de medições ou na calibração.

## Coleta e próximos passos

1. Definir cenas reproduzíveis, duração, aquecimento, ajustes e versões. Registrar
   sistema, drivers, clocks, limites de energia, temperatura e condições da RAM.
2. Reunir capturas próprias ou dados com reutilização autorizada. O
   [PresentMon](https://github.com/GameTechDev/PresentMon) captura tempos de quadros
   e exporta CSV no Windows; não é uma base pronta de previsões para qualquer PC.
3. Revisar as capturas e cadastrar repetições de cada configuração. Guardar arquivos
   brutos volumosos fora do Git; manter metadados e referências rastreáveis.
4. Separar dados de calibração dos de avaliação, sem colocar repetições da mesma
   captura em conjuntos diferentes. Medir erro por jogo, cenário, resolução e GPU.
5. Só então experimentar regressão/interpolação e limites de CPU/GPU. Comparar com
   uma referência simples, documentar erros e recusar previsões fora da cobertura.
6. Discutir a integração Python → JSON → interface após validar o experimento.
   Não ativar como substituto silencioso da FPSHQ nem alterar o site nesta etapa.

RAM, VRAM, patches, drivers, refrigeração e processos em segundo plano podem mudar
o resultado. Nenhuma pontuação isolada ou relação linear de potência garante FPS.
