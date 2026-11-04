# Etapa 3 — comparação e associação comprovada

`CompararProdutosService` é um comparador sem acesso à rede ou gravação. Retorna `confirmada`, `ambigua` ou `rejeitada`, com evidências, conflitos e pendências específicos. `ClassificarPendenciasService` usa os models para carregar peças e registrar diagnósticos na fila. `AssociarCatalogoService` aplica os mesmos critérios ao fluxo existente de ofertas, incluindo a revalidação do detalhe remoto.

Nome normalizado serve para examinar variantes, não comprova identidade sozinho. Mantemos números, hífens, barras e sufixos. Removemos símbolos de marca antes de normalizar Unicode e tratamos espaçamentos equivalentes. Não há percentual de similaridade aceito automaticamente. A única equivalência explícita de marca adicionada é WD/Western Digital, observada nos snapshots revisados; não confundimos fabricante da GPU com montadora da placa.

Uma confirmação exige identificador forte (MPN/código do fabricante ou GTIN válido com checksum), marca, domínio comprovado, estado ativo e ausência de conflitos técnicos. GTINs de 8/12/13/14 dígitos são comparados preenchendo zeros à esquerda até 14, após validar o checksum. Prefixos internos SEED/DEMO/BOOSTIO/REDE/KABUM não são MPNs. Havendo MPN e GTIN, um não mascara a divergência do outro. Vários códigos divergentes no mesmo atributo exigem revisão.

Os domínios e atributos suportados vêm dos snapshots oficiais existentes: CPU, GPU, RAM, placa-mãe, SSD, HD e mouse. Categorias ainda não mapeadas permanecem ambíguas. Nenhuma categoria sugerida pelo coletor é tratada como prova. São verificadas as especificações presentes em ambos os lados: sockets, núcleos/threads, capacidade, DDR, frequência, tipo de armazenamento, módulos e formato de RAM. Informação ausente não é inventada. Identificador igual não supera uma contradição de título, sufixo, notebook/desktop, kit, capacidade ou BOX/OEM.

RAM em kit é permitida apenas se a quantidade comprovada concordar com a peça local. Combos de CPU/placa-mãe e kits de outras categorias são bloqueados nesta implementação. RAM SO-DIMM sem informação equivalente na ficha local exige revisão. Casos com vários componentes locais plausíveis, vários produtos remotos ou busca incompleta não geram associação automática. O pool local é limitado a 2.000 candidatos; truncamento exige revisão, sem escolha arbitrária.

## Execução

Antes de usar o matching em banco existente, atualize a preparação da etapa 1 e as identidades. `mercadolivre-identidades-preparar` agora acrescenta `gtin` nullable à tabela existente, preservando os MPNs. O manifesto de identidades aceita `gtin` opcional, acompanhado da identidade revisada já exigida; não descobre GTIN por nome.

```bash
python -m flask --app app mercadolivre-identidades-preparar
python -m flask --app app mercadolivre-classificar --limite 20
python -m flask --app app mercadolivre-classificar --limite 20 --aplicar
```

Use o mesmo prefixo Docker Compose dos comandos anteriores na VPS. O padrão é simulação. Aplicar salva evidências e candidatos em `produto_pendente`; não aprova fichas nem cria ofertas. A importação transacional pertence à etapa 5. `--depois-id` permite trabalhar com outro lote. Pendências rejeitadas/importadas não são reabertas. O título individual do anúncio, quando fornecido, também é comparado; ele não pode ser ignorado em favor do catálogo.

## Validação e limites

A fixture `matching_catalogos_reais.json` contém nove snapshots oficiais já coletados, com fontes e a revisão existente, cujo MPN também consta na URL da peça de origem. Os testes verificam os pares positivos e cruzam modelos distintos da mesma categoria como negativos. Essa amostra permite medir falsos positivos nesses pares; não comprova a precisão de todo o marketplace. Os testes adicionais são explicitamente sintéticos e cobrem variantes semelhantes, códigos divergentes, kits, GTIN, buscas incompletas, duplicatas locais e persistência da fila.

Os nomes dos services e classes novos ficam em português. O service da etapa 2 foi renomeado para `DescobrirProdutosService`, com imports e documentação atualizados.

## Atualização: núcleo compartilhado e pontuação

A política acima descreve a primeira implementação. Ela foi substituída pelo núcleo reutilizável com as faixas solicitadas (>80 automático; 60–80 avaliação; <60 sem associação), com proteção contra contradições. MPN/GTIN não são mais obrigatórios: marca, modelo comercial exato e especificações essenciais também podem comprovar a associação. A arquitetura atual e a migração do formato de RAM estão em [associacao-inteligente.md](associacao-inteligente.md).
