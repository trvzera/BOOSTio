from services.build_service.prompt_build_service import criar_prompt_correcao
import json

import pytest

from services.build_service.criar_build_service import CriarBuildService


@pytest.mark.parametrize('mensagem,codigo', [
    ('A IA não completou as peças obrigatórias da build: placa_video.', 'pecas-obrigatorias'),
    ('A configuração sugerida contém incompatibilidades: Padrão DDR.', 'compatibilidade'),
    ('A configuração sugerida não atende ao armazenamento mínimo: solicitado 1000 GB, selecionado 120 GB.', 'armazenamento'),
    ('A configuração sugerida ultrapassou o limite destinado ao PC.', 'orcamento'),
])
def test_prompt_correcao_preserva_pedido_e_informa_erro_custos_e_limites(mensagem, codigo):
    build = {'componentes': [{'tipo': 'ssd', 'id': 1, 'quantidade': 2}]}
    catalogo = {'ssd': [{'id': 1, 'preco': 200, 'capacidade_gb': 120}]}
    original = 'Pedido original: jogos, sem trocar peças próprias.'
    prompt = criar_prompt_correcao(original, ValueError(mensagem), build, build,
                                                     catalogo, 8000, 20, 1000)
    assert prompt.startswith(original)
    dados = json.loads(prompt.splitlines()[-1])
    assert dados['codigo_falha'] == codigo
    assert dados['falha_detectada_pelo_servidor'] == mensagem
    assert dados['custos_calculados_pelo_servidor']['pc'] == 400
    assert dados['limites_obrigatorios'] == dict(orcamento_total=8000, teto_pc=6400,
                                                teto_perifericos=1600, armazenamento_minimo_gb=1000)
    assert json.loads(dados['resposta_anterior_nao_confiavel']) == build
    assert 'NOVO JSON COMPLETO' in prompt


def test_resposta_grande_nao_trunca_estrutura_json_do_diagnostico():
    prompt = criar_prompt_correcao('Pedido', ValueError('JSON inválido'),
                                                     'x' * 30000, None, {}, 8000)
    dados = json.loads(prompt.splitlines()[-1])
    assert dados['resposta_anterior_truncada'] is True
    assert len(dados['resposta_anterior_nao_confiavel']) == 16000
    assert dados['falha_detectada_pelo_servidor'] == 'JSON inválido'
    assert dados['limites_obrigatorios']['orcamento_total'] == 8000
