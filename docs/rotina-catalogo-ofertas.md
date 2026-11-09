# Rotina de aprovação do catálogo e busca de ofertas

Sequência para aprovar uma amostra de peças, buscar ofertas na Shopee e no Mercado
Livre, acompanhar a fila e analisar as pendências com IA.

Cada bloco contém **um comando**, para copiar e executar separadamente.
Os comandos foram conferidos no código; este documento não significa que a
rotina já foi executada no banco.

## 0. Organizar os terminais

Use o ambiente Python do projeto. Em cada terminal, partindo da raiz do
repositório, entre na pasta do backend:

```bash
cd backend
```

Depois disso, execute todos os comandos abaixo a partir de `backend/`.
O banco e as integrações das lojas precisam estar configurados.

- **Terminal 1:** aprovação da amostra e enfileiramento das ofertas.
- **Terminal 2:** worker contínuo; mantenha aberto enquanto ele processa a fila.
- **Terminal 3:** acompanhamento da fila e, depois da coleta, análise pela IA.
- Se a aplicação web estiver rodando, mantenha-a no próprio terminal.

Os comandos com `--aplicar` confirmam a gravação. O worker e os comandos de
reativação não usam essa opção: eles já executam ações reais.

## 1. Aprovar até 300 peças por categoria

### Simular

Confira o total de peças aprováveis, as recusas e os resultados por categoria:

```bash
python -m flask --app app catalogo-aprovar-lote --limite 300 --semente 1
```

### Gravar a aprovação

```bash
python -m flask --app app catalogo-aprovar-lote --limite 300 --semente 1 --aplicar
```

`--limite 300` é um máximo **por categoria**, não um total para o catálogo todo.
Somente peças em revisão que atendam às regras de identidade, ficha mínima e
ausência de duplicatas podem ser aprovadas; algumas categorias podem ter menos
de 300 elegíveis.

A semente repete o sorteio enquanto os dados e os estados das peças forem os
mesmos. Após gravar, as peças aprovadas saem do conjunto em revisão; repetir a
aprovação pode selecionar outras peças.

Aprovar não cria preço nem oferta. A peça só entra no catálogo do usuário depois
de ter uma oferta ativa com preço, conforme as regras de publicação.

## 2. Enfileirar a busca de ofertas nas duas lojas

O exemplo usa `amostra-2026-11-08` como identificação da rodada. Esse texto não
define uma data de agendamento: identifica as tarefas e evita duplicatas ao
repetir o mesmo pedido. Para iniciar uma nova rodada, escolha outro identificador
e use-o nos dois comandos.

### Shopee

```bash
python -m flask --app app marketplaces-enfileirar-ofertas --loja shopee --execucao amostra-2026-11-08 --gravar-ofertas --aplicar
```

### Mercado Livre

```bash
python -m flask --app app marketplaces-enfileirar-ofertas --loja mercado_livre --execucao amostra-2026-11-08 --gravar-ofertas --aplicar
```

- `--aplicar` grava as tarefas na fila.
- `--gravar-ofertas` define que essas tarefas devem persistir as ofertas
  encontradas. Sem essa opção, as tarefas simulam a importação.
- Sem `--categoria`, são consideradas todas as categorias. Entram peças
  aprovadas/publicáveis que tenham os requisitos técnicos mínimos.
- O enfileiramento também considera peças que já estavam aprovadas antes da
  amostra; ele não fica limitado às recém-aprovadas pelo passo 1.
- Enfileirar não coleta imediatamente: o worker executa as tarefas.

## 3. Rodar o worker

No **Terminal 2**, deixe este processo aberto:

```bash
python -m flask --app app marketplaces-worker
```

O worker alterna o processamento entre as lojas e respeita pausas e limites de
requisições. Ele continua aguardando quando não há tarefas elegíveis; não encerra
automaticamente ao esvaziar a fila. Para solicitar o encerramento, use **Ctrl+C**.

Esse worker processa a fila compartilhada, incluindo tarefas de rodadas anteriores.
Ele não fica restrito ao identificador usado no passo 2.

### Alternativa: executar um ciclo e encerrar

Use esta alternativa no lugar do worker contínuo quando quiser processar uma
tarefa elegível por loja e encerrar:

