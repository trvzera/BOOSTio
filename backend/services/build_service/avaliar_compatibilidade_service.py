import math
import re

from models.build_salva import MODELOS
from .encaixe_fisico import avaliar_medidas


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
    """Diagnóstico parcial, sem gravar dados, impedir rascunhos ou inferir medidas pelo nome."""

    def executar(self, estado, catalogo=None):
        componentes = estado.get("componentes", {})
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

        regras = []
        def registrar(codigo, titulo, condicao, motivo):
            status = "nao_verificado" if condicao is None else "sem_conflitos" if condicao else "incompativel"
            mensagem = "Conflito confirmado: " + titulo + ". " + motivo if condicao is False else motivo
            regras.append({"codigo": codigo, "titulo": titulo, "status": status, "mensagem": mensagem,
                           "fonte": "catalogo_da_conta"})

        def tem(tipo):
            return tipo in componentes

        def get(tipo):
            return next((peca for categoria, _, peca in itens if categoria == tipo), None) or {}

        for indice, (tipo, item, peca) in enumerate(itens):
            if peca is None:
                registrar(f"identificacao-{tipo}-{indice}", "Identificação da peça", None,
                          f"{tipo}: peça própria ou modelo sem identificação no catálogo; suas especificações não foram verificadas.")

        faltam = [tipo for tipo in ("processador", "placa_mae", "memoria_ram", "fonte", "gabinete") if not tem(tipo)]
        if not tem("ssd") and not tem("hd"):
            faltam.append("armazenamento")
        cpu, placa, gabinete, fonte = (get(tipo) for tipo in ("processador", "placa_mae", "gabinete", "fonte"))
        if tem("processador") and cpu.get("videointegrado") is False and not tem("placa_video"):
            faltam.append("placa_video")
        if tem("processador") and cpu.get("cooler") is False and not tem("air_cooler") and not tem("water_cooler"):
            faltam.append("cooler")

        if tem("processador") and tem("placa_mae"):
            socket_cpu, socket_placa = texto(cpu.get("soquete")), texto(placa.get("socket"))
            registrar("socket", "Socket do processador e da placa-mãe",
                      socket_cpu == socket_placa if socket_cpu and socket_placa else None,
                      "Compare os sockets cadastrados. Socket ausente não equivale a compatibilidade confirmada.")
            registrar("suporte-cpu-bios", "Suporte ao modelo da CPU e BIOS", None,
                      "Socket igual não confirma a lista de CPUs suportadas nem a versão necessária de BIOS; esses dados ainda precisam ser verificados.")

        rams = [(item, peca) for tipo, item, peca in itens if tipo == "memoria_ram"]
        if rams and tem("placa_mae"):
            padrao = texto(placa.get("tipo_memoria"))
            ddrs = [texto((peca or {}).get("ddr")) for _, peca in rams]
            registrar("ram-ddr", "Padrão DDR", all(ddr == padrao for ddr in ddrs) if padrao and all(ddrs) else None,
                      "A RAM deve usar o padrão DDR suportado pela placa-mãe.")
            pentes = [numero((p or {}).get("quantidade_pentes")) for _, p in rams]
            capacidades = [numero((p or {}).get("capacidade_gb")) for _, p in rams]
            slots, maximo = numero(placa.get("quantidade_slots_ram")), numero(placa.get("memoria_maxima_gb"))
            usados = sum(item.get("quantidade", 1) * pente for (item, _), pente in zip(rams, pentes)) if all(p is not None for p in pentes) else None
            capacidade = sum(item.get("quantidade", 1) * gb for (item, _), gb in zip(rams, capacidades)) if all(gb is not None for gb in capacidades) else None
            registrar("ram-slots", "Quantidade de pentes", usados <= slots if usados is not None and slots is not None else None,
                      "Conta pentes por kit × quantidade; falta de quantidade de slots não significa slots ilimitados.")
            registrar("ram-capacidade", "Capacidade de RAM", capacidade <= maximo if capacidade is not None and maximo is not None else None,
                      "Compara a capacidade cadastrada por produto × quantidade com o limite da placa-mãe.")
            registrar("ram-perfis", "Perfis e estabilidade da RAM", None,
                      "DDR, slots e capacidade não garantem estabilidade de kits misturados ou suporte a XMP/EXPO; conferir especificações e QVL quando disponível.")

        if tem("placa_mae") and tem("gabinete"):
            formatos, formato = lista(gabinete.get("formatos_placa_mae")), texto(placa.get("formato"))
            aliases = {"MICROATX": "MATX", "MICRO-ATX": "MATX", "M-ATX": "MATX", "MINIITX": "ITX", "MINI-ITX": "ITX"}
            formato = aliases.get(formato, formato)
            formatos = [aliases.get(f, f) for f in formatos] if formatos else None
            registrar("formato-placa", "Formato da placa-mãe", formato in formatos if formato and formatos else None,
                      "Usa os formatos declarados no catálogo, sem inferir suporte pelo tamanho externo do gabinete.")

        fans = avaliar_medidas(itens, registrar, estado.get("substituirFansWaterCooler") is True)

        if tem("processador"):
            for tipo in ("air_cooler", "water_cooler"):
                if tem(tipo):
                    sockets = [texto(s) for s in re.findall(r"LGA\s*\d+|AM\d+|FM\d+|STR\d+|TR\d+", get(tipo).get("compatibilidade") or "", flags=re.I)]
                    socket = texto(cpu.get("soquete"))
                    conhecidos = bool(sockets)
                    registrar(tipo + "-socket", "Socket do cooler", socket in sockets if socket and conhecidos else None,
                              "A lista deve identificar sockets, não apenas a marca AMD/Intel.")
        if tem("air_cooler") and tem("water_cooler"):
            registrar("cooler-unico", "Cooler do processador", False, "Há air cooler e water cooler selecionados para o mesmo processador.")

        if tem("placa_mae"):
            discos = [(tipo, item, peca) for tipo, item, peca in itens if tipo in ("ssd", "hd")]
            m2 = sata = 0
            interfaces_conhecidas = True
            for _, item, peca in discos:
                interface = texto((peca or {}).get("interface") or (peca or {}).get("tipo"))
                formato = texto((peca or {}).get("formato")) or ""
                if interface and any(v in interface + formato for v in ("NVME", "PCIE", "M.2", "M2")):
                    m2 += item.get("quantidade", 1)
                    if "SATA" in interface:
                        registrar("m2-sata", "M.2 SATA", None, "É necessário confirmar quais slots M.2 aceitam SATA e quais portas são compartilhadas.")
                elif interface and "SATA" in interface:
                    sata += item.get("quantidade", 1)
                else:
                    interfaces_conhecidas = False
            if discos:
                registrar("discos-interface", "Identificação dos discos", True if interfaces_conhecidas else None,
                          "Interface desconhecida não é tratada como NVMe nem SATA automaticamente.")
            for usados, campo, codigo in ((m2, "quantidade_slots_m2", "m2"), (sata, "quantidade_portas_sata", "sata")):
                if usados:
                    limite = numero(placa.get(campo))
                    registrar("discos-" + codigo, "Conexões " + codigo.upper(), usados <= limite if limite is not None else None,
                              f"Compara as unidades com {campo}; campo ausente não representa conexões livres.")
            if discos:
                registrar("discos-compartilhamento", "Compartilhamento de conexões e baias", None,
                          "Falta confirmar desativação de portas, padrões/comprimentos M.2 e baias necessárias no gabinete.")

        if tem("fonte"):
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
            registrar("fonte-potencia", "Consumo estimado e fonte", condicao,
                      "A potência deve superar o consumo estimado cadastrado; essa soma não mede picos reais de carga.")
            registrar("fonte-conectores", "Conectores e encaixe da fonte", None,
                      "Conectores, padrão e espaço para a fonte ainda precisam de confirmação no catálogo.")

        erros = [r for r in regras if r["status"] == "incompativel"]
        desconhecidas = [r for r in regras if r["status"] == "nao_verificado"]
        status = "incompativel" if erros else "nao_verificado" if desconhecidas or faltam or not regras else "sem_conflitos"
        rotulos = {"incompativel": "Incompatibilidade identificada", "nao_verificado": "Compatibilidade não totalmente verificada",
                   "sem_conflitos": "Sem conflitos nas verificações disponíveis"}
        return {"status": status, "rotulo": rotulos[status], "escopo": "parcial", "pecasPendentes": faltam,
                "verificacoes": regras, "erros": erros, "naoVerificado": desconhecidas, "fans": fans,
                "aviso": "Peças preenchidas não significam compatibilidade completa. BIOS, conectores e interferências não são aprovados sem dados."}

    def para_resposta(self, build, incluir_links=False):
        dados = build.to_dict(incluir_links=incluir_links)
        dados["compatibilidade"] = self.executar(dados["estado"])
        return dados
