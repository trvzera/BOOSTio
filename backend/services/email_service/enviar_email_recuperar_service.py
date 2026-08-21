from flask import current_app
from flask_mail import Message
from models import TokenRecuperacao,mail,Usuario
from werkzeug.security import generate_password_hash
import secrets


class EnviarEmailRecuperarService:
  def executar(self,usuario:Usuario):
    if not usuario:
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
    #Invalida qualquer link de recuperação anterior ainda não usado.
    TokenRecuperacao.deletar_tokens_usuario(usuario.id)

    token_recuperacao = TokenRecuperacao(
      usuario_id = usuario.id,
      token_hash = generate_password_hash(token)
    )

    token_recuperacao.salvar()

  @staticmethod
  def _montar_link(token:str) -> str:
    base_url = current_app.config['FRONTEND_URL'].rstrip('/')
    return f"{base_url}/pages/reset-senha.html?token={token}"

  @staticmethod
  def _monta_mensagem(msg:Message,link:str):
    msg.body = f'Para redefinir sua senha, acesse o link: {link}'
    msg.html = f'''
        <div style="font-family: Arial, sans-serif; background-color:#1c1c1e; padding: 32px; border-radius: 16px; max-width: 480px; margin: 0 auto; border: 1px solid #3a3a3c;">
  <h2 style="color:#ffffff; text-align:center;">Recuperar senha</h2>
  <p style="color:#8e8e93; text-align:center;">Recebemos uma solicitação para redefinir a senha da sua conta BOOSTio. Clique no botão abaixo para criar uma nova senha:</p>
  <div style="text-align:center; margin: 24px 0;">
    <a href="{link}" style="display:inline-block; background-color:#007bff; color:#ffffff; text-decoration:none; border-radius: 12px; padding: 14px 32px; font-weight:bold; font-size:15px;">Redefinir senha</a>
  </div>
  <p style="color:#696969; text-align:center; font-size:13px;">Esse link expira em <strong style="color:#8e8e93;">30 minutos</strong>. Se você não solicitou essa alteração, ignore este email.</p>
</div>
    '''
