# Especificações e identidade comercial

A busca de anúncios e a associação são etapas separadas. Pesquisar pelo nome não comprova que o resultado seja a mesma peça. O comparador continua exigindo identidade, especificações compatíveis e ausência de variantes conflitantes.

## Fichas originais

`catalogo-fichas-originais --pasta DIRETORIO` simula o preenchimento de lacunas usando arquivos `kabum-ID.json` com documentos técnicos originais. `--aplicar` confirma. É necessária uma oferta já vinculada à peça com o mesmo ID da fonte. O adaptador da KaBuM fica em `services/especificacoes_service`, separado do comparador reutilizável. Não executa scripts das páginas.

Campos conhecidos não são sobrescritos. Preços, estoque e benchmarks não são alterados. Cada campo recebe origem, data, evidência e assinatura da identidade. A persistência confere novamente a peça e a oferta original dentro da transação.

`part_number` permanece reservado ao identificador do fabricante. `codigo_modelo_fabricante` guarda um código comercial literal confirmado na ficha/título original. IDs de lojas ficam nas ofertas; referências internas, em `referencia_interna`.

O código comercial só comprova associação enquanto sua procedência e assinatura forem válidas. Não elimina verificações de RGB, versão, sufixos, pacote, socket e demais especificações. Informação ausente não significa valor negativo: `WITH_RGB_LIGHTING=false` não comprova ausência de iluminação monocromática.

## Revisão de GPUs genéricas

`catalogo-gpus-converter-referencias --pasta DIRETORIO` simula a conversão de referências genéricas para o modelo comercial comprovado pela oferta original. `--aplicar` confirma. Nesta experiência, a aplicação foi autorizada somente numa cópia de teste; o catálogo original e a VPS não receberam essa conversão.

São exigidos o mesmo chip, sufixos, categoria desktop/notebook, memória e tipo de memória. ID, preço, estoque e benchmarks são preservados. O fabricante do chip e o nome anterior ficam em `fabricante_chip` e `modelo_referencia`. A tabela `revisao_identidade_peca` guarda valores anteriores e posteriores e as evidências. Identidades aprovadas ou ofertas do Mercado Livre existentes impedem conversão automática.

Prepare o esquema com `catalogo-preparar`, seguindo os procedimentos de backup e simulação do projeto. As novas colunas aceitam ausência de dados. A migração não substitui tabelas do catálogo.

## Medição e limites

Mantenha o conjunto original de peças como denominador. Separe anúncios encontrados, peças distintas reconhecidas, ofertas importadas e componentes novos criados. Uma proposta confirmada na cópia não é uma oferta publicada. Respostas antigas permitem reproduzir o matching, mas não comprovam preços e disponibilidade atuais.

HTTP 403 não autoriza contornar restrições. HTTP 429 interrompe a coleta; o resumo informa o status e a espera solicitada pelo servidor, quando disponível. Retome pelo checkpoint depois da espera, sem repetir grupos concluídos.
