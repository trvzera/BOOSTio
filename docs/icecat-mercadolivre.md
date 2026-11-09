# Cadastro de peças descobertas no Mercado Livre com fichas Icecat

O fluxo existente de descoberta continua pesquisando anúncios por categoria e marca.
Na importação, o sistema consulta novamente preço, vendedor e condição no Mercado
Livre e tenta associar o produto às peças locais. Se o resultado for rejeitado
(sem candidato comprovado), e a criação de novos estiver habilitada, consulta
uma ficha Icecat antes de decidir o cadastro. Uma associação local ambígua fica
para revisão.

O adaptador Icecat é independente da loja. Ele retorna dados técnicos e fontes.
A gravação usa a transação do importador comum, que relê a pendência e verifica
novamente duplicatas sob bloqueio. Peça, oferta e histórico são confirmados juntos.
Uma falha reverte os três. Uma reexecução da pendência importada retorna inalterada.

## Preparar o ambiente local

Instale as dependências atualizadas. No `backend/.env`, configure:

```dotenv
ICECAT_USUARIO=seu_usuario_icecat
ICECAT_SENHA=sua_senha_icecat
ICECAT_INDICE=/caminho/absoluto/BOOSTio/database/icecat/indice.db
ICECAT_PASTA_FICHAS=/caminho/absoluto/BOOSTio/database/icecat/fichas
```

O índice XML completo em inglês já baixado precisa ser convertido uma vez. A
conversão lê o arquivo em streaming e cria um SQLite de consulta separado do
banco da aplicação. Ela pode demorar e usa espaço em disco para as tabelas e
índices. Uma nova versão é construída em arquivo temporário e substitui a
anterior somente ao terminar, com trava para impedir preparações simultâneas.

A partir da raiz do projeto:

```bash
cd backend
../venv/bin/python -m flask --app app icecat-indice-preparar \
  --arquivo ../files.index.xml.gz
```

Este comando altera somente o cache Icecat. Para uma atualização semanal, baixe
novamente o índice completo pelo acesso oficial e repita a preparação. O download
semanal do índice ainda é uma etapa externa a este adaptador.

## Conferir uma consulta e importar

Exemplo de consulta independente de anúncios, sem gravação de componentes:

```bash
../venv/bin/python -m flask --app app icecat-consultar \
  --categoria memoria_ram --marca Kingston --modelo KVR16N11/8 \
  --titulo 'Kingston ValueRAM KVR16N11/8' --mpn KVR16N11/8 --anuncio-ativo
```

A opção `--anuncio-ativo` considera um anúncio ativo hipotético apenas na consulta
de diagnóstico. Na importação, o estado vem da resposta atual do Mercado Livre.

Para os anúncios que já estão na fila do Mercado Livre, simule primeiro:

```bash
../venv/bin/python -m flask --app app mercadolivre-importar-pendencias \
  --limite 10 --permitir-novos
```

Depois de conferir o resumo, a aplicação é explícita:

```bash
../venv/bin/python -m flask --app app mercadolivre-importar-pendencias \
  --limite 10 --permitir-novos --aplicar
```

`--depois-id` permite paginar a fila. O worker existente usa a mesma importação
quando executado com `--permitir-novos` (ou `CATALOGO_PERMITIR_NOVOS` no ambiente).
A opção continua desabilitada por padrão. Sem `ICECAT_INDICE`, preserva o fluxo
anterior. O resumo por anúncio expõe `icecat` e o lote informa as requisições
Icecat separadamente das requisições Mercado Livre.

## Docker e VPS

Os caminhos do ambiente devem existir dentro do container. Monte um diretório
privado para o índice e o cache, por exemplo `./database/icecat:/dados/icecat`.
Nas execuções avulsas, acrescente `-v "$PWD/database/icecat:/dados/icecat"` ao
`docker compose run`. Para preparar o índice, monte também o `.gz` somente para
leitura. Configure `ICECAT_INDICE=/dados/icecat/indice.db` e
`ICECAT_PASTA_FICHAS=/dados/icecat/fichas` na `.env.production`.

O `catalogo-worker` também precisa dessa montagem para o processamento periódico.
Esta entrega não ativa worker nem importa peças na VPS. As migrations anteriores
do catálogo técnico devem ser aplicadas antes da nova versão, com backup e teste
numa cópia do banco. Nenhuma nova tabela é exigida no banco de peças por este
adaptador.

## Critérios e limites

- Busca primeiro MPN e GTIN aprovado no índice. Quando ambos existem, exige
  interseção entre os resultados. Sem identificadores, tenta o modelo exato,
  exigindo marca e a validação das especificações para confirmação.
- O índice serve para descobrir candidatos. A ficha confirma ID, categoria,
  fabricante, identidade e dados técnicos. Um identificador já cadastrado com
  dados divergentes segue para revisão, evitando duplicação.
- Acima de três candidatos requer revisão. Entre até três, somente uma ficha
  comprovada, sem outra ficha ambígua, pode enriquecer o anúncio.
- Consulta exclusivamente XML inglês no domínio HTTPS oficial. Não segue
  redirecionamentos com credenciais. Limita cada ficha a 2 MB, valida XML sem
  entidades externas e rejeita respostas HTML. HTTP 401/429 e falhas de rede
  interrompem o lote. Não há repetição automática agressiva.
- Limite padrão de 20 downloads por execução, separados por pelo menos um segundo.
  Fichas ficam em cache pela combinação ID + data de atualização do índice.
  A simulação pode baixar e guardar fichas, mas reverte gravações no banco.
- Especificações vêm de atributos estruturados mapeados. Valores ausentes não
  viram zero, consumo estimado ou disponibilidade presumida. Rótulos desconhecidos
  ficam sem preenchimento. Datas e SHA-256 da fonte acompanham os campos.
- O mapeamento inicial cobre campos de CPU, GPU, RAM, placa-mãe, armazenamento,
  fonte e periféricos. Uma categoria pode continuar pendente por falta de campos.
  Refrigeração requer revisão do subtipo (fan, air cooler ou water cooler).
- Fichas válidas para cadastro podem ter lacunas para montagem, como consumo
  elétrico. A flag de elegibilidade bloqueia essas peças na seleção automática.
  A oferta mantém preço e disponibilidade obtidos do Mercado Livre, inclusive
  disponibilidade desconhecida quando a API não a informa.

Uma ficha real autenticada de RAM foi usada para conferir o XML. O fluxo de
criação de componente, oferta e histórico é testado com respostas Mercado Livre
simuladas, incluindo duplicação, conflitos e rollback. Isso não mede cobertura
comercial de todas as categorias. A disponibilidade do índice não assegura
acesso a cada ficha; respeite o plano e as condições da conta Icecat.
