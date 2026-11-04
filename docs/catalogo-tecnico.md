# Catálogo técnico independente de lojas

O cadastro técnico e a oferta são processos separados. Uma ficha validada pode
criar um componente sem preço ou estoque; isso não cria uma oferta nem confirma
que há produto à venda. Valores desconhecidos são NULL, nunca zero ou disponível
por suposição. Nenhuma integração com Icecat foi implementada nesta etapa.

## Migração

Faça backup antes de alterar a estrutura. Os comandos usam o banco configurado
na aplicação; confira o ambiente antes de executar. Com o esquema anterior do
catálogo já preparado, execute primeiro a simulação:

```bash
cd backend
../venv/bin/python -m flask --app app catalogo-tecnico-preparar
../venv/bin/python -m flask --app app catalogo-tecnico-preparar --aplicar
```

Em Docker na VPS, substitua o prefixo Python por
`docker compose --env-file .env.production run --rm --no-deps -T api python`.
Arquivos locais devem ser montados no container para importação. Não aplique
migrações na produção antes de testar numa cópia do MySQL. Esta etapa foi testada
em SQLite; a alteração MySQL ainda precisa dessa validação real. DDL no MySQL
pode confirmar alterações parcialmente; a migração permite reexecução, mas backup
continua necessário.

## Formato interno versão 1

Este é um contrato do BOOSTio, não o formato de uma API externa. Exemplo sintético
para testar a importação; as URLs de exemplo não são evidência real e precisam
ser substituídas por fontes efetivamente conferidas antes de um cadastro real:

```json
{
  "versao": 1,
  "provedor": "fonte-tecnica",
  "id_externo": "ssd-1",
  "categoria": "ssd",
  "identidade": {
    "fabricante": "Kingston",
    "modelo": "A400 480GB",
    "mpn": "SA400S37/480G"
  },
  "especificacoes": {
    "capacidade_gb": 480,
    "tipo": "SSD",
    "interface": "SATA",
    "formato": "2.5",
    "consumo_energia": 1.5
  },
  "fontes": {
    "fabricante": {"url": "https://example.org/ficha"},
    "modelo": {"url": "https://example.org/ficha"},
    "mpn": {"url": "https://example.org/ficha"},
    "capacidade_gb": {"url": "https://example.org/ficha"},
    "tipo": {"url": "https://example.org/ficha"},
    "interface": {"url": "https://example.org/ficha"},
    "formato": {"url": "https://example.org/ficha"},
    "consumo_energia": {"url": "https://example.org/ficha"}
  }
}
```

Também aceita GTIN válido em `identidade.gtin` e sua fonte. Não use o ID da loja
como MPN. `atualizado_na_origem` é opcional, em ISO 8601; só informe se fornecido
pela origem. Preço, disponibilidade, referências internas, benchmarks, estado de
validação e IDs locais são proibidos nas especificações técnicas.

O arquivo pode conter um objeto ou uma lista com até 1.000 fichas, no máximo
10 MiB. Cada ficha tem limite de 256 KiB. O formato do lote inteiro é conferido
antes da primeira gravação; origens repetidas no mesmo lote são recusadas.
Cada ficha usa uma transação: uma falha interrompe o lote, preservando as fichas
já concluídas. Reexecute o arquivo após corrigir o problema; a operação é
idempotente. A simulação reverte cada ficha; portanto não representa conflitos
entre duas novas identidades de origens diferentes no mesmo lote.

```bash
../venv/bin/python -m flask --app app catalogo-tecnico-importar --arquivo fichas.json
../venv/bin/python -m flask --app app catalogo-tecnico-importar --arquivo fichas.json --aplicar
../venv/bin/python -m flask --app app catalogo-tecnico-listar --estado pendente_dados
../venv/bin/python -m flask --app app catalogo-tecnico-revisar --id 1 --acao rejeitar --responsavel operador --motivo 'Modelo incorreto' --aplicar
../venv/bin/python -m flask --app app catalogo-tecnico-revisar --id 1 --acao reabrir --responsavel operador --motivo 'Fonte corrigida' --aplicar
../venv/bin/python -m flask --app app catalogo-tecnico-revisar --id 1 --acao aprovar --responsavel operador --motivo 'Dados conferidos' --aplicar
```

Todos os comandos de alteração simulam por padrão. Responsável e motivo são
obrigatórios na revisão. A aprovação revalida a ficha; não é um bypass para
conflitos. Corrija os dados no arquivo e reimporte após reabrir uma rejeição.
Rejeitar uma ficha já importada é bloqueado: despublicar uma peça exige análise
própria para preservar builds e ofertas existentes.

## Fluxo e manutenção

- `FichaTecnicaCatalogo`: origem única por provedor e ID, documento recebido,
  hash, pendências, diagnóstico e vínculo com a peça.
- `RevisaoFichaTecnica`: transições com responsável, motivo e hash da versão.
  Não armazena todas as versões completas anteriores do documento.
- `ImportarBaseTecnicaService`: valida o contrato, compara identidade e dados
  técnicos e decide importar ou encaminhar para revisão.
- `RepositorioCatalogoTecnico`: serializa gravações pela abstração existente
  de controle de coleta e confirma ou reverte a transação.
- `RevisarFichaService`: decisões administrativas com revalidação e proteção
  contra alteração concorrente da ficha durante aprovação.

Fichas insuficientes ficam em `pendente_dados`; conflitos e ambiguidades em
`em_revisao`. Uma identidade já existente com especificações divergentes não
cria outra peça. Dados técnicos conhecidos não são sobrescritos automaticamente.
Campos ausentes podem ser preenchidos quando a associação é comprovada.

A elegibilidade para montagem é separada da identidade técnica. Uma peça nova
pode existir com ficha incompleta para montagem, mas fica fora dos candidatos.
Sem preço válido ou disponibilidade confirmada, também não entra na seleção.
O legado mantém o comportamento anterior: flag NULL não afirma auditoria.

## Limitações e próximas etapas

URLs HTTPS são validadas estruturalmente; o importador local não baixa nem
comprova o conteúdo das páginas. O arquivo deve vir de um operador ou adaptador
confiável. Não exponha este comando como endpoint público para conteúdo livre.

Ainda faltam: adapter autenticado da fonte escolhida, medição real de cobertura,
sincronização incremental periódica e promoção comercial de peças técnicas a
partir de ofertas verificadas de várias lojas. Os coletores e o matching de
ofertas existentes continuam separados. Não há promessa de 70% de cobertura.
A disponibilidade de dados públicos não comprova licença comercial; valide os
termos da fonte antes de automatizar coleta e publicação.
