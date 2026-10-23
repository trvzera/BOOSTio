from flask_mail import Message
from models import Codigo,mail,Usuario
from html import escape
import re
import secrets


class EnviarEmailService:
  def executar(self,usuario:Usuario):
    if not usuario:
      raise ValueError("Nenhum usuario encontrado")
    if usuario.verificado:
      raise ValueError("Email já verificado")

    Codigo.verificar_limite_envio(usuario.id)
    
    email_destino = usuario.email
    msg = Message(
        subject='Seu código de verificação — BOOSTio',
        recipients=[email_destino],
        extra_headers={"Auto-Submitted": "auto-generated", "X-Auto-Response-Suppress": "All"},
    )

    codigo = self._gerar_codigo()
    self._monta_mensagem(msg,codigo,usuario.nome)

    Codigo.emitir(usuario.id, email_destino, codigo)
    mail.send(msg)

    return True

  @staticmethod
  def _gerar_codigo():
    return f"{secrets.randbelow(1_000_000):06d}"

  @staticmethod
  def _monta_mensagem(msg:Message,codigo:str,nome:str=""):
    if not isinstance(codigo, str) or not re.fullmatch(r"[0-9]{6}", codigo):
      raise ValueError("Código de verificação inválido")
    nome = " ".join(str(nome or "").split())[:60]
    saudacao = f"Olá, {nome}!" if nome else "Olá!"
    msg.body = (
      f"BOOSTio — Confirme seu e-mail\n\n{saudacao}\n\n"
      "Recebemos um pedido para verificar este e-mail na sua conta BOOSTio. "
      "Volte à tela de verificação e informe o código abaixo:\n\n"
      f"{codigo}\n\n"
      "O código expira em 5 minutos e só pode ser usado uma vez. "
      "Se solicitar outro, use o código do e-mail mais recente.\n\n"
      "Não compartilhe este código. A equipe BOOSTio nunca pedirá seu código por mensagem.\n"
      "Se você não solicitou a verificação, ignore este e-mail.\n\n"
      "Equipe BOOSTio\nMensagem automática de segurança da sua conta."
    )
    # HTML transacional sem imagens remotas, rastreamento, anexos ou fontes externas.
    # A versão em texto acima mantém o mesmo conteúdo e código.
    msg.html = f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta name="color-scheme" content="dark"><meta name="supported-color-schemes" content="dark"><title>Confirme seu e-mail — BOOSTio</title></head>
<body style="margin:0;padding:0;background-color:#000000;color:#e5e5ea;font-family:Poppins,Arial,Helvetica,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;">Confirme seu e-mail com o código de uso único. Ele é válido por 5 minutos.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#000000" style="background-color:#000000;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#1c1c1e" style="max-width:520px;background-color:#1c1c1e;border:1px solid #3a3a3c;border-top:3px solid #007bff;border-radius:20px;"><tr><td style="padding:32px 24px;color:#e5e5ea;font-family:Poppins,Arial,Helvetica,sans-serif;">
<p style="margin:0 0 28px;color:#ffffff;font-family:Lexend,Arial,Helvetica,sans-serif;font-size:22px;font-weight:bold;">BOOST<span style="color:#007bff;">io</span></p>
<h1 style="margin:0 0 20px;font-family:Lexend,Arial,Helvetica,sans-serif;font-size:26px;line-height:1.3;color:#007bff;">Confirme seu <span style="white-space:nowrap;">e-mail</span></h1>
<p style="margin:0 0 12px;font-size:16px;line-height:1.6;">{escape(saudacao)}</p>
<p style="margin:0 0 24px;font-size:16px;line-height:1.6;">Recebemos um pedido para verificar este e-mail na sua conta BOOSTio. Volte à tela de verificação e informe:</p>
<p data-verification-code style="margin:0 0 20px;padding:20px 12px;border:1px solid #3a3a3c;border-radius:12px;background-color:#000000;text-align:center;font-family:Lexend,Arial,Helvetica,sans-serif;font-size:34px;font-weight:600;line-height:1.4;font-variant-numeric:tabular-nums;letter-spacing:4px;color:#ffffff;">{codigo}</p>
<p style="margin:0 0 24px;font-size:14px;line-height:1.7;color:#a1a1a6;">Válido por <strong style="color:#e5e5ea;">5 minutos</strong>, para um único uso. Se solicitar outro, use o código do e-mail mais recente.</p>
<p style="margin:0 0 12px;font-size:14px;line-height:1.7;color:#a1a1a6;"><strong style="color:#e5e5ea;">Não compartilhe este código.</strong> A equipe BOOSTio nunca pedirá seu código por mensagem.</p>
<p style="margin:0 0 28px;font-size:14px;line-height:1.7;color:#a1a1a6;">Se você não solicitou a verificação, ignore este e-mail.</p>
<p style="margin:0;padding-top:20px;border-top:1px solid #3a3a3c;font-size:13px;line-height:1.7;color:#a1a1a6;">Equipe BOOSTio<br>Mensagem automática de segurança da sua conta.</p>
</td></tr></table></td></tr></table></body></html>'''
