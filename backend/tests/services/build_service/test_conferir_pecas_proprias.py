import pytest
from flask import Flask

from models import db, PlacaVideo, Processador
from services.build_service.conferir_pecas_proprias_service import ConferirPecasPropriasService
from services.build_service.criar_build_service import CriarBuildService
from services.build_service.planejamento_geracao import ErroPlanejamentoBuild


@pytest.fixture
def banco(tmp_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{tmp_path / 'proprias.db'}"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.add_all([
            PlacaVideo(status_validacao='aprovado', fabricante='NVIDIA', modelo='GeForce RTX 4060 8GB', memoria_gb=8, consumo_energia=115),
            PlacaVideo(status_validacao='aprovado', fabricante='NVIDIA', modelo='GeForce RTX 4060 Ti 8GB', memoria_gb=8, consumo_energia=160),
            Processador(status_validacao='aprovado', fabricante='AMD', modelo='Ryzen 5 5600', soquete='AM4', nucleo=6, thread=12,
                        clockbase=3.5, clockmax=4.4, consumo_energia=65)])
        db.session.commit()
        yield
        db.session.remove()
        db.engine.dispose()


def test_modelo_exato_e_reconhecido(banco):
    ConferirPecasPropriasService.executar({'placa_video': 'NVIDIA GeForce RTX 4060 8GB', 'processador': 'ryzen 5 5600'})


def test_modelo_digitado_pela_metade_avisa_antes_da_ia_e_sugere_parecidos(banco):
    with pytest.raises(ErroPlanejamentoBuild) as erro:
        ConferirPecasPropriasService.executar({'placa_video': 'RTX 4060'})
    assert 'a placa de vídeo "RTX 4060"' in str(erro.value)
    assert 'GeForce RTX 4060 8GB' in str(erro.value) and 'RTX 4060 Ti' in str(erro.value)
    assert erro.value.geracao['etapa'] == 'pecas' and erro.value.geracao['motivo'] == 'pecas'
    assert ' IA ' not in str(erro.value) and 'resposta' not in str(erro.value)


def test_peca_desconhecida_sem_parecidas_ainda_explica_o_que_fazer(banco):
    with pytest.raises(ErroPlanejamentoBuild, match='deixe a BOOSTio escolher'):
        ConferirPecasPropriasService.executar({'processador': 'Intel Core Ultra 9 999'})


def test_pecas_que_nao_entram_no_consumo_nao_sao_exigidas(banco):
    ConferirPecasPropriasService.executar({'monitor': 'LG UltraGear 24GN60R-B', 'teclado': 'Meu teclado'})


def test_geracao_nao_chama_a_ia_quando_a_peca_propria_nao_e_reconhecida(banco, mocker):
    from models import Usuario
    db.session.add(Usuario(nome='A', email='a@example.test', verificado=True))
    db.session.commit()
    llm = mocker.patch('services.build_service.gerar_candidata_service.LLMService.executar')
    pedido = dict(nome='PC', descricao='Jogos', utilidade='Jogos', orcamento=6000,
                  pecas_proprias={'placa_video': 'RTX 4060', 'monitor': 'LG UltraGear 24GN60R-B'})
    with pytest.raises(ErroPlanejamentoBuild, match='Não reconhecemos'):
        CriarBuildService().executar(1, pedido)
    llm.assert_not_called()
