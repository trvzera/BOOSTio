# Fontes externas para o laboratório

Revisão em **26/10/2026**. Há um caso pontual do calculador web registrado como
referência externa; ainda não há autorização de treinamento confirmada. A base
`dados/medicoes.json` continua vazia.

## FPSHQ

As duas consultas públicas abaixo retornaram **HTTP 302**, `Content-Type:
text/html` e `Location: https://premium52.timeweb.ru/noactive/?ref=fpshq.com`:

- `https://fpshq.com/api/public/v1/games?q=valorant&lang=pt`
- `https://fpshq.com/api/public/v1/fps?game=valorant&cpu=ryzen-5-5600&gpu=rtx-3060&res=1080p&preset=high&lang=pt`

Consulta limitada a uma tentativa por endereço, sem seguir redirecionamentos.
Não recebemos JSON ou FPS válido. Isso documenta este ambiente/momento, não a
causa operacional ou a disponibilidade em todas as redes.

O cliente já existente na BOOSTio conhece `fps`, `low1`, `source` e `basis`, com
identificação de jogo/CPU/GPU e ajustes retornados. Quando voltar, precisamos
verificar novamente esse contrato e as condições de armazenamento/reutilização.
`source: measured` é uma declaração do provedor; `source: model` identifica uma
saída modelada. Nenhuma delas confirma RAM, patch ou cenário desta build.

## HowManyFPS

A [página oficial da API](https://howmanyfps.com/developer-api) publica um exemplo
de POST com `cpu`, `gpu`, `game`, `resolution` e `upscaling`, e resposta com
`avgFps` e `min1Fps`. O exemplo não documenta autenticação, confirmação dos modelos
no retorno, preset, RAM, patch ou cena. Precisamos da coleção Postman e contrato
enviados com o acesso antes de implementar o cliente HTTP.

O projeto ainda aguarda resposta ao e-mail de acesso, conforme confirmado pelo
responsável em 26/10. Não houve chamada da Developer API, contratação, consumo de
plano ou coleta em lote. O teste pontual abaixo usou a interface pública.

### Caso de estudo · Valorant na interface web

O [calculador de Valorant](https://howmanyfps.com/games/valorant) funcionou no
Safari sem login. Foram selecionados Ryzen 5 5600, GeForce RTX 3060 **8 GB** e
16 GB de RAM, mantendo 1920×1080, High, mapa Lotus, modo Multiplayer e Apply Offset
desmarcado. A interface exibiu **351 FPS médios e 230 FPS de 1% low**. O indicador
de Offset mostrava ±15%, mas não foi aplicado e não comprova intervalo estatístico.

O resultado e a configuração visível foram registrados em `dados/referencias-web.json`.
Não houve execução de jogo no computador do usuário ou acesso a tempos de quadros.
Frequência/pentes de RAM, versão do jogo, driver e outros campos não exibidos
permanecem desconhecidos. Não reutilizar esse resultado para a RTX 3060 de 12 GB.

Esse registro testa o fluxo de dados do laboratório e permite comparar futuramente
um resultado próprio com a referência. A autorização para calibração/treinamento
continua pendente; o exemplo não forma uma base autorizada de benchmarks.

O destaque “10K Requests” não informa, sozinho, gratuidade, período de renovação
ou direito a exportar a base. A gratuidade das ferramentas públicas não comprova
uma licença gratuita da API para este uso.

Os [termos públicos, seção 6](https://howmanyfps.com/terms), restringem cópia e
extração automatizada sem autorização. No contato de acesso, confirmar:

- Se a licença da API permite armazenar resultados e por quanto tempo.
- Se permite usar os dados para calibrar e avaliar um estimador independente.
- Se os retornos são capturas brutas, agregados ou previsões de um modelo.
- Quais metadados vêm com o resultado: RAM, preset, versão, cena, ray tracing,
  upscaling e geração de quadros, além do método de 1% low.
- Cota, custo, atualização, atribuição e possibilidade de manter o projeto público.

## Preparação disponível

`referencias.py` normaliza **arquivos JSON locais** de consulta/resposta, sem
acessar APIs ou gravar resultados. FPSHQ segue o contrato conhecido pelo cliente
existente; HowManyFPS segue apenas o exemplo público, ainda não homologado com acesso.

```bash
python3 experimentos/fps-local/referencias.py --provedor fpshq --consulta caminho/consulta.json --resposta caminho/resposta.json
python3 experimentos/fps-local/referencias.py --provedor howmanyfps --consulta caminho/consulta.json --resposta caminho/resposta.json
python3 experimentos/fps-local/referencias.py --listar-web
```

Esses arquivos de consulta usam os nomes de campo do respectivo provedor, não os
do `dados/consulta-exemplo.json` do laboratório. Não colocar credenciais nos arquivos.

A saída é `referencia-externa`, com origem declarada, contexto desconhecido e
`pronta_para_calibracao: false`. Respostas HTML, erros e combinações divergentes
não viram FPS. Campos não publicados não recebem valores presumidos.

O normalizador não insere referências em `medicoes.json`. Resultados do modelo de
outro provedor podem ajudar na comparação entre sistemas, se autorizados; não
substituem uma avaliação independente com capturas reais.

Todos os valores dos testes são sintéticos. Nenhum dado deles deve ser usado como
resultado real da FPSHQ ou da HowManyFPS.
