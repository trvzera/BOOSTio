
### Acesso de administradores com aplicativo autenticador

Prepare o segundo fator antes de direcionar tráfego para a nova versão. No ambiente da API, defina `ADMIN_2FA_CHAVE` com uma chave Fernet exclusiva, gerada com `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` em terminal privado. Guarde a chave no gerenciador de segredos e junto ao procedimento de recuperação dos backups.

Na imagem atualizada, a partir de `backend`, crie a tabela no banco existente. O comando pode ser repetido.

```bash
python -m flask --app app admin-2fa-preparar
```

Para cada administrador, use um terminal interativo privado com o titular. Informe o e-mail da conta, adicione a chave exibida ao aplicativo como TOTP de seis dígitos, período de 30 segundos e SHA-1, e confirme o código no terminal. Comece o primeiro login com o próximo código.

```bash
python -m flask --app app admin-2fa-configurar --email EMAIL_DO_ADMIN
```

Publique frontend e API juntos. Cada login administrativo concluído substitui a sessão anterior. Em caso de perda do aparelho, um operador da VPS verifica a identidade do titular e repete o cadastro em terminal privado. A confirmação substitui o segredo e encerra as sessões da conta.

### Conexão com o Discord

No painel [Discord Developer Portal](https://discord.com/developers/applications), abra o aplicativo usado para OAuth2 e cadastre a URL de retorno da API em **OAuth2 → Redirects**. Para a produção da BOOSTio, use `https://api.boostio.com.br/auth/discord/callback`. Para desenvolvimento com a API local, use `http://127.0.0.1:5000/auth/discord/callback`, ou o endereço definido em `API_PUBLIC_URL` com o mesmo caminho.

Defina `DISCORD_CLIENT_ID` e `DISCORD_CLIENT_SECRET` no ambiente da API com as credenciais OAuth2 do aplicativo. Em banco existente, execute a migração na imagem atualizada antes de publicar a API.

```bash
python -m flask --app app usuarios-discord-preparar
```

Em **Configurações → Discord**, autorize o acesso ao perfil básico. A BOOSTio guarda o ID e o nome de usuário da conta vinculada. Os tokens do Discord são descartados após a consulta ao perfil. O botão **Desconectar Discord** apaga o vínculo na BOOSTio. O usuário também pode gerenciar a autorização no Discord em **Configurações de usuário → Aplicativos autorizados**.
