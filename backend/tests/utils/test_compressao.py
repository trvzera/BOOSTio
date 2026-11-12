import gzip
import json

from flask import Flask, jsonify

from utils.compressao import configurar_compressao


def criar_app():
    app = Flask(__name__)
    configurar_compressao(app)

    @app.get("/grande")
    def grande():
        return jsonify({"itens": ["x" * 50] * 100})

    @app.get("/pequena")
    def pequena():
        return jsonify({"ok": True})

    @app.get("/texto")
    def texto():
        return "a" * 5000

    return app


def test_json_grande_vai_compactado_quando_o_navegador_aceita():
    r = criar_app().test_client().get("/grande", headers={"Accept-Encoding": "gzip, br"})
    assert r.headers["Content-Encoding"] == "gzip" and "Accept-Encoding" in r.headers["Vary"]
    assert int(r.headers["Content-Length"]) == len(r.data)
    assert json.loads(gzip.decompress(r.data))["itens"][0] == "x" * 50


def test_sem_aceitar_gzip_json_pequeno_ou_nao_json_nao_mudam():
    cliente = criar_app().test_client()
    assert "Content-Encoding" not in cliente.get("/grande").headers
    assert "Content-Encoding" not in cliente.get("/pequena", headers={"Accept-Encoding": "gzip"}).headers
    assert "Content-Encoding" not in cliente.get("/texto", headers={"Accept-Encoding": "gzip"}).headers
