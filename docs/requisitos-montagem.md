# Requisitos técnicos por peça e por combinação

A completude técnica é separada da validação de identidade e da oferta. O indicador
`ficha_montagem_validada` agora significa que a peça tem os dados mínimos para ser
considerada como candidata, sujeita às verificações da build. Não aprova fabricante,
modelo, procedência, BIOS, oferta ou disponibilidade.

## Campos opcionais para candidatura

- RAM: latência não impede candidatura; formato, DDR, capacidade, frequência e
  quantidade de módulos continuam exigidos.
- HD: RPM não impede candidatura; capacidade e interface continuam exigidas.
- Fans e coolers: iluminação é opcional; tamanho, quantidade do kit e sockets
  aplicáveis continuam necessários.
- Monitor: painel é opcional; resolução, frequência, tamanho e conexão permanecem.
  A preferência padrão por IPS/VA deixou de excluir outros painéis ou dado ausente.
  O método de filtros ainda admite uma lista de painéis exigidos, para consumidores
  que efetivamente tenham essa restrição; não foi criado novo parâmetro de frontend.
- CPU: vídeo integrado e inclusão de cooler podem ser desconhecidos na peça. Sem
  vídeo confirmado, a combinação exige GPU dedicada. Sem cooler incluso confirmado,
  exige um cooler separado. O validador final rejeita socket de cooler não verificado.

`requisitos_montagem.MINIMOS` concentra a regra. Os requisitos de matching não foram
relaxados: uma latência ou cor diferente ainda pode indicar outro SKU e impedir a
associação. Campos não foram apagados, nem preenchidos com suposições.

## Planejamento de potência

`PlanejarPotenciaService` concentra reservas v1:

| Componente sem consumo | Reserva |
|---|---:|
| Placa-mãe | 50 W por produto |
| RAM | 10 W por módulo físico |
| SSD | 15 W por produto |
| HD | 30 W por produto |
| Fan | 10 W por fan físico |
| Air cooler | 30 W por produto |
| Water cooler | 60 W por produto |
| Gabinete/acessórios internos | 20 W por produto |

São parâmetros conservadores de planejamento, não máximos universais nem medições.
O consumo cadastrado prevalece quando disponível e é multiplicado pela quantidade
comprada. Consumo de um kit cadastrado já é por produto: não multiplica novamente
pelo número de pentes/fans. Na ausência dele, a reserva usa unidades físicas ×
quantidade de kits. Kit sem quantidade conhecida continua não verificável. CPU/GPU
não recebem reserva genérica e exigem consumo positivo, finito e confirmado.

A fonte deve cobrir a soma conhecida + reservas com 20% de margem. A regra expõe
valores conhecidos, reservas, unidades, margem e campos desconhecidos no diagnóstico
`fonte-potencia`, com origem `politica_planejamento_energia`. O prompt recebe a mesma
política. Estimativas não são persistidas em `consumo_energia`, não comprovam picos,
qualidade da fonte nem capacidade térmica. Conectores continuam sendo conferidos.
Geração automática não aceita potência sem verificação suficiente; rascunhos manuais
continuam podendo registrar pendências.

## Reavaliação das fichas existentes

Na pasta `backend`:

```bash
python -m flask --app app catalogo-montagem-reavaliar
python -m flask --app app catalogo-montagem-reavaliar --aplicar --resumo ../output/reavaliacao.json
```

Simula por padrão. A gravação recalcula apenas o indicador técnico das peças com
origem docyx, em lotes, com bloqueio e transação. Não altera aprovação de identidade,
preço, estoque ou ofertas, nem os registros legados sem essa origem. Reexecutar não
gera novas alterações. Importação docyx e enriquecimento BuildCores também recalculam
o indicador para peças novas/alteradas. Não há alteração de esquema nesta etapa.

## Medição local

Sobre as 51.920 peças importadas do docyx:

| Base | Mínimos anteriores | Novos mínimos |
|---|---:|---:|
| Catálogo local, sem os dados BuildCores | 6.828 | 10.668 |
| Cópia enriquecida com BuildCores | 6.828 | 12.751 |

No subconjunto de 2.118 peças enriquecidas, antes nenhuma atendia a todas as antigas
exigências. Agora 2.089 atendem aos mínimos para candidatura: 210 CPUs, 75 placas-mãe,
1.691 memórias, 3 water coolers e 110 fans. Restam 3 sockets não reconhecidos, 25
padrões de memória não aceitos pelo normalizador atual e 1 compatibilidade de cooler.
Isso não libera automaticamente as identidades que permanecem `em_revisao`, nem
substitui ofertas ou validação da combinação final.

Relatórios: `output/requisitos-montagem/simulacao.json`, `enriquecidas.json` e
`resultado.json`. Reavaliação local e da cópia executadas com backup e comparação
para assegurar preservação dos demais dados. Nenhuma operação foi feita na VPS.