```bash
python -m flask --app app marketplaces-worker --uma-vez
```

## 4. Acompanhar a fila

No **Terminal 3**, rode novamente sempre que quiser atualizar os números:

```bash
python -m flask --app app marketplaces-fila-resumo
```

O resumo agrupa as tarefas por loja e estado. Confira pendências, tarefas em
execução e falhas; uma pausa por limite de requisições pode manter tarefas
pendentes por algum tempo.

Uma tarefa concluída não garante que uma oferta foi encontrada. O resumo da fila
mostra processamento, não a taxa de peças com preço.

### Se uma loja ficar bloqueada por autorização

Primeiro corrija a configuração ou renove a autorização da loja. Depois execute
somente o comando da loja afetada; reativar não corrige credenciais.

**Mercado Livre:**

```bash
python -m flask --app app marketplaces-fila-reativar --loja mercado_livre
```

**Shopee:**

```bash
python -m flask --app app marketplaces-fila-reativar --loja shopee
```

## 5. Analisar as pendências com IA

Depois da coleta, escolha **uma** das duas opções abaixo. Ambas podem ser
processos longos; deixe a análise em um terminal próprio, sem iniciar outra
análise igual em paralelo.

### Opção A — somente sugerir

A IA indica uma peça candidata e registra sua recomendação para revisão:

```bash
python -m flask --app app admin-pendencias-sugerir --limite 500 --aplicar
```

### Opção B — sugerir e decidir

A IA também aceita ou rejeita os casos que alcançarem o mínimo de confiança,
que é **90 por padrão**:

```bash
python -m flask --app app admin-pendencias-sugerir --limite 500 --decidir --aplicar
```

Casos abaixo desse nível continuam para revisão. O aceite passa novamente pelas
validações de associação; a indicação da IA não dispensa essas regras.
Rejeições aplicadas pela IA não têm comando de desfazer.

`--limite 500` limita as pendências analisadas, não o número de requisições à IA.
O comando envia grupos de até 20, com espera e nova tentativa em caso de limite.
Pendências sem candidatas elegíveis ou já analisadas podem não ser enviadas.

Esse passo usa a `GEMINI_API_KEY` configurada no `.env` e consome a cota disponível
do provedor. Não é necessário copiar a chave para o terminal.

### Alternativa pelo painel

Na área de administração, use **Selecionar todas** e **Enviar para a IA**.
Marque **Deixar a IA decidir** se quiser o comportamento da opção B. Mantenha
a aba aberta durante o processamento pelo painel.

## 6. Reverter a aprovação em lote, se necessário

### Conferir o que seria revertido

```bash
python -m flask --app app catalogo-aprovar-lote --reverter
```

### Aplicar a reversão

```bash
python -m flask --app app catalogo-aprovar-lote --reverter --aplicar
```

A reversão retorna para revisão somente as peças aprovadas por esta regra que
**ainda não tenham nenhuma oferta**. Não altera aprovações manuais nem desfaz
ofertas coletadas ou decisões da IA.

O comando não seleciona uma rodada por `--execucao`: pode alcançar aprovações
anteriores feitas pela mesma regra, respeitando os critérios acima.

## 7. Conferir os resultados da rodada

- Na situação informada ao montar este guia, havia **2.910 tarefas antigas do
  Mercado Livre**. Esse número é histórico, não uma contagem atual confirmada;
  confira a fila no passo 4.
- Para medir os resultados depois de enfileirar e processar a rodada, conte,
  por categoria, as peças com **pelo menos uma oferta ativa e preço maior que
  zero**. Não conte várias ofertas da mesma peça como várias peças encontradas.
- Compare com as peças elegíveis consideradas na rodada. O enfileiramento pode
  incluir peças aprovadas antes da amostra; usar apenas 300 como denominador
  pode produzir uma taxa incorreta.
- Separe peças sem oferta, tarefas com falha e tarefas ainda pendentes. Fila
  processada não significa cobertura completa de preços ou estoque confirmado.

## Referências

- [Índice geral dos comandos do projeto](comandos.md).
- [Regras da aprovação em lote](aprovacao-em-lote.md).
- [Funcionamento da fila de marketplaces](marketplaces-fila.md).
- [Painel administrativo e análise por IA](admin.md).
