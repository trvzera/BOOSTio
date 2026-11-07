# Preço e link só na oferta

## Regra

Preço, disponibilidade, data da cotação e link de loja pertencem à tabela `oferta`. As tabelas de
peças guardam só a ficha técnica (identidade, especificações, benchmark, imagem, validação).
`Peca.preco`, `Peca.esgotado`, `Peca.preco_atualizado_em` e `Peca.kabum_external` continuam existindo
**somente para leitura**: são calculados a partir das ofertas ativas (`models/preco_oferta.py`), então o
catálogo, a geração de builds, os benchmarks e o JSON do front-end mantêm os mesmos nomes de campos.

A oferta que define o valor lido na peça é, nesta ordem: disponível (`esgotado = falso`), de estoque
desconhecido, esgotada; em cada grupo, a de menor preço. `kabum_external` (campo `link`) é sempre o
link da oferta ativa da KaBuM. Peça sem oferta tem preço e disponibilidade `NULL`.

A geração de builds passou a usar o **menor preço entre as ofertas ativas disponíveis**, e não só o
da KaBuM. Ofertas do Mercado Livre e da Shopee entram quando a associação revisada já as gravou como
ativas e com estoque conhecido como disponível.

## Escrita

| Operação | Onde |
| --- | --- |
| Trocar ou remover o link da KaBuM | `repositories/ofertas_kabum_repository.definir_link` (a oferta antiga é desativada, o histórico fica) |
| Cotação da KaBuM (`precos-atualizar`) | `ofertas_kabum_repository.aplicar_cotacao`; histórico em `historico_oferta` (uma linha por mudança ou por dia) |
| Carga inicial (`pecas-popular`) | `Peca.cadastrar_ausentes` separa preço/link do item e grava a oferta |
| Mercado Livre e Shopee | sem mudança (`ofertas_repository`) |

`ConsultaPreco` continua controlando quais anúncios já foram consultados no dia. Criar uma peça com
`preco=`, `esgotado=` ou `kabum_external=` não é mais aceito pelos serviços; os testes antigos usam
`tests/compat_oferta.py` para montar cenários.

## Migração dos dados (fase 1)

```sh
python -m flask --app app ofertas-kabum-migrar            # simula e conta
python -m flask --app app ofertas-kabum-migrar --aplicar  # grava
```

Copia link, preço, estoque e data de cada peça com link da KaBuM para uma oferta `kabum`, e as
observações de `historico_preco` que têm preço para `historico_oferta`. Repetir não duplica nem
sobrescreve uma cotação já gravada na oferta. As colunas antigas **não são apagadas**: ficam como cópia
de segurança, e as verificações de esquema as ignoram. Observações sem preço (só "esgotado") permanecem
apenas em `historico_preco`.

Rode antes de subir esta versão: sem as ofertas, as peças ficam sem preço. Faça backup do banco.

Medido numa cópia do banco local: 1.534 ofertas criadas, 51.921 peças sem link (catálogo técnico),
segunda execução sem alterações e preço lido igual à coluna antiga em todas as 5.001 peças de CPU/GPU
comparadas.

## Pendente

- **Fase 2:** comando que apaga as quatro colunas das tabelas de peças e recria o índice
  `ix_<tabela>_publicacao` após validação com dados reais.
- **Histórico de menor preço entre lojas:** `/catalogo/<cat>/<id>/historico-precos` segue mostrando a
  KaBuM, porque o front-end descarta pontos cuja `loja` não seja `kabum`. Mostrar o menor preço entre
  lojas exige mudar o front-end.
- Não foi testado em MySQL real (subconsultas correlacionadas por peça e travas em `refresh ... FOR UPDATE`).
