
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
