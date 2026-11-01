import math
import re

from models.build_salva import MODELOS
from utils.sockets import normalizar_socket, suporte_socket_cooler
from .encaixe_fisico import avaliar_medidas
from .armazenamento import avaliar_armazenamento
from .conectores import avaliar_conectores
from .preferencias_gabinete_service import PreferenciasGabineteService


def numero(valor):
    if valor is None or isinstance(valor, bool) or valor == "":
        return None
    try:
        valor = float(valor)
        return valor if math.isfinite(valor) and valor >= 0 else None
    except (ValueError, TypeError):
        return None


def texto(valor):
    if not isinstance(valor, str) or valor.strip().casefold() in ("", "n/a", "não informado", "desconhecido"):
        return None
    return re.sub(r"\s+", "", valor).upper()


def lista(valor):
    if isinstance(valor, str):
        valor = re.split(r"[,;/]", valor)
    return [texto(item) for item in valor if texto(item)] if isinstance(valor, (list, tuple)) else None


class AvaliarCompatibilidadeService:
    def executar(self, estado, catalogo=None):
        if not isinstance(estado, dict):
            raise ValueError("Informe estado como um objeto válido")

        componentes = estado.get("componentes", {})
        itens = self._identificar_pecas(componentes, catalogo)

        regras, orientacoes = [], PreferenciasGabineteService.orientacoes(estado, itens)
        self._orientar_rede(estado, componentes, orientacoes)

        def _registrar(codigo, titulo, condicao, motivo, fonte="catalogo_da_conta"):
            status = "nao_verificado" if condicao is None else "sem_conflitos" if condicao else "incompativel"
            mensagem = "Conflito confirmado: " + titulo + ". " + motivo if condicao is False else motivo
            regras.append({"codigo": codigo, "titulo": titulo, "status": status, "mensagem": mensagem,
                           "fonte": fonte})

        def _possui_peca(tipo):
            return tipo in componentes

        def _buscar_peca(tipo):
            return next((peca for categoria, _, peca in itens if categoria == tipo), None) or {}

        for indice, (tipo, item, peca) in enumerate(itens):
            if peca is None:
                _registrar(f"identificacao-{tipo}-{indice}", "Identificação da peça", None,
                          f"{tipo}: peça própria ou modelo sem identificação no catálogo; suas especificações não foram verificadas.")

        faltam = [tipo for tipo in ("processador", "placa_mae", "memoria_ram", "fonte", "gabinete") if not _possui_peca(tipo)]
        if not _possui_peca("ssd") and not _possui_peca("hd"):
            faltam.append("armazenamento")
        cpu, placa, gabinete, fonte = (_buscar_peca(tipo) for tipo in ("processador", "placa_mae", "gabinete", "fonte"))
        if gabinete.get("observacoes_medidas"):
            orientacoes.append({"codigo": "gabinete-condicoes", "titulo": "Condições da ficha do gabinete",
                               "mensagem": gabinete["observacoes_medidas"], "fonte": "catalogo_da_conta"})
        if _possui_peca("processador") and cpu.get("videointegrado") is False and not _possui_peca("placa_video"):
            faltam.append("placa_video")
        if _possui_peca("processador") and cpu.get("cooler") is False and not _possui_peca("air_cooler") and not _possui_peca("water_cooler"):
            faltam.append("cooler")

        self._avaliar_processador(_possui_peca, cpu, placa, _registrar)

        self._avaliar_memoria(itens, _possui_peca, placa, _registrar)

        self._avaliar_formato(_possui_peca, gabinete, placa, _registrar)

        fans = avaliar_medidas(itens, _registrar, estado.get("substituirFansWaterCooler") is True)

        self._avaliar_cooler(_possui_peca, _buscar_peca, cpu, _registrar)

        if _possui_peca("placa_mae"):
            discos = [(item, peca) for tipo, item, peca in itens if tipo in ("ssd", "hd")]
            if discos:
                for r in avaliar_armazenamento(placa, discos):
                    _registrar(r['codigo'], r['titulo'], r['condicao'], r['mensagem'])

        self._avaliar_fonte(_possui_peca, itens, fonte, _registrar)

        return self._montar_resultado(regras, faltam, orientacoes, fans)

    def para_resposta(self, build, incluir_links=False):
        dados = build.to_dict(incluir_links=incluir_links)
        dados["compatibilidade"] = self.executar(dados["estado"])
        return dados

    @staticmethod
    def _identificar_pecas(componentes, catalogo):
        itens = []
        for tipo, selecao in componentes.items():
            for item in selecao if isinstance(selecao, list) else [selecao]:
                peca = None
                if "id" in item:
                    identificador = str(item["id"]).split(":")[-1]
                    if catalogo is not None:
                        peca = next((p for p in catalogo if p.get("categoria") == tipo and str(p["id"]).split(":")[-1] == identificador), None)
                    elif tipo in MODELOS and identificador.isdigit():
                        modelo = MODELOS[tipo].buscar_por_id(int(identificador))
                        peca = modelo.to_catalogo() if modelo else None
                itens.append((tipo, item, peca))

        return itens

    @staticmethod
    def _orientar_rede(estado, componentes, orientacoes):
        rede = estado.get("rede") if isinstance(estado.get("rede"), dict) else {}
        acessorio_rede = {"cabo": "cabo_rede", "wifi": "adaptador_wifi"}.get(rede.get("tipo"))
        if acessorio_rede and rede.get("possuiAcessorio") is False and not componentes.get(acessorio_rede):
            descricao = "Cabo de rede" if acessorio_rede == "cabo_rede" else "Adaptador Wi-Fi"
            comprimento = numero(rede.get("comprimentoCaboM"))
            if acessorio_rede == "cabo_rede" and comprimento:
                descricao += f" de pelo menos {comprimento:g} m"
            orientacoes.append({"codigo": "rede-pendente", "mensagem": descricao +
                " pendente: não foi incluído na build nem no total. Adicione um modelo adequado ou compre separadamente; confira a velocidade e as conexões antes de comprar."})

    @staticmethod
    def _avaliar_processador(_possui_peca, cpu, placa, _registrar):
        if _possui_peca("processador") and _possui_peca("placa_mae"):
            socket_cpu, socket_placa = normalizar_socket(cpu.get("soquete")), normalizar_socket(placa.get("socket"))
            _registrar("socket", "Socket do processador e da placa-mãe",
                      socket_cpu == socket_placa if socket_cpu and socket_placa else None,
                      f"Encaixe do processador: {socket_cpu or 'não informado'}; placa-mãe: {socket_placa or 'não informado'}. "
                      "O mesmo encaixe não confirma suporte ao modelo nem a BIOS instalada.")
            _registrar("suporte-cpu-bios", "Suporte ao modelo da CPU e BIOS", None,
                      "Socket igual não confirma a lista de CPUs suportadas nem a versão necessária de BIOS; esses dados ainda precisam ser verificados.")


    @staticmethod
    def _avaliar_memoria(itens, _possui_peca, placa, _registrar):
        rams = [(item, peca) for tipo, item, peca in itens if tipo == "memoria_ram"]
        if rams and _possui_peca("placa_mae"):
            padrao = texto(placa.get("tipo_memoria"))
            ddrs = [texto((peca or {}).get("ddr")) for _, peca in rams]
            _registrar("ram-ddr", "Padrão DDR", all(ddr == padrao for ddr in ddrs) if padrao and all(ddrs) else None,
                      "A RAM deve usar o padrão DDR suportado pela placa-mãe.")
            pentes = [numero((p or {}).get("quantidade_pentes")) for _, p in rams]
            capacidades = [numero((p or {}).get("capacidade_gb")) for _, p in rams]
            slots, maximo = numero(placa.get("quantidade_slots_ram")), numero(placa.get("memoria_maxima_gb"))
            if slots is not None and not slots.is_integer():
                slots = None
            usados = sum(item.get("quantidade", 1) * pente for (item, _), pente in zip(rams, pentes)) if all(p is not None for p in pentes) else None
            capacidade = sum(item.get("quantidade", 1) * gb for (item, _), gb in zip(rams, capacidades)) if all(gb is not None for gb in capacidades) else None
            _registrar("ram-slots", "Quantidade de pentes", usados <= slots if usados is not None and slots is not None else None,
                      "Conta pentes por kit × quantidade; falta de quantidade de slots não significa slots ilimitados.")
            if slots is None:
                _registrar("ram-limite-provisorio", "Limite provisório de RAM", usados <= 2 if usados is not None else None,
                          "Slots não informados: a montagem fica limitada provisoriamente a dois pentes, contando todos os kits. "
                          "Isso não confirma os slots reais nem a capacidade máxima; confira o manual antes de comprar.",
                          fonte="politica_de_montagem")
            _registrar("ram-capacidade", "Capacidade de RAM", capacidade <= maximo if capacidade is not None and maximo is not None else None,
                      "Compara a capacidade cadastrada por produto × quantidade com o limite da placa-mãe.")
            _registrar("ram-perfis", "Perfis e estabilidade da RAM", None,
                      "DDR, slots e capacidade não garantem estabilidade de kits misturados ou suporte a XMP/EXPO; conferir especificações e QVL quando disponível.")


    @staticmethod
    def _avaliar_formato(_possui_peca, gabinete, placa, _registrar):
        if _possui_peca("placa_mae") and _possui_peca("gabinete"):
            formatos, formato = lista(gabinete.get("formatos_placa_mae")), texto(placa.get("formato"))
            aliases = {"MICROATX": "MATX", "MICRO-ATX": "MATX", "M-ATX": "MATX", "MINIITX": "ITX", "MINI-ITX": "ITX"}
            formato = aliases.get(formato, formato)
            formatos = [aliases.get(f, f) for f in formatos] if formatos else None
            _registrar("formato-placa", "Formato da placa-mãe", formato in formatos if formato and formatos else None,
                      "Usa os formatos declarados no catálogo, sem inferir suporte pelo tamanho externo do gabinete.")


    @staticmethod
    def _avaliar_cooler(_possui_peca, _buscar_peca, cpu, _registrar):
        if _possui_peca("processador"):
            for tipo in ("air_cooler", "water_cooler"):
                if _possui_peca(tipo):
                    cooler = _buscar_peca(tipo)
                    suporte = suporte_socket_cooler(cpu.get("soquete"), cooler)
                    motivo = ("Há versões ou kits de montagem diferentes deste cooler. Confirme o suporte ao socket "
                              f"{normalizar_socket(cpu.get('soquete')) or 'da CPU'} na embalagem/manual da unidade."
                              if cooler.get("sockets_suporte_condicional") and suporte is None else
                              "Confere o encaixe da CPU com a lista de sockets do cooler. Apenas AMD/Intel não identifica o suporte.")
                    _registrar(tipo + "-socket", "Socket do cooler", suporte, motivo)
        if _possui_peca("air_cooler") and _possui_peca("water_cooler"):
            _registrar("cooler-unico", "Cooler do processador", False, "Há air cooler e water cooler selecionados para o mesmo processador.")


    @staticmethod
    def _avaliar_fonte(_possui_peca, itens, fonte, _registrar):
        if _possui_peca("fonte"):
            internos = [(item, peca) for tipo, item, peca in itens if tipo not in ("fonte", "monitor", "teclado", "mouse", "fone", "cabo_rede", "adaptador_wifi")]
            consumos = [numero((p or {}).get("consumo_energia")) for _, p in internos]
            potencia = numero(fonte.get("potencia_w")) or None
            minimo_conhecido = sum((consumo or 0) * item.get("quantidade", 1)
                                  for (item, _), consumo in zip(internos, consumos))
            consumo = minimo_conhecido if internos and all(v is not None for v in consumos) else None
            condicao = None
            if potencia is not None:
                if minimo_conhecido > potencia:
                    condicao = False
                elif consumo is not None and consumo < potencia:
                    condicao = True
            _registrar("fonte-potencia", "Consumo estimado e fonte", condicao,
                      "A potência deve superar o consumo estimado cadastrado; essa soma não mede picos reais de carga.")
            consumidores = [(t, i, p) for t, i, p in itens if t in ('placa_mae', 'placa_video', 'ssd', 'hd')]
            condicao, mensagem = avaliar_conectores(fonte, consumidores)
            _registrar("fonte-conectores", "Conectores da placa-mãe, GPU e discos", condicao, mensagem)


    @staticmethod
    def _montar_resultado(regras, faltam, orientacoes, fans):
        erros = [r for r in regras if r["status"] == "incompativel"]
        desconhecidas = [r for r in regras if r["status"] == "nao_verificado"]
        status = "incompativel" if erros else "nao_verificado" if desconhecidas or faltam or not regras else "sem_conflitos"
        rotulos = {"incompativel": "Incompatibilidade identificada", "nao_verificado": "Compatibilidade não totalmente verificada",
                   "sem_conflitos": "Sem conflitos nas verificações disponíveis"}
        return {"status": status, "rotulo": rotulos[status], "escopo": "parcial", "pecasPendentes": faltam,
                "verificacoes": regras, "erros": erros, "naoVerificado": desconhecidas, "orientacoes": orientacoes, "fans": fans,
                "aviso": "Peças preenchidas não significam compatibilidade completa. BIOS, conectores e interferências não são aprovados sem dados."}
