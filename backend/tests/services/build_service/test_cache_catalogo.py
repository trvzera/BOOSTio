from flask import Flask

from services.build_service import listar_catalogo_build_service as modulo
from services.build_service.listar_catalogo_build_service import ListarCatalogoBuildService


def _app(segundos):
    app = Flask(__name__)
    app.config["CATALOGO_CACHE_SEGUNDOS"] = segundos
    return app


def test_sem_cache_monta_o_catalogo_a_cada_chamada(mocker):
    montar = mocker.patch.object(ListarCatalogoBuildService, "_montar", side_effect=[[1], [2]])
    with _app(0).app_context():
        assert ListarCatalogoBuildService().executar() == [1]
        assert ListarCatalogoBuildService().executar() == [2]
    assert montar.call_count == 2


def test_com_cache_reaproveita_ate_vencer(mocker):
    mocker.patch.dict(modulo._guardado, {"catalogo": None, "ate": 0.0})
    montar = mocker.patch.object(ListarCatalogoBuildService, "_montar", side_effect=[[1], [2]])
    mocker.patch.object(modulo.time, "monotonic", side_effect=[100.0, 130.0, 161.0, 161.0])
    with _app(60).app_context():
        assert ListarCatalogoBuildService().executar() == [1]
        assert ListarCatalogoBuildService().executar() == [1]
        assert ListarCatalogoBuildService().executar() == [2]
    assert montar.call_count == 2
