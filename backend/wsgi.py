"""Entrada de produção: gunicorn -c gunicorn.conf.py wsgi:app."""
from app import app, ambiente

if ambiente != "producao":
    raise RuntimeError("Defina APP_ENV=producao antes de iniciar o servidor de produção")

app.config.update(DEBUG=False, TESTING=False)
