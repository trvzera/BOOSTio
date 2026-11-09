"""Pontuação explicável e independente de loja. Percentual não é probabilidade."""
import re
from heapq import nsmallest
from .produto_normalizado import ProdutoNormalizado
from .normalizar_produto import nome,codigo,gtin,variante
from .comparar_nomes_service import CompararNomesService,marca,cpu
from .conferir_especificacoes_service import ConferirEspecificacoesService,valores,converter as converter_valor
from .comparar_codigo_modelo_service import CompararCodigoModeloService


class AssociacaoInteligenteService:
    VERSAO='associacao_v8'

    @staticmethod
    def classificar_percentual(percentual):
        return 'confirmada' if percentual>80 else 'ambigua' if percentual>=60 else 'rejeitada'

    def comparar_identificadores(self,peca,produto,identidade=None):
        local=identidade or {};conflitos=[];pendencias=[];provas=[];avisos=[]
        mpn=local.get('mpn',getattr(peca,'part_number',None))
        if mpn and re.match(r'^(SEED|DEMO|BOOSTIO|REDE|KABUM)[-_]',str(mpn),re.I):mpn=None
        remotos={codigo(v) for v in valores(produto.identificadores.get('mpn')) if v}
        if len(remotos)>1:pendencias.append('mpns_multiplos')
        if mpn and remotos:
            if codigo(mpn) not in remotos:conflitos.append('mpn_divergente')
            elif len(remotos)==1:provas.append('mpn')
        gl=local.get('gtin',getattr(peca,'gtin',None));gr={gtin(v) for v in valores(produto.identificadores.get('gtin'))}
        if None in gr:avisos.append('gtin_remoto_invalido');gr.discard(None)
        if len(gr)>1:avisos.append('gtins_multiplos_sem_prova_univoca')
        if gl:
            g=gtin(gl)
            if g is None:avisos.append('gtin_local_invalido')
            elif gr and g not in gr:conflitos.append('gtin_divergente')
            elif gr=={g}:provas.append('gtin')
        return dict(conflitos=conflitos,pendencias=pendencias,evidencias=provas,mpn_local=mpn,avisos=avisos)

    def comparar_marca(self,peca,produto):
        esperada=marca(peca.fabricante)
        if produto.marca:
            return dict(pontos=10 if marca(produto.marca)==esperada else 0,
                conflitos=[] if marca(produto.marca)==esperada else ['marca_divergente'])
        encontrada=bool(esperada and re.search(r'(?<!\w)'+re.escape(esperada)+r'(?!\w)',nome(produto.titulo)))
        return dict(pontos=8 if encontrada else 0,conflitos=[],pendencias=[] if encontrada else ['marca_ausente'])

    def comparar_titulo(self,peca,produto):
        texto=nome(produto.titulo);local=nome(peca.modelo);cat=peca.__tablename__;conflitos=[]
        if re.search(r'\b(combo|upgrade|sucata|defeito)\b|somente (?:a )?(?:caixa|embalagem)',texto):conflitos.append('produto_composto_ou_inadequado')
        if cat not in ('cabo_rede', 'adaptador_wifi') and re.search(r'^(?:kit\s+de\s+)?(?:cabo|suporte|almofadas?|earpads?|case|estojo|carcaca|pelicula|adaptador)\s+(?:para|de reposicao)', texto):
            conflitos.append('acessorio_para_outro_produto')
        if cat in ('processador', 'placa_video', 'memoria_ram') and re.search(
                r'^(?:cooler|dissipador|ventoinha|water\s*cooler|bloco|pasta\s*termica)\b.*\bpara\b', texto):
            conflitos.append('acessorio_para_outro_produto')
        if cat in ('ssd', 'hd') and re.search(r'(?:\+|\bcom\b)\s*(?:um\s+)?(?:adaptador|caddy|case|gabinete)\b', texto):
            conflitos.append('produto_composto_ou_inadequado')
        if produto.contexto.get('usado'):conflitos.append('produto_usado_ou_recondicionado')
        kit=bool(re.search(r'\bkit\b|\d+\s*[x×]\s*\d+\s*gb',texto))
        if kit and cat not in ('memoria_ram', 'fan'):conflitos.append('kit_nao_suportado')
        if cat in ('processador','placa_video'):
            notebook=lambda t:bool(re.search(r'\b(notebook|laptop|mobile)\b',t))
            if notebook(texto)!=notebook(local):conflitos.append('desktop_notebook_divergentes')
            a,b=variante(cat,local),variante(cat,texto)
            if not b:b=variante(cat,produto.modelo or '')
            if not b and cat=='processador' and re.fullmatch(r'\d{3,5}(?:x3d|[a-z]{1,3})?',nome(produto.modelo or '')):b=nome(produto.modelo)
            if a and b and a!=b:conflitos.append('modelo_ou_sufixo_divergente')
            if cat=='processador' and cpu(local) and cpu(texto) and cpu(local)!=cpu(texto):conflitos.append('familia_processador_divergente')
        if cat in ('placa_mae','fonte'):
            padrao=r'\b[abxhzwq]\d{3}[a-z0-9]*(?:-[a-z0-9+]+)*\b' if cat=='placa_mae' else r'\b[a-z]{1,5}-?\d{3,4}[a-z0-9]{0,4}\b'
            lm=set(re.findall(padrao,local));rm=set(re.findall(padrao,texto))
            if lm and rm and not lm & rm:conflitos.append('modelo_no_titulo_divergente')
        if cat=='memoria_ram':
            formato=' '.join(str(v) for v in valores(produto.especificacoes.get('formato_ram')))
            formato_local = converter_valor('formato_ram', getattr(peca, 'formato', None))
            if re.search(r'so.?dimm|notebook|laptop',formato) and not (formato_local == 'sodimm' or re.search(r'so.?dimm|notebook|laptop',local)):
                return dict(conflitos=conflitos,pendencias=['formato_notebook_nao_comprovado_localmente'])
            if re.search(r'so.?dimm|notebook|laptop',local) and formato=='dimm':conflitos.append('formato_desktop_divergente')
        return dict(conflitos=conflitos,pendencias=[])

    def comparar_nome_modelo(self,peca,produto):
        resultado = CompararNomesService().executar(peca,produto)
        if not resultado['exato']:
            comum = CompararCodigoModeloService().executar(peca,produto)
            if comum:
                resultado.update(exato=True, pontos=35, codigo_modelo=comum)
        return resultado

    def comparar_especificacoes(self,peca,produto):
        return ConferirEspecificacoesService().executar(peca,produto)

    def avaliar(self,peca,produto,*,identidade=None):
        if not isinstance(produto,ProdutoNormalizado):raise ValueError('Use um ProdutoNormalizado; o núcleo não interpreta respostas de lojas')
        identificadores=self.comparar_identificadores(peca,produto,identidade)
        m=self.comparar_marca(peca,produto);n=self.comparar_nome_modelo(peca,produto)
        titulo=self.comparar_titulo(peca,produto);e=self.comparar_especificacoes(peca,produto)
        conflitos=identificadores['conflitos']+m['conflitos']+titulo['conflitos']+e['conflitos']
        pendencias=identificadores['pendencias']+m.get('pendencias',[])+titulo['pendencias']
        armazenamento = CompararCodigoModeloService.variantes_armazenamento(peca,produto)
        conflitos.extend(armazenamento['conflitos'])
        pendencias.extend(armazenamento['pendencias'])
        if produto.categoria and produto.categoria!=peca.__tablename__:conflitos.append('categoria_incompativel')
        if produto.contexto.get('dominio_divergente'):conflitos.append('categoria_incompativel')
        if not produto.categoria_confirmada:pendencias.append('categoria_nao_comprovada')
        if produto.ativo is not True:pendencias.append('estado_ativo_nao_comprovado')
        if not produto.id_externo:pendencias.append('identificacao_externa_invalida')
        if not produto.titulo:pendencias.append('nome_ausente')
        if produto.contexto.get('marcas_multiplas'):pendencias.append('marcas_multiplas')
        if produto.contexto.get('variantes_nao_resolvidas'):pendencias.append('variantes_nao_resolvidas')
        if peca.__tablename__ in ('ssd','hd'):
            tipos={{'hdd':'hd'}.get(nome(str(v)),nome(str(v))) for v in valores(produto.especificacoes.get('tecnologia_armazenamento'))}
            if tipos and tipos!={peca.__tablename__}:conflitos.append('tipo_armazenamento_divergente')
        mpn=identificadores['mpn_local']
        if getattr(peca,'cooler',None) is True and any(str(v).upper().endswith('WOF') for v in valores(produto.identificadores.get('mpn'))):
            conflitos.append('inclusao_cooler_divergente')
        if getattr(peca,'iluminacao',None) is False and re.search(r'\b(?:a?rgb)\b',nome(produto.titulo)):
            conflitos.append('iluminacao_no_titulo_divergente')
        if getattr(peca,'cooler',None) is True and re.search(r'\b(oem|tray|wof)\b',nome(produto.titulo)):
            conflitos.append('inclusao_cooler_divergente')
        if mpn and str(mpn).upper().endswith('BOX') and (re.search(r'\b(oem|tray)\b',nome(produto.titulo)) or produto.contexto.get('oem')):
            conflitos.append('embalagem_box_oem_divergente')
        provas=list(identificadores['evidencias'])
        versoes = lambda texto: set(re.findall(r'\bv[1-9]\b|\brev\.?\s*[0-9.]+', nome(texto)))
        versao_local = versoes(peca.modelo)
        versao_remota = versoes(' '.join([produto.titulo, produto.modelo or '']))
        if versao_local and versao_remota and versao_local != versao_remota:
            conflitos.append('revisao_divergente')
        codigo_fabricante = getattr(peca, 'codigo_modelo_fabricante', None)
        comprovacao = (getattr(peca, 'fontes_especificacoes', None) or {}).get('codigo_modelo_fabricante', {})
        titulo_origem = ''
        codigos_remotos = [produto.modelo or '', *produto.modelos_alternativos, *valores(produto.identificadores.get('mpn'))]
        codigo_no_titulo = bool(codigo_fabricante and re.search(r'(?<![a-z0-9/_.-])' + re.escape(codigo(codigo_fabricante)) + r'(?![a-z0-9/_.-])', nome(produto.titulo)))
        if codigo_fabricante and (codigo_no_titulo or any(codigo(codigo_fabricante) == codigo(v) for v in codigos_remotos)):
            from utils.identidade_peca import assinatura_peca
            from models.medidas_fisicas import produto_kabum
            origem_local = produto_kabum(getattr(peca, 'kabum_external', None))
            if (comprovacao.get('criterio') == 'anuncio_original_e_especificacoes_compativeis'
                    and comprovacao.get('valor') == codigo_fabricante
                    and comprovacao.get('assinatura_peca') == assinatura_peca(peca)
                    and origem_local and produto_kabum(comprovacao.get('url')) == origem_local
                    and isinstance(comprovacao.get('titulo_origem'), str) and comprovacao['titulo_origem'].strip()
                    and re.fullmatch(r'[a-f0-9]{64}', comprovacao.get('sha256_especificacoes', ''))):
                provas.append('codigo_fabricante')
                titulo_origem = comprovacao.get('titulo_origem', '')
        rgb_remoto = {converter_valor('iluminacao', v) for v in valores(produto.especificacoes.get('rgb'))}
        if True in rgb_remoto and False in rgb_remoto:
            pendencias.append('rgb_nao_comprovado')
        if rgb_remoto == {False} and re.search(r'\ba?rgb\b', nome(peca.modelo)):
            conflitos.append('rgb_divergente')
        cores = {'preto':'preto','black':'preto','branco':'branco','white':'branco',
                 'rosa':'rosa','pink':'rosa','vermelho':'vermelho','red':'vermelho','azul':'azul','blue':'azul'}
        def extrair_cores(texto):
            texto = re.sub(r'\b(?:switch|outemu|gateron|cherry(?: mx)?|gx)\s+(?:red|blue|brown|black|white)\b', '', nome(texto))
            return {cores[v] for v in re.findall(r'\b(?:'+ '|'.join(cores) + r')\b', texto)}
        nome_local_completo = ' '.join([peca.modelo, titulo_origem])
        cores_locais = extrair_cores(nome_local_completo) if peca.__tablename__ not in ('ssd','hd','processador') else set()
        cores_remotas = extrair_cores(' '.join(valores(produto.especificacoes.get('cor')))) or extrair_cores(produto.titulo)
        if cores_locais and cores_remotas and not cores_locais <= cores_remotas:
            conflitos.append('cor_divergente')
        if not (set(provas) & {'mpn','gtin'}):
            if cores_locais and not cores_remotas:
                pendencias.append('cor_nao_comprovada')
            local=nome(nome_local_completo);remoto=nome(' '.join([produto.titulo,produto.modelo or '',*produto.modelos_alternativos]))
            if any(converter_valor('iluminacao', v) is True for v in valores(produto.especificacoes.get('rgb'))):remoto += ' rgb'
            for flag,padrao in (('wifi',r'\bwi.?fi\b'),('rgb',r'\b(?:a?rgb)\b'),('oc',r'\boc\b'),('2048sp',r'\b2048\s*sp\b'),('airflow',r'\bairflow\b'),('mesh',r'\bmesh\b')):
                if bool(re.search(padrao,local))!=bool(re.search(padrao,remoto)):
                    pendencias.append('variante_nao_comprovada:'+flag)
            versao=lambda t:set(re.findall(r'\bv[1-9]\b|\brev\.?\s*[0-9.]+|\b20(?:1|2)[0-9]\b',t))
            if versao(local)!=versao(remoto):pendencias.append('versao_nao_comprovada')
        pontos=round(m['pontos']+n['pontos']+n['titulo']+e['pontos'],2)
        if provas:pontos=max(95,pontos)
        elif not n['exato'] or not e['completa']:
            pontos=min(pontos,80)
            if not n['exato']:pendencias.append('modelo_exato_nao_comprovado')
            pendencias.extend('especificacao_essencial_ausente:'+c for c in e['ausentes'])
        else:provas.append('modelo_especificacoes')
        if 'codigo_fabricante' in provas and not (set(provas) & {'mpn','gtin'}) and peca.__tablename__ in ('memoria_ram','fan'):
            quantidade = 'quantidade_pentes' if peca.__tablename__ == 'memoria_ram' else 'quantidade'
            if quantidade in e['ausentes']:
                pendencias.append('quantidade_nao_comprovada')
        if pendencias:pontos=min(pontos,80)
        if conflitos:pontos=0
        classificacao=self.classificar_percentual(pontos)
        criterio=next((c for c in ('mpn','gtin','codigo_fabricante','modelo_especificacoes') if c in provas),None)
        codigos_identidade = {codigo(v) for v in (mpn, codigo_fabricante) if v}
        codigo_conclusivo = n.get('codigo_modelo') and codigo(n['codigo_modelo']) in codigos_identidade
        return dict(classificacao=classificacao,percentual=pontos,criterio=criterio,versao=self.VERSAO,
            codigo_modelo=n.get('codigo_modelo'),
            identidade_modelo_conflitante=bool(conflitos and m['pontos'] > 0 and (
                codigo_conclusivo or peca.__tablename__ == 'processador' and n['exato'] and cpu(peca.modelo))),
            avisos=identificadores['avisos'],
            conflitos=sorted(set(conflitos)),pendencias=sorted(set(pendencias)),evidencias=sorted(provas),
            parcelas=dict(marca=m['pontos'],modelo=n['pontos'],titulo=n['titulo'],especificacoes=e['pontos'],identificador_conclusivo=bool(identificadores['evidencias'])),
            especificacoes_conferidas=e['conferidos'])

    def selecionar(self,pecas,produto,*,identidades=None,completo=True):
        identidades = identidades or {}
        total = 0
        conflito_identidade = False

        def avaliar_candidatos():
            nonlocal total, conflito_identidade
            for peca in pecas:
                resultado = self.avaliar(peca, produto, identidade=identidades.get(peca.id))
                total += 1
                if (resultado.get('identidade_modelo_conflitante') or resultado['conflitos']
                        and {'mpn', 'gtin', 'codigo_fabricante'}.intersection(resultado['evidencias'])):
                    conflito_identidade = True
                yield dict(peca=f'{peca.__tablename__}:{peca.id}', **resultado)

        ordenados = nsmallest(10, avaliar_candidatos(), key=lambda r: (-r['percentual'], r['peca']))
        melhor = ordenados[0] if ordenados else None
        percentual = melhor['percentual'] if melhor else 0
        segundo = ordenados[1]['percentual'] if len(ordenados) > 1 else None
        unico = completo and not conflito_identidade and percentual > 80 and (
            segundo is None or segundo <= 80 and percentual - segundo >= 10)
        if not unico and (percentual > 80 or not completo or conflito_identidade):
            percentual = min(80, max(60, percentual))
        classificacao='confirmada' if unico else self.classificar_percentual(min(percentual,80))
        impedimentos = []
        if conflito_identidade:impedimentos.append('identidade_existente_com_dados_contraditorios')
        if not completo:impedimentos.append('busca_incompleta')
        if segundo is not None and melhor['percentual'] > 80 and (segundo > 80 or melhor['percentual'] - segundo < 10):
            impedimentos.append('candidatos_sem_margem_suficiente')
        return dict(classificacao=classificacao,percentual=percentual,criterio=melhor['criterio'] if unico else None,
            impedimentos=impedimentos,
            peca=melhor['peca'] if unico else None,busca_completa=completo,candidatos=ordenados[:10],total_candidatos_avaliados=total,candidatos_omitidos=max(0,total-10),
            motivo='Correspondência única acima de 80' if unico else 'Avaliar candidatos' if classificacao=='ambigua' else 'Sem correspondência; avaliar cadastro ou enriquecimento')
