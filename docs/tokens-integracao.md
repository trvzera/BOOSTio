# Model de tokens de integração

`TokenIntegracao` estende `ModeloBase`. Guarda integração, Client ID, conta externa,
access token e refresh token cifrados, expiração em UTC sem timezone, estado de
renovação pendente e data da última renovação. Uma restrição única impede repetir
o mesmo trio integração/aplicação/conta. Não há vínculo com Usuario: a conta é a
identidade externa usada pela integração administrativa do BOOSTio.

Os tokens são recuperáveis porque precisam ser usados na API. Fernet fornece
criptografia autenticada; hashes não atenderiam a esse uso. A chave fica em
`INTEGRACOES_TOKEN_CHAVE`, separada do banco e de SECRET_KEY. Não há geração
silenciosa na inicialização. Gere uma única vez em terminal privado:

```sh
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Guarde a saída no ambiente do backend e em backup seguro, fora do Git e dos dumps
do banco. Todos os processos precisam da mesma chave. Perdê-la impede recuperar
os tokens. Substituí-la sem recifrar os registros existentes também impede leitura;
rotação de chave não está implementada neste model.

## Uso

```python
from datetime import datetime, timezone, timedelta
from models import TokenIntegracao

token = TokenIntegracao(integracao="mercado_livre", client_id=client_id, conta_id=conta_id)
token.definir_tokens(access_token, refresh_token,
                     datetime.now(timezone.utc) + timedelta(seconds=expires_in))
token.salvar()
```

`definir_tokens` valida e cifra os dois valores antes de alterar a instância; não
faz commit nem chama a API. `access_token` e `refresh_token` são propriedades de
leitura que decifram explicitamente. Não serialize essas propriedades em respostas
públicas. `esta_expirado` usa margem padrão de 60 segundos.

`buscar(..., bloquear=True)` usa SELECT FOR UPDATE no MySQL com atualização dos
valores da sessão. O chamador deve manter a transação até commit/rollback. SQLite
não oferece o mesmo bloqueio de linha; os testes SQLite não comprovam concorrência
no MySQL. O model não resolve sozinho a atomicidade entre a API externa e o banco:
uma falha após consumir refresh token ainda requer tratamento pelo service.

## Migration

Faça backup antes de modificar o esquema da VPS. Após instalar as dependências e
reconstruir a imagem:

```sh
docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app integracoes-tokens-preparar
```

A migration cria somente `token_integracao`, aceita SQLite/MySQL e é repetível.
Se encontrar nomes de colunas incompatíveis, recusa a tabela em vez de alterá-la.
Não é uma ferramenta de reparação de tipos, índices ou constraints de tabelas
criadas manualmente.

## Uso pelo Mercado Livre

O service agora usa este model por meio do repository SQL. A coluna `versao`
protege escritas concorrentes com atualização condicional, em transações próprias.
A transferência do arquivo e a renovação estão descritas em
[mercado-livre.md](mercado-livre.md). Não há fallback automático ao arquivo ou aos
tokens do ambiente. O método `buscar(bloquear=True)` permanece disponível, mas o
fluxo de renovação usa controle otimista de versão, sem locks durante a rede.

Não adicione esta coluna manualmente: a migration é apropriada a uma instalação
que ainda não possua `token_integracao`. Se já criou uma versão anterior da tabela,
a verificação de colunas recusará o esquema e será necessário migrar `versao`
explicitamente antes de ativar a nova versão.
