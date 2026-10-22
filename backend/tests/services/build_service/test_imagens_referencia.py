import json
from pathlib import Path

from models import Processador
from models.imagens_referencia import imagem_referencia, referencias


def test_vinculo_exato_prioridade_e_sem_update_no_banco():
    numero, ficha = next((pn, f) for pn, f in referencias().items() if f["categoria"] == "processador")
    dados = {**ficha, "part_number": numero}
    assert imagem_referencia(dados) == ficha["imagem"]
    for campo in ("part_number", "categoria", "fabricante", "modelo"):
        assert imagem_referencia({**dados, campo: "outra revisão"}) is None
    peca = Processador(id=999, part_number=numero, fabricante=ficha["fabricante"], modelo=ficha["modelo"])
    assert peca.to_catalogo()["imagem"] == ficha["imagem"]
    assert peca.imagem_url is None and peca.id == 999
    peca.imagem_url = "https://cdn.example.test/imagem.webp"
    assert peca.to_catalogo()["imagem"] == peca.imagem_url


def test_referencias_correspondem_ao_catalogo_e_a_arquivos_locais():
    frontend = Path(__file__).resolve().parents[4] / "frontend"
    catalogo = {p["part_number"]: p for p in json.loads((frontend / "data/catalogo-demo.json").read_text())}
    assert len(referencias()) == 750
    for pn, ficha in referencias().items():
        assert all(catalogo[pn][campo] == ficha[campo] for campo in ("categoria", "fabricante", "modelo"))
        arquivo = (frontend / "pages" / ficha["imagem"]).resolve()
        assert arquivo.is_relative_to(frontend / "imgs/produtos") and arquivo.is_file()
