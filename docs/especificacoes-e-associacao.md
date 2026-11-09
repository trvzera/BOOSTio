# Especificações e associação do catálogo

O núcleo em `services/catalogo_service` recebe `ProdutoNormalizado` e não depende de uma loja. O adaptador do Mercado Livre traduz atributos reais da API para esse contrato. As pesquisas por marca continuam disponíveis; pesquisas por peça ajudam a procurar modelos que não apareceram nos primeiros resultados genéricos.

## Fluxo

1. Descobrir anúncios, armazenando a resposta original na fila.
2. Separar referência interna, MPN e ID da loja com `catalogo-identificadores-separar`.
3. Opcionalmente preencher lacunas das peças existentes com `catalogo-especificacoes-preencher`.
4. Classificar novamente a fila e importar apenas associações confirmadas pelo fluxo existente.

O preenchimento é uma etapa administrativa explícita; não foi ativado automaticamente no worker. Não cria peças ou ofertas, não consulta páginas externas e não muda preços, estoque ou benchmarks. Ele usa as fichas já coletadas, exigindo marca, categoria, estado ativo, código comercial completo e pelo menos duas especificações compatíveis (ou identificação conclusiva). Título e ficha precisam concordar. Códigos internos não são MPN. Só campos vazios são preenchidos; `False` e zero já cadastrados não significam ausência. Contradições impedem a atualização. Mais de uma peça compatível exige revisão.

`Peca.fontes_especificacoes` guarda, por campo, URL, valor original, valor convertido, código, data, critério e hash da ficha. A persistência é feita no model, com bloqueio e nova conferência do estado técnico, transação por peça e rollback em falhas. Vínculos previamente válidos têm sua assinatura atualizada; vínculos já inválidos não são reativados. O retorno de simulação mostra o que seria preenchido sem gravar. Repetir a aplicação não altera campos já preenchidos.

## Preparação e execução

Faça backup antes de aplicar alterações. No ambiente Flask configurado, primeiro confira e aplique a migração aditiva, que acrescenta `fontes_especificacoes` JSON nullable nas tabelas de componentes (SQLite e MySQL):

```bash
python -m flask --app app catalogo-preparar
python -m flask --app app catalogo-preparar --aplicar
python -m flask --app app catalogo-identificadores-separar
python -m flask --app app catalogo-identificadores-separar --aplicar
```

Preencher apenas um lote de fichas já coletadas:

```bash
python -m flask --app app catalogo-especificacoes-preencher --categoria memoria_ram --limite 100
python -m flask --app app catalogo-especificacoes-preencher --categoria memoria_ram --limite 100 --aplicar
```

Continue com `--depois-id` igual a `ultima_pendencia_id` do resumo. São processados anúncios pendentes ou em revisão; rejeitados e importados não são reabertos automaticamente. Falhas geram saída não zero e resumo. Os contadores são por anúncio; uma peça pode aparecer em vários anúncios. A etapa não substitui a classificação/importação posterior nem publica automaticamente os dados.

Para preparar pesquisas mais específicas:

```bash
python -m flask --app app catalogo-planejar-pecas --categoria memoria_ram --limite 100 --resultados 10 > plano-memorias.json
python -m flask --app app catalogo-worker --plano plano-memorias.json --uma-vez
```

O primeiro comando só gera um plano: usa MPN verdadeiro quando existe e o modelo completo caso contrário, preservando sufixos. Nunca usa `KABUM-*` como nome de fabricante. O worker existente executa o plano com suas travas, limites, checkpoints e política de gravação; consulte a documentação do worker antes de usar `--aplicar`. Buscar pelo nome de uma peça não comprova que o resultado corresponde a ela: todos os resultados continuam passando pelo matching.

## Matching v3

Há perfis técnicos para as 17 categorias, conversões explícitas de unidades e distinção entre DIMM/UDIMM equivalente, SO-DIMM e memórias registradas. Códigos comerciais completos podem estar dentro de descrições longas. Chipset isolado não identifica a edição comercial de uma placa. Sufixos, RGB, Wi-Fi, cores e revisões continuam protegidos. Black/Red/Blue de famílias de SSD/HD não são tratados automaticamente como cor do gabinete; cores de switch não são cor do teclado.

GTIN inválido ou múltiplo é registrado como aviso, sem servir de prova. Um GTIN válido conhecido divergente continua bloqueando a associação. Ausências técnicas e modelos ambíguos não são resolvidos baixando o limite: mais de 80 pontos continua necessário, com candidato único e sem conflitos. A pontuação não é probabilidade estatística.

## Resultado medido e limites

Reprodução offline dos mesmos 1.318 anúncios reais anteriormente coletados, sem novas chamadas ao Mercado Livre: antes eram 21 anúncios confirmados para 19 peças; agora são 51 anúncios para 41 peças. Em relação às 1.535 peças do catálogo, a cobertura passou de 1,24% para 2,67%. Isso ainda está longe da meta de 70%.

O preenchimento atualizou 14 peças distintas na cópia de teste e falhou em zero entradas. Exemplo: Crucial `CT8G4DFRA32A`, anteriormente sem formato, recebeu DIMM a partir de UDIMM explícito e seu código de fabricante. O total final continuou em 51 anúncios/41 peças: um anúncio ganhou confirmação, mas outro passou para revisão após uma informação técnica tornar a combinação ambígua. Portanto, enriquecimento não foi contado como aumento automático de associações.

Não houve importação de ofertas nem alteração do catálogo original ou da VPS nesta validação. Os relatórios locais estão em `output/match-v3/`. As pesquisas por peça foram validadas na geração do plano e nos testes, mas ainda não executadas em nova varredura real. Campos ausentes nas duas fontes continuam desconhecidos; não se deduz consumo, especificação ou benchmark de nomes aproximados. Nenhuma base externa completa de fabricantes foi implementada nesta etapa.
