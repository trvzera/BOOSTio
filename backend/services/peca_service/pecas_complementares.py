from models import Fan, Fone, Gabinete, Mouse, Teclado
from models.medidas_fisicas import completar_medidas


CADASTROS = (
    (Fan, "ARCTIC", "P12 PWM PST Black", "ACFAN00120A",
     "https://www.kabum.com.br/produto/464964/cooler-fan-arctic-p12-pwm-pst-120mm-preto-acfan00120a"),
    (Fan, "ARCTIC", "P12 PWM PST Black Pack of 5", "ACFAN00137A", None),
    (Fan, "be quiet!", "Pure Wings 3 120mm PWM", "BL105",
     "https://www.kabum.com.br/produto/727733/ventoinha-be-quiet-pure-wings-3-120mm-pwm-4-pinos-preto-bl105"),
    (Mouse, "Logitech", "M100 Black", "910-003241",
     "https://www.kabum.com.br/produto/302167/mouse-logitech-m100-usb-1000-dpi-preto-910-003241"),
    (Teclado, "Logitech", "K270 ABNT2", "920-004427",
     "https://www.kabum.com.br/produto/39391/teclado-sem-fio-logitech-k270-com-teclas-de-midia-de-facil-acesso-conexao-usb-pilhas-inclusas-e-layout-abnt2-920-004427"),
    (Fone, "Logitech", "H390 USB-A Black", "981-000014",
     "https://www.kabum.com.br/produto/95485/headset-com-fio-usb-logitech-h390-com-almofadas-controles-de-audio-integrado-e-microfone-com-reducao-de-ruido-981-000014"),
    (Gabinete, "Cooler Master", "MasterBox 520 Black", "MB520-KGNN-S01",
     "https://www.kabum.com.br/produto/502252/gabinete-gamer-cooler-master-mid-tower-argb-m-atx-atx-mini-itx-masterbox-mb520-vidro-temperado-preto-mb520-kgnn-s01"),
)


def pecas_complementares():
    dados = {}
    for classe, fabricante, modelo, part_number, link in CADASTROS:
        identidade = {"categoria": classe.__tablename__, "fabricante": fabricante,
                      "modelo": modelo, "part_number": part_number}
        ficha = completar_medidas(identidade)
        if not ficha.get("fonte_medidas"):
            raise ValueError(f"Cadastro complementar sem ficha revisada: {part_number}")
        colunas = {coluna.name for coluna in classe.__table__.columns}
        item = {campo: valor for campo, valor in ficha.items()
                if campo in colunas and valor is not None}
        item.setdefault("consumo_energia", 0)
        if classe is Gabinete:
            item.update(formato="Mid Tower", painel_vidro=True)
        item.update(preco=0, esgotado=True, preco_atualizado_em=None, kabum_external=link)
        dados.setdefault(classe, []).append(item)
    return dados
