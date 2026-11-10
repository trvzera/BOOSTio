"""Enriquecimento de lojas sem ficha própria, usando as mesmas bases técnicas."""
from dataclasses import asdict
from models.modelos_pecas import MODELOS_PECAS
from services.icecat_service.completar_ficha_icecat_service import CompletarFichaIcecatService
from .extrair_dados_tecnicos_service import ExtrairDadosTecnicosService
from .consultar_base_hardware_service import ConsultarBaseHardwareService
from .validar_ficha_tecnica_service import ValidarFichaTecnicaService


class EnriquecerNormalizadoService:
    def executar(self, produto):
        modelo = next(m for m in MODELOS_PECAS if m.__tablename__ == produto.categoria)
        extraidos = ExtrairDadosTecnicosService().executar(modelo, produto)
        consulta = ConsultarBaseHardwareService().executar(produto)
        produto = consulta['produto']
        dados = {**consulta['dados'], **extraidos['dados']}
        if produto.marca:
            dados['fabricante'] = produto.marca
        if produto.modelo:
            dados['modelo'] = produto.modelo
        ficha = dict(dados=dados, fontes={**consulta['fontes'], **extraidos['fontes']},
            conflitos=extraidos['conflitos'], identidade={}, produto={'id': produto.id_externo},
            pronto=False, normalizado=asdict(produto), loja=produto.loja)
        icecat = CompletarFichaIcecatService.configurado()
        if icecat:
            produto, ficha = icecat.executar(produto, ficha)
        validacao = ValidarFichaTecnicaService().executar(produto.categoria, ficha['dados'], produto,
            ficha.get('identidade'), fontes=ficha['fontes'], finalidade='catalogo')
        ficha.update(pronto=validacao['pronto'], campos_pendentes=validacao['campos_pendentes'],
                     conflitos=sorted(set(ficha['conflitos'] + validacao['conflitos'])))
        return produto, ficha
