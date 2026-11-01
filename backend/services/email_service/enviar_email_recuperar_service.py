from flask import current_app
from flask_mail import Message
from models import TokenRecuperacao,mail,Usuario
import secrets


class EnviarEmailRecuperarService:
  def executar(self,usuario:Usuario):
    if not usuario or not usuario.ativo:
      raise ValueError("Nenhum usuario encontrado")

    token = self._gerar_token()
    self._salvar_token(usuario,token)

    msg = Message(
        subject='Recuperar senha - BOOSTio',
        recipients=[usuario.email],
    )

    link = self._montar_link(token)
    self._monta_mensagem(msg,link)

    mail.send(msg)

    return True

  @staticmethod
  def _gerar_token() -> str:
    return secrets.token_urlsafe(32)

  def _salvar_token(self,usuario:Usuario,token:str) -> None:
    TokenRecuperacao.emitir(usuario, token)

  @staticmethod
  def _montar_link(token:str) -> str:
    base_url = current_app.config['FRONTEND_URL'].rstrip('/')
    return f"{base_url}/pages/reset-senha.html?token={token}"

  @staticmethod
  def _monta_mensagem(msg:Message,link:str):
    msg.body = f'Para redefinir sua senha, acesse o link: {link}'


    msg.html = f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light only"><title>Recuperar senha — BOOSTio</title></head>
<body style="margin:0;padding:0;background-color:#000000;color:#e5e5ea;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#000000" style="background-color:#000000;"><tr><td style="padding:24px 12px;">
        <div style="font-family: Arial, sans-serif; background-color:#1c1c1e; padding: 32px; border-radius: 16px; max-width: 480px; margin: 0 auto; border: 1px solid #3a3a3c;">
  <h2 style="color:#ffffff; text-align:center;">Recuperar senha</h2>
  <p style="color:#8e8e93; text-align:center;">Recebemos uma solicitação para redefinir a senha da sua conta BOOSTio. Clique no botão abaixo para criar uma nova senha:</p>
  <div style="text-align:center; margin: 24px 0;">
    <a href="{link}" style="display:inline-block; background-color:#007bff; color:#ffffff; text-decoration:none; border-radius: 12px; padding: 14px 32px; font-weight:bold; font-size:15px;">Redefinir senha</a>
  </div>
  <p style="color:#696969; text-align:center; font-size:13px;">Esse link expira em <strong style="color:#8e8e93;">30 minutos</strong>. Se você não solicitou essa alteração, ignore este email.</p>
</div>
</td></tr></table></body></html>
    '''
