import re
import time
import secrets

from cryptography.fernet import Fernet, InvalidToken as SegredoInvalido
from cryptography.hazmat.primitives.twofactor import InvalidToken
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.twofactor.totp import TOTP
from flask import current_app

from models import db
from models.fator_admin import FatorAdmin


def cifra():
    try:
        return Fernet(current_app.config.get("ADMIN_2FA_CHAVE") or b"")
    except ValueError:
        raise ValueError("A equipe precisa configurar a chave de autenticação administrativa.") from None


def intervalo_valido(segredo, codigo):
    if not isinstance(codigo, str) or not re.fullmatch(r"[0-9]{6}", codigo):
        return None
    autenticador = TOTP(segredo, 6, SHA1(), 30)
    atual = int(time.time()) // 30
    for intervalo in (atual, atual - 1, atual + 1):
        try:
            autenticador.verify(codigo.encode("ascii"), intervalo * 30)
            return intervalo
        except InvalidToken:
            continue
    return None


def consumir_codigo(usuario, codigo):
    fator = db.session.get(FatorAdmin, usuario.id)
    if fator is None:
        raise ValueError("Peça à equipe responsável que configure o autenticador da conta.")
    try:
        segredo = cifra().decrypt(fator.segredo_cifrado)
    except SegredoInvalido:
        raise ValueError("A equipe precisa conferir a configuração do autenticador.") from None
    intervalo = intervalo_valido(segredo, codigo)
    if intervalo is None:
        return False
    token = secrets.token_hex(32)
    atualizados = FatorAdmin.query.filter(
        FatorAdmin.usuario_id == usuario.id,
        FatorAdmin.ultimo_intervalo < intervalo,
        FatorAdmin.segredo_cifrado == fator.segredo_cifrado,
    ).update({FatorAdmin.ultimo_intervalo: intervalo, FatorAdmin.sessao_hash: FatorAdmin.hash_sessao(token)}, synchronize_session=False)
    db.session.commit()
    return token if atualizados else None
