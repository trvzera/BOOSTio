"""Planeja buscas por marcas reais do catálogo, sem acesso a APIs de lojas."""
import hashlib
import re
import unicodedata

from services.peca_service.modelos_pecas import MODELOS_PECAS


class PlanejarDescobertaService:
    TERMOS = {
        'processador': 'processador', 'placa_video': 'placa de video',
        'placa_mae': 'placa mae', 'memoria_ram': 'memoria RAM',
        'ssd': 'SSD', 'hd': 'HD', 'fonte': 'fonte PC', 'gabinete': 'gabinete PC',
        'air_cooler': 'air cooler', 'water_cooler': 'water cooler',
        'fan': 'ventoinha PC', 'mouse': 'mouse', 'teclado': 'teclado',
        'monitor': 'monitor', 'fone': 'headset',
        'adaptador_wifi': 'adaptador wifi', 'cabo_rede': 'cabo de rede',
    }

    def por_peca(self, *, categoria, limite=100, depois_id=0, resultados=10, modelos=None):
        """Pesquisa modelo/MPN completos; encontrar um anúncio não comprova associação."""
        from utils.codigos_peca import codigo_interno
        if type(limite) is not int or not 1 <= limite <= 500 or type(resultados) is not int or not 1 <= resultados <= 100:
            raise ValueError('Limites inválidos')
        if type(depois_id) is not int or depois_id < 0:
            raise ValueError('Cursor inválido')
        modelo = next((m for m in (MODELOS_PECAS if modelos is None else modelos) if m.__tablename__ == categoria), None)
        if modelo is None or categoria not in self.TERMOS:
            raise ValueError('Categoria desconhecida')
        trabalhos = []
        for peca in modelo.lote_para_identificadores(depois_id, limite):
            identidade = peca.part_number if peca.part_number and not codigo_interno(peca.part_number) else peca.modelo
            consulta = ' '.join(f'{self.TERMOS[categoria]} {peca.fabricante} {identidade}'.split())
            if not identidade or len(consulta) > 150 or any(ord(c) < 32 for c in consulta):
                raise ValueError(f'Nome ou MPN inválido para pesquisa: {categoria}:{peca.id}')
            trabalhos.append(dict(nome=f'{categoria}-peca-{peca.id}', categoria=categoria,
                consulta=consulta, origem='catalogo', marca=peca.fabricante,
                max_produtos=resultados, max_anuncios=resultados, max_ofertas_por_produto=1,
                max_paginas=20, max_requisicoes=30, intervalo=1.0, limite_fila=20, periodo_segundos=86400))
        if not trabalhos:
            raise ValueError('Nenhuma peça no lote solicitado')
        return dict(versao=1, trabalhos=trabalhos)

    def executar(self, *, limite=100, modelos=None, marcas_por_categoria=5):
        if type(limite) is not int or not 1 <= limite <= 100:
            raise ValueError('Informe entre 1 e 100 produtos por categoria/marca')
        if marcas_por_categoria is not None and (type(marcas_por_categoria) is not int or not 1 <= marcas_por_categoria <= 50):
            raise ValueError('Informe entre 1 e 50 marcas por categoria ou todas')
        trabalhos = []
        for modelo in MODELOS_PECAS if modelos is None else modelos:
            categoria = modelo.__tablename__
            termo = self.TERMOS.get(categoria)
            if termo is None:
                raise ValueError('Categoria sem termo de descoberta: ' + categoria)
            vistos = set()
            selecionadas = 0
            for fabricante in modelo.fabricantes_para_descoberta():
                marca = ' '.join(fabricante.split())
                chave = unicodedata.normalize('NFKC', marca).casefold()
                if not marca or chave in vistos or chave in {'outros', 'outro', 'importado', 'generico', 'genérico', 'sem marca', 'nao informado', 'não informado'}:
                    continue
                if marcas_por_categoria is not None and selecionadas >= marcas_por_categoria:
                    break
                vistos.add(chave)
                selecionadas += 1
                consulta = f'{termo} {marca}'
                if categoria == 'processador' and chave == 'amd':
                    consulta += ' Ryzen'
                if len(consulta) > 150 or any(ord(c) < 32 for c in consulta):
                    raise ValueError('Marca inválida para pesquisa')
                sufixo = hashlib.sha256(chave.encode()).hexdigest()[:8]
                slug = re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize(
                    'NFKD', chave).encode('ascii', 'ignore').decode()).strip('-')
                trabalhos.append({
                    'nome': f'{categoria}-{slug[:35]}-{sufixo}',
                    'categoria': categoria, 'consulta': consulta, 'origem': 'catalogo',
                    'marca': marca,
                    'max_produtos': limite, 'max_ofertas_por_produto': 1,
                    'max_anuncios': limite, 'max_paginas': 20,
                    'max_requisicoes': 30, 'intervalo': 1.0,
                    'limite_fila': 20, 'periodo_segundos': 86400,
                })
        if not trabalhos or len(trabalhos) > 1000:
            raise ValueError('O plano deve conter entre 1 e 1000 grupos')
        return {'versao': 1, 'trabalhos': trabalhos}
