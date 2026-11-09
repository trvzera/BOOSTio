# Aprovação em lote de peças

Peças importadas nascem `em_revisao` e não recebem oferta nem aparecem ao cliente. O comando aprova em
lote as que passam em regras objetivas; o restante continua em revisão.

```bash
cd backend
python -m flask --app app catalogo-aprovar-lote                       # simula todas as categorias
python -m flask --app app catalogo-aprovar-lote --categoria ssd       # simula uma categoria
python -m flask --app app catalogo-aprovar-lote --limite 300 --semente 1 --aplicar   # amostra de 300 por categoria
python -m flask --app app catalogo-aprovar-lote --aplicar             # aprova todas as aprováveis
python -m flask --app app catalogo-aprovar-lote --reverter --aplicar  # desfaz
```

## Regras (`aprovacao_lote_v1`)

1. **Identidade:** fabricante e modelo preenchidos; o modelo tem algum algarismo (`modelo_generico` se não tiver).
2. **Ficha:** a ficha não foi reprovada (`ficha_reprovada`) e todos os campos mínimos da categoria para
   montagem estão preenchidos (`ficha_incompleta`).
3. **Sem duplicata:** nenhuma outra peça da categoria tem o mesmo fabricante+modelo ou o mesmo part number
   (`possivel_duplicata`; ambas ficam em revisão).
4. **Opcional:** `--exigir-identificador` só aprova quem tem part number ou código do fabricante
   (`sem_part_number`). Sem a opção, o relatório mostra `sem_identificador` para você medir o efeito.

## Segurança

- Simula por padrão e mostra, por categoria, quantas aprovaria e o motivo de cada recusa.
- `--limite` aprova no máximo N por categoria, sorteadas (`--semente` repete o sorteio): use para medir
  a taxa de ofertas encontradas antes de aprovar tudo.
- A decisão fica em `validacao_motivo` (`aprovacao_lote_v1: ...`) e `validado_em`.
- `--reverter` volta para revisão só as peças aprovadas por esta regra que **ainda não têm nenhuma oferta**;
  peças aprovadas à mão ou já com oferta não são tocadas.
- Aprovar não cria oferta: a peça só aparece ao cliente depois que uma loja a encontrar com preço.
