# Etapa 5 — importação transacional

`ImportarProdutoService` consulta novamente o detalhe oficial e as ofertas do catálogo antes de entrar na transação. Somente importa o anúncio externo da pendência, na condição nova e com vendedor conferido. Preço e quantidade disponíveis são os da consulta atual; a cotação original da descoberta não é reutilizada.

`RepositorioImportacaoCatalogo` coordena uma transação por anúncio. Reutiliza a linha `ControleColeta` para serializar importações e as operações concorrentes já existentes. Sob bloqueio, relê pendência e candidatos, repete o matching e verifica mudanças desde a consulta. Uma peça existente recebe apenas oferta e histórico, sem alteração de sua ficha ou preço principal. Duplicatas locais, título divergente, vendedor alterado e categoria incerta exigem revisão.

Um novo componente só é criado com `--permitir-novos`, identidade comprovada e todos os requisitos do enriquecimento satisfeitos. Valores ausentes de campos opcionais ficam NULL explícito, inclusive flags com default False. Não inserimos um consumo zero para satisfazer o model nem presumimos estoque. Os casos sem fonte completa continuam pendentes. A publicação de novos fica desativada por padrão até a revisão do lote inicial prevista na etapa 8.

Peça nova, identidade, vínculo, oferta, primeiro histórico e resultado/origem da importação são confirmados juntos. Uma falha desfaz todo esse conjunto. A aplicação de ofertas existente recebeu opções internas para participar da transação externa e preservar as demais ofertas, mantendo seu comportamento padrão para os coletores anteriores. Disponibilidade conhecida é preservada; desconhecida permanece NULL.

O resultado com fontes é gravado nas evidências da pendência e seu estado passa a `importado`. Repetir a mesma pendência importada retorna `inalterada`, sem novas peças, ofertas, históricos ou alterações de datas. Monitoramento posterior usa o coletor de ofertas existente. Uma falha de lote registra motivo genérico na pendência e aparece no resumo; detalhes sensíveis de SQL/OAuth não são publicados.

Prepare previamente `catalogo-preparar`, `mercadolivre-identidades-preparar`, as tabelas de ofertas/histórico e o controle de coleta pelos comandos existentes. A execução não cria ou corrige esquema implicitamente.

```bash
python -m flask --app app mercadolivre-importar-pendencias --limite 20
python -m flask --app app mercadolivre-importar-pendencias --limite 20 --aplicar
```

`--permitir-novos` habilita a criação validada; use primeiro sem `--aplicar` para revisar propostas. `--depois-id`, `--max-requisicoes` e `--intervalo` mantêm a execução limitada. O comando imprime resumo, e retorna erro se houver falhas. Não executamos importação na VPS nesta implementação.

A decisão/transação foi extraída para `services/catalogo_service/ImportarCatalogoService`, com contrato normalizado para qualquer loja. A integração Mercado Livre apenas consulta/converte os dados e chama esse núcleo. A política percentual e os requisitos sem MPN estão em [associacao-inteligente.md](associacao-inteligente.md).
