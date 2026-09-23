from urllib.parse import quote_plus

from models import (
  db,
  Processador,
  PlacaMae,
  PlacaVideo,
  MemoriaRAM,
  SSD,
  HD,
  Fonte,
  Gabinete,
  WaterCooler,
  AirCooler,
  Fan,
  Fone,
  Teclado,
  Mouse,
  Monitor,
)


def _link_busca_kabum(fabricante: str, modelo: str) -> str:
  return f"https://www.kabum.com.br/busca/{quote_plus(f'{fabricante} {modelo}')}"


#Links reais da pagina do produto na Kabum, hardcoded (levantados uma unica vez via busca offline).
#Peca sem entrada aqui cai no link de busca (_link_busca_kabum) ate alguem achar e adicionar o link certo.
LINKS_KABUM: dict[str, str] = {
  "SEED-ACOOL-01": "https://www.kabum.com.br/produto/1002623/air-cooler-cooler-master-hyper-212-3dhp-black-edition-argb-intel-e-amd-120mm-preto-may-t2hp-217pa-r1",
  "SEED-ACOOL-02": "https://www.kabum.com.br/produto/460434/air-cooler-para-processador-deepcool-ak400-bk-preto",
  "SEED-ACOOL-05": "https://www.kabum.com.br/produto/128332/cooler-fan-thermaltake-tt-ux200-aircooler-120mm-argb-cl-p065-al12sw-a",
  "SEED-ACOOL-08": "https://www.kabum.com.br/produto/244585/cooler-para-processador-redragon-tyr-led-azul-intel-e-amd-120mm-pwm-fan-4-heat-pipes-tdp-130w-cc-9104b",
  "SEED-ACOOL-10": "https://www.kabum.com.br/produto/643319/cooler-master-hyper-212-halo-street-fighter-6-ryu-amd-intel-argb-branco-rr-s4ww-20pa-ry",
  "SEED-ACOOL-25": "https://www.kabum.com.br/produto/565355/air-cooler-cougar-forza-50-essential-intel-amd-120mm-3mfze50-0001",
  "SEED-CASE-01": "https://www.kabum.com.br/produto/903460/gabinete-gamer-cooler-master-masterbox-q300l-vidro-temperado-painel-modular-micro-atx-preto",
  "SEED-CASE-02": "https://www.kabum.com.br/produto/509115/gabinete-gamer-cooler-master-masterbox-td500-mesh-v2-white-mid-tower-vidro-sem-fonte-3x-fans-argb-td500v2-wgnn-s00",
  "SEED-CASE-11": "https://www.kabum.com.br/produto/172268/gabinete-masterbox-cooler-master-nr200-mini-itx-sfx-preto-mcb-nr200-knnn-s00",
  "SEED-CASE-12": "https://www.kabum.com.br/produto/171504/gabinete-gamer-cooler-master-masterbox-mb520-argb-mid-tower-lateral-acrilico-mcb-b520-kgnn-rga",
  "SEED-CASE-23": "https://www.kabum.com.br/produto/203445/gabinete-aerocool-cylon-mid-tower-rgb-led-atx-lateral-de-acrilico-preto-63858",
  "SEED-CPU-02": "https://www.kabum.com.br/produto/320797/processador-amd-ryzen-7-5700x-3-4ghz-4-6ghz-max-turbo-cache-36mb-8-nucleos-16-threads-am4-sem-video-integrado-100-100000926wof",
  "SEED-CPU-03": "https://www.kabum.com.br/produto/422164/processador-amd-ryzen-5-7600-4-00ghz-6-core-38mb-am5",
  "SEED-CPU-04": "https://www.kabum.com.br/produto/378413/processador-amd-ryzen-7-7700x-4-5ghz-5-4ghz-max-turbo-cache-40mb-8-nucleos-16-threads-am5-com-video-integrado-100-100000591wof",
  "SEED-CPU-05": "https://www.kabum.com.br/produto/378412/processador-amd-ryzen-9-7900x-4-7ghz-5-6ghz-max-turbo-cache-76mb-12-nucleos-24-threads-am5-com-video-integrado-100-100000589wof-",
  "SEED-CPU-06": "https://www.kabum.com.br/produto/283719/processador-intel-core-i3-12100f-3-3ghz-4-3ghz-max-turbo-cache-12mb-4-nucleos-8-threads-lga-1700-sem-video-integrado-bx8071512100f",
  "SEED-CPU-07": "https://www.kabum.com.br/produto/315050/processador-intel-core-i5-12400f-2-5ghz-4-4ghz-turbo-cache-7-5mb-12-threads-hexa-core-lga-1700-bx8071512400f",
  "SEED-CPU-08": "https://www.kabum.com.br/produto/1000731/processador-intel-core-i5-13400f-4-6ghz-max-turbo-cache-20mb-10-nucleos-16-threads-lga-1700-oem",
  "SEED-CPU-09": "https://www.kabum.com.br/produto/400720/processador-intel-core-i7-13700k-lga-1700-3-4ghz-5-4ghz-max-turbo-cache-30mb-16-nucleos-24-threads-bx8071513700k",
  "SEED-CPU-10": "https://www.kabum.com.br/produto/497573/processador-intel-core-i9-14900k-3-2ghz-6ghz-max-turbo-cache-36mb-24-nucleos-32-threads-lga-1700-com-video-integrado-bx8071514900k",
  "SEED-CPU-11": "https://www.kabum.com.br/produto/357485/processador-amd-ryzen-3-4100-4-0ghz-cache-6mb-am4-wraith-stealth-sem-vi-deo-integrado-100-100000510box",
  "SEED-CPU-12": "https://www.kabum.com.br/produto/320799/processador-amd-ryzen-5-5500-3-6ghz-4-2ghz-max-turbo-cache-19mb-6-nucleos-12-threads-am4-sem-video-integrado-100-100000457box",
  "SEED-CPU-13": "https://www.kabum.com.br/produto/1053828/processador-amd-ryzen-7-5800x3d-3-4ghz-8-core-cache-100mb-am4-100-100000651pof",
  "SEED-CPU-16": "https://www.kabum.com.br/produto/426262/processador-amd-ryzen-7-7800x3d-4-2ghz-5-0ghz-max-turbo-cache-104mb-8-nucleos-16-threads-am5-com-video-integrado-100-100000910wof",
  "SEED-CPU-17": "https://www.kabum.com.br/produto/390981/processador-amd-ryzen-radeon-9-7950x-2200mhz-cache-80mb-1hexa-core-am5-video-integrado-100-100000514wof",
  "SEED-CPU-18": "https://www.kabum.com.br/produto/520366/processador-amd-ryzen-5-8500g-3-5-ghz-5-0ghz-max-turbo-cache-22mb-6-nucleos-12-threads-am5-com-video-integrado-100-100000931box",
  "SEED-CPU-19": "https://www.kabum.com.br/produto/158284/processador-intel-core-i3-10100f-3-60ghz-4-30ghz-turbo-cache-6mb-lga-1200-bx8070110100f",
  "SEED-CPU-20": "https://www.kabum.com.br/produto/162097/processador-intel-core-i5-10400f-2-9ghz-4-3ghz-turbo-hexa-core-cache-12mb-lga-1200-bx8070110400f",
  "SEED-CPU-21": "https://www.kabum.com.br/produto/1050169/processador-intel-core-i5-11400f-2-6ghz-cache-12mb-6-nucleos-12-threads-lga-1200-oem",
  "SEED-CPU-23": "https://www.kabum.com.br/produto/283717/processador-intel-core-i7-12700f-2-1ghz-4-9ghz-max-turbo-cache-25mb-12-nucleos-20-threads-lga-1700-sem-video-integrado-bx8071512700f",
  "SEED-CPU-25": "https://www.kabum.com.br/produto/421583/processador-intel-core-i3-13100f-box-lga-1700-3-4ghz-12mb-cache-s-video-bx8071513100f",
  "SEED-FAN-02": "https://www.kabum.com.br/produto/202502/cooler-fan-deepcool-rf120-120mm-rgb-led-dp-frgb-rf120-1c",
  "SEED-FAN-03": "https://www.kabum.com.br/produto/284277/cooler-fan-corsair-ll120-120mm-rgb-white-co-9050091-ww",
  "SEED-GPU-01": "https://www.kabum.com.br/produto/998335/placa-de-video-pcyes-nvidia-geforce-gtx-1660-super-gddr6-6gb-dual-192-bits-pvx1660s62f",
  "SEED-GPU-02": "https://www.kabum.com.br/produto/217261/placa-de-video-zotac-nvidia-geforce-rtx-3060-twin-edge-12gb-gddr6-zt-a30600e-10m",
  "SEED-GPU-03": "https://www.kabum.com.br/produto/1063824/placa-de-video-geforce-rtx3060-ti-8gb-gddr6-256bits-pvr30608tgr6df3",
  "SEED-GPU-04": "https://www.kabum.com.br/produto/1063823/placa-de-video-pcyes-geforce-rtx4060-8gb-gddr6-128bits-pvr40608gr6df2",
  "SEED-GPU-11": "https://www.kabum.com.br/produto/149754/placa-de-video-pcyes-nvidia-geforce-gt-1030-2gb-gddr5",
  "SEED-GPU-13": "https://www.kabum.com.br/produto/400204/placa-de-video-pcyes-gtx-1660-super-nvidia-geforce-6gb-gddr6-192bits-pa1660s6gr6df",
  "SEED-GPU-14": "https://www.kabum.com.br/produto/998334/placa-de-video-pcyes-nvidia-geforce-rtx-3050-6gb-gddr6-96bits-pvpcr30506gb2f",
  "SEED-GPU-20": "https://www.kabum.com.br/produto/1061740/placa-grafica-de-microprocessador-com-dispositivo-de-dissipacao-de-calor-full-size-vga-4gb-ddr5-rx550",
  "SEED-GPU-23": "https://www.kabum.com.br/produto/510975/placa-de-video-rx-6750-xt-mech-2x-12g-v1-radeon-12gb-gddr6-freesync-dual-fan",
  "SEED-HDD-01": "https://www.kabum.com.br/produto/533737/hd-seagate-barracuda-1tb-3-5-polegadas-7200rpm-256mb-sata-st1000dm014",
  "SEED-HDD-02": "https://www.kabum.com.br/produto/196410/hd-seagate-2tb-barracuda-3-5-sata-st2000dm008",
  "SEED-HDD-03": "https://www.kabum.com.br/produto/233137/hd-wd-blue-1tb-para-notebook-5400-rpm-2-5-sata-3-128mb-cache-wd10spzx",
  "SEED-HDD-04": "https://www.kabum.com.br/produto/1054904/hd-wd-2tb-wd-blue-3-5-sata-3-7200rpm-wd20ezbx",
  "SEED-HDD-05": "https://www.kabum.com.br/produto/618330/hd-wd-purple-4tb-3-5-5400rpm-sata-iii-6gb-s-cache-256mb-wd43purz",
  "SEED-HDD-08": "https://www.kabum.com.br/produto/173455/hd-seagate-surveillance-skyhawk-2tb-3-5-sata-st2000vx008",
  "SEED-HDD-10": "https://www.kabum.com.br/produto/196401/hd-seagate-4tb-barracuda-3-5-sata-st4000dm004",
  "SEED-HDD-11": "https://www.kabum.com.br/produto/919636/hd-interno-500gb-seagate-barracuda-pc-computador-cftv-dvr",
  "SEED-HDD-14": "https://www.kabum.com.br/produto/503869/hd-seagate-4tb-skyhawk-surveillance-3-5polegadas-sata-3-5400rpm-st4000vx016",
  "SEED-HDD-15": "https://www.kabum.com.br/produto/1062238/hd-500gb-wd-blue-wd5000aakx",
  "SEED-HDD-17": "https://www.kabum.com.br/produto/1055848/hd-wd-4tb-wd-red-plus-nas-3-5-sata-3-5400rpm-wd40efzz-garantia-br-",
  "SEED-HDD-19": "https://www.kabum.com.br/produto/472212/hd-surveillance-wd-purple-2tb-cache-64mb-3-5-sata-wd23purz",
  "SEED-HDD-22": "https://www.kabum.com.br/produto/653363/hd-3tb-7200rpm-seagate-barracuda-st3000dm001",
  "SEED-HDD-23": "https://www.kabum.com.br/produto/404177/hd-seagate-8tb-exos-7e10-7200-rpm-256mb-sata-iii-st8000nm017b",
  "SEED-HDD-24": "https://www.kabum.com.br/produto/1055090/hd-wd-1tb-wd-green-3-5-sata-3-7200rpm-pull-wd10eurx",
  "SEED-HEADSET-01": "https://www.kabum.com.br/produto/266118/headset-gamer-hyperx-cloud-stinger-conector-3-5mm-hx-hscs-bk",
  "SEED-HEADSET-02": "https://www.kabum.com.br/produto/181876/headset-gamer-logitech-g335-3-5mm-para-pc-playstation-xbox-switch-mobile-driver-40mm-arco-ajustavel-preto-981-000977",
  "SEED-HEADSET-03": "https://www.kabum.com.br/produto/921167/headset-gamer-razer-kraken-v4-x-drivers-40-mm-microfone-cardioide-rgb-preto-rz04-05180100",
  "SEED-HEADSET-04": "https://www.kabum.com.br/produto/690576/headset-gamer-corsair-hs55-surround-v2-branco-ca-9011390-ww",
  "SEED-HEADSET-05": "https://www.kabum.com.br/produto/677078/headset-gamer-jbl-quantum-100-m2-drivers-de-40mm-microfone-preto",
  "SEED-HEADSET-07": "https://www.kabum.com.br/produto/102770/headset-gamer-havit-drivers-53mm-microfone-plugavel-3-5mm-pc-ps4-xbox-one-preto-hv-h2002d",
  "SEED-HEADSET-08": "https://www.kabum.com.br/produto/727786/headset-gamer-redragon-zeus-lite-p3-drivers-53mm-pc-ps5-xbox-preto-h510-lt",
  "SEED-HEADSET-09": "https://www.kabum.com.br/produto/321163/headset-gamer-sem-fio-logitech-g435-dolby-atmos-drivers-40mm-lightspeed-e-bluetooth-usb-pc-ps4-ps5-mobile-preto-981-001049",
  "SEED-HEADSET-11": "https://www.kabum.com.br/produto/1056511/headset-gamer-hyperx-cloud-alpha-sem-fio-audio-espacial-red",
  "SEED-HEADSET-13": "https://www.kabum.com.br/produto/114290/headset-gamer-logitech-g432-7-1-dolby-surround-para-pc-playstation-xbox-e-nintendo-switch-preto-azul-981-000769",
  "SEED-HEADSET-14": "https://www.kabum.com.br/produto/120487/headset-gamer-sem-fio-logitech-g733-7-1-dolby-surround-rgb-lightsync-blue-voice-para-pc-e-playstation-preto-981-000863",
  "SEED-HEADSET-15": "https://www.kabum.com.br/produto/128544/headset-gamer-razer-blackshark-v2-x-drivers-50mm-microfone-cardioide-surround-7-1-3-5-mm-preto-rz04-03240100",
  "SEED-HEADSET-17": "https://www.kabum.com.br/produto/593759/headset-gamer-corsair-hs35-v2-neodimio-de-50mm-com-microfone-para-pc-mac-consoles-e-celulares-preto-ca-9011377-na",
  "SEED-HEADSET-18": "https://www.kabum.com.br/produto/109994/headset-gamer-corsair-void-elite-wireless-rgb-7-1-surround-drivers-50mm-branco-ca-9011202-na",
  "SEED-HEADSET-21": "https://www.kabum.com.br/produto/227818/headset-gamer-redragon-zeus-x-chroma-mk-ii-rgb-som-surround-7-1-drivers-53mm-usb-preto-e-vermelho-h510-rgb",
  "SEED-HEADSET-22": "https://www.kabum.com.br/produto/645662/headset-steelseries-arctis-nova-1-branco-pc-mac-ps4-ps5-xbox-switch-e-dispositivos-moveis-fone-61607",
  "SEED-HEADSET-23": "https://www.kabum.com.br/produto/1056356/headset-steelseries-arctis-nova-7-wireless-gen-2-cor-preto",
  "SEED-KEYB-01": "https://www.kabum.com.br/produto/999719/teclado-mecanico-gamer-redragon-kumara-elite-rainbow-switch-brown-tipo-c-abnt2-preto-k552-krs-pt-brown-",
  "SEED-KEYB-03": "https://www.kabum.com.br/produto/99696/teclado-gamer-hyperx-alloy-core-rgb-abnt2-hx-kb5me2-br",
  "SEED-KEYB-05": "https://www.kabum.com.br/produto/593793/teclado-gamer-corsair-core-k55-rgb-icue-rgb-usb-2-0-preto-ch-9226c65-br",
  "SEED-KEYB-07": "https://www.kabum.com.br/produto/458558/teclado-gamer-redragon-karura-luluca-rgb-abnt2",
  "SEED-KEYB-08": "https://www.kabum.com.br/produto/452857/teclado-mecanico-gamer-logitech-g413-se-preto-920-010554",
  "SEED-KEYB-09": "https://www.kabum.com.br/produto/105009/teclado-mecanico-gamer-hyperx-alloy-origins-core-rgb-switch-hyperx-red-usb-tipo-c-abnt2-preto-4p5p3a2-ac4",
  "SEED-KEYB-12": "https://www.kabum.com.br/produto/703012/teclado-gamer-logitech-g-pro-x-tkl-rapid-switches-magnetico-analogicos-modo-rapid-trigger-layout-us-preto-920-013131",
  "SEED-KEYB-15": "https://www.kabum.com.br/produto/722601/teclado-magnetico-gamer-corsair-k70-pro-tkl-led-rgb-switch-corsair-mgx-hall-effect-rapid-trigger-anti-ghosting-us-preto-ch-911911g-na",
  "SEED-KEYB-18": "https://www.kabum.com.br/produto/20866/teclado-com-fio-usb-logitech-k120-resistente-a-respingos-e-layout-abnt2-920-004423",
  "SEED-KEYB-21": "https://www.kabum.com.br/produto/1054492/teclado-magnetico-redragon-kumara-rt-k552-m-rgb-8000hz-rapid-trigger",
  "SEED-KEYB-25": "https://www.kabum.com.br/produto/156354/teclado-mecanico-gamer-razer-blackwidow-v3-tenkeyless-chroma-razer-rgb-switch-yellow-us-preto-rz03-03491800-r3m1",
  "SEED-MB-01": "https://www.kabum.com.br/produto/398510/placa-mae-asus-prime-a520m-k-amd-am3-matx-ddr4-1500-m0eay0",
  "SEED-MB-03": "https://www.kabum.com.br/produto/875852/placa-mae-gigabyte-b550m-ds3h-ac-r2-amd-am4-micro-atx-ddr4-rgb-wi-fi-bluetooth-preto-b550m-ds3h-ac-r2",
  "SEED-MB-05": "https://www.kabum.com.br/produto/133767/placa-mae-asrock-b450m-steel-legend-amd-am4-matx-ddr4",
  "SEED-MB-07": "https://www.kabum.com.br/produto/940305/placa-mae-msi-pro-b760m-p-intel-b760-ddr4-preto-pro-b760m-p-ddr4",
  "SEED-MB-08": "https://www.kabum.com.br/produto/502496/placa-mae-msi-mag-b650-tomahawk-am5-atx-ddr5-wifi",
  "SEED-MB-09": "https://www.kabum.com.br/produto/395136/placa-mae-gigabyte-z790-aorus-elite-ax-lga-1700-atx-ddr5-wi-fi-preto-z790-aorus-elite-ax",
  "SEED-MB-13": "https://www.kabum.com.br/produto/265624/placa-mae-asrock-a520m-hvs-amd-am4-matx-ddr4-90-mxbe60-a0uayz",
  "SEED-MB-15": "https://www.kabum.com.br/produto/239693/placa-mae-gigabyte-b450m-ds3h-v2-amd-am4-matx-ddr4-hdmi",
  "SEED-MB-18": "https://www.kabum.com.br/produto/619346/placa-mae-gigabyte-a620m-gaming-x-ax-r1-1-ddr5-am5-micro-atx",
  "SEED-MB-19": "https://www.kabum.com.br/produto/525050/placa-mae-asrock-b650m-hdv-m-2-amd-b650-matx-ddr5-preto-90-mxbla-",
  "SEED-MB-22": "https://www.kabum.com.br/produto/587807/placa-mae-asrock-h610m-hdv-m-2-d5-intel-chipset-h610-ddr5-lga-1700-matx",
  "SEED-MB-23": "https://www.kabum.com.br/produto/644839/placa-mae-gigabyte-h610m-h-intel-13-12-geracao-lga-1700-ddr4-micro-atx",
  "SEED-MB-24": "https://www.kabum.com.br/produto/312739/placa-mae-asus-prime-d4-intel-lga-1700-matx-ddr4-h610m-e",
  "SEED-MB-25": "https://www.kabum.com.br/produto/495667/placa-mae-msi-mag-b760-tomahawk-wifi-intel-lga-1700-atx-12-13-14-geracoes-ddr5-bluetooth-911-7d96-013",
  "SEED-MONITOR-02": "https://www.kabum.com.br/produto/294985/monitor-lg-23-8-led-full-hd-75hz-ips-hdmi-vga-freesync-preto-24mp400-b",
  "SEED-MONITOR-07": "https://www.kabum.com.br/produto/1023251/monitor-gamer-samsung-odyssey-g5-34p-ultrawide-165hz-1ms-hdr10-hdmi-freesync-premium",
  "SEED-MONITOR-17": "https://www.kabum.com.br/produto/232252/monitor-gamer-samsung-odyssey-g3-24pol-full-hd-144-hz-1ms-hdmi-display-port-vga-freesync-premium-regulagem-de-altura-lf24g35tfwlxzd",
  "SEED-MOUSE-01": "https://www.kabum.com.br/produto/112948/mouse-gamer-logitech-g203-lightsync-rgb-efeito-de-ondas-de-cores-6-botoes-programaveis-e-ate-8-000-dpi-preto-910-005793",
  "SEED-MOUSE-02": "https://www.kabum.com.br/produto/94555/mouse-gamer-redragon-cobra-chroma-rgb-12400-dpi-8-botoes-preto-m711",
  "SEED-MOUSE-03": "https://www.kabum.com.br/produto/921180/mouse-gamer-razer-deathadder-essential-com-fio-6400-dpi-branco-rz01-03850200-r3m1",
  "SEED-MOUSE-04": "https://www.kabum.com.br/produto/98696/mouse-gamer-hyperx-pulsefire-core-rgb-6200-dpi-4p4f8aa",
  "SEED-MOUSE-06": "https://www.kabum.com.br/produto/519839/mouse-gamer-fortrek-vickers-new-edition-rgb-8000-dpi-6-botoes-preto-77246",
  "SEED-MOUSE-07": "https://www.kabum.com.br/produto/98244/mouse-gamer-logitech-g502-hero-com-rgb-lightsync-ajustes-de-peso-11-botoes-programaveis-sensor-hero-25k-910-005550",
  "SEED-MOUSE-08": "https://www.kabum.com.br/produto/507609/mouse-gamer-razer-viper-mini-signature-edition-30000dpi-49g-8khz",
  "SEED-MOUSE-09": "https://www.kabum.com.br/produto/590471/mouse-gamer-redragon-ranger-basic-preto-m910-k",
  "SEED-MOUSE-12": "https://www.kabum.com.br/produto/97092/mouse-gamer-sem-fio-logitech-g305-lightspeed-12000-dpi-6-botoes-preto-910-005281",
  "SEED-MOUSE-13": "https://www.kabum.com.br/produto/152166/mouse-gamer-redragon-griffin-chroma-rgb-7200dpi-8-botoes-preto-paw3212",
  "SEED-MOUSE-14": "https://www.kabum.com.br/produto/632852/mouse-gamer-com-fio-redragon-usb-centrophorus-m601-rgb-7200dpi-1000hz-cor-preto",
  "SEED-MOUSE-15": "https://www.kabum.com.br/produto/476952/mouse-gamer-razer-basilisk-v3-rgb-chroma-26000-dpi-optical-switch-11-botoes-preto-rz01-04000100-r3u1",
  "SEED-MOUSE-17": "https://www.kabum.com.br/produto/131189/mouse-gamer-corsair-katar-pro-ultra-leve-rgb-6-botoes-12400dpi-preto-ch-930c011-na",
  "SEED-MOUSE-19": "https://www.kabum.com.br/produto/384661/mouse-gamer-fortrek-g-black-hawk-rgb-usb-2-0-7200dpi-preto-75682",
  "SEED-MOUSE-20": "https://www.kabum.com.br/produto/149990/mouse-sem-fio-gamer-logitech-g-pro-x-superlight-lightspeed-25000-dpi-5-botoes-branco-910-005941",
  "SEED-MOUSE-21": "https://www.kabum.com.br/produto/618927/mouse-gamer-razer-viper-v3-pro-35000-dpi-54g-ultraleve-com-dongle-8k-95hr-de-bateria-recarregavel-preto",
  "SEED-MOUSE-23": "https://www.kabum.com.br/produto/525157/mouse-gamer-havit-hv-ms1001-rgb-4800-dpi-7-botoes-preto",
  "SEED-MOUSE-25": "https://www.kabum.com.br/produto/133268/mouse-vinik-gamer-vx-gaming-galatica-2400-dpi-led-azul",
  "SEED-PSU-06": "https://www.kabum.com.br/produto/1063045/fonte-cooler-master-mwe-v3-gold-650w-atx-3-1-80-plus-mpe-6502-acaag-3bbr",
  "SEED-PSU-12": "https://www.kabum.com.br/produto/1031691/fonte-corsair-rm750x-shift-750w-80-plus-gold-totalmente-modular-pfc-ativo-com-cabo-preto-cp-9020298",
  "SEED-PSU-17": "https://www.kabum.com.br/produto/923379/fonte-cooler-master-mwe-gold-750-v3-atx-3-1-80-plus-gold",
  "SEED-PSU-23": "https://www.kabum.com.br/produto/1031689/fonte-corsair-rm1000x-shift-1000w-80-plus-gold-totalmente-modular-pfc-ativo-com-cabo-preto-cp-9020300",
  "SEED-RAM-01": "https://www.kabum.com.br/produto/172365/memoria-ram-kingston-fury-beast-8gb-3200mhz-ddr4-cl16-preto-kf432c16bb-8",
  "SEED-RAM-02": "https://www.kabum.com.br/produto/1020445/memoria-kingston-fury-beast-16gb-ddr4-3200mhz-cl16-2x8gb-alta-performance-gamer",
  "SEED-RAM-03": "https://www.kabum.com.br/produto/402907/memoria-kingston-fury-beast-16gb-ram-3200mhz-ddr4-kf432c16bb-16",
  "SEED-RAM-04": "https://www.kabum.com.br/produto/110769/memoria-ram-corsair-vengeance-lpx-16gb-2x8gb-2400mhz-ddr4-cl16-black-cmk16gx4m2a2400c16",
  "SEED-RAM-05": "https://www.kabum.com.br/produto/382771/memoria-ram-corsair-vengeance-rgb-32gb-2x16gb-6200mhz-ddr5-cl36-preto-cmh32gx5m2b6200c36",
  "SEED-RAM-07": "https://www.kabum.com.br/produto/688214/memoria-ram-xpg-lancer-blade-rgb-16gb-6000mts-ddr5-cl48-preto",
  "SEED-RAM-09": "https://www.kabum.com.br/produto/581703/memoria-crucial-basics-8gb-3200mhz-ddr4-udimm-cb8gu3200",
  "SEED-RAM-13": "https://www.kabum.com.br/produto/1055751/memoria-ram-corsair-vengeance-lpx-ddr4-8gb-3200mhz-preto-cmk8gx4m1z3200c16-",
  "SEED-RAM-14": "https://www.kabum.com.br/produto/97099/memoria-ram-corsair-vengeance-rgb-pro-16gb-2x8gb-2666mhz-ddr4-cl16-preto-cmw16gx4m2a2666c16",
  "SEED-RAM-16": "https://www.kabum.com.br/produto/512397/memoria-gamer-xpg-spectrix-d35g-16gb-rgb-ddr4-3200-mhz-branco-ax4u320016g16a-swhd35g",
  "SEED-RAM-19": "https://www.kabum.com.br/produto/484113/memoria-gamer-crucial-ballistix-16gb-2400mhz-desktop",
  "SEED-RAM-22": "https://www.kabum.com.br/produto/1055706/memoria-ram-kingston-fury-renegade-ddr5-32gb-2x16gb-6400mhz-rgb-preto-prata-kf564c32rsak2-32-",
  "SEED-RAM-23": "https://www.kabum.com.br/produto/469049/memoria-ram-corsair-vengeance-64gb-2x32gb-6000mhz-ddr5-cl30-preto-cmk64gx5m2b6000c30",
  "SEED-RAM-24": "https://www.kabum.com.br/produto/905306/memoria-16gb-ddr4-3200mhz-patriot-viper-stell-cinza-pvs416g320c6",
  "SEED-SSD-01": "https://www.kabum.com.br/produto/400945/ssd-kingston-nv2-500gb-m-2-2280-nvme-pcie-4-0-x4-leitura-3500mb-s-e-gravacao-2100mb-s-preto-snv2s-500g",
  "SEED-SSD-02": "https://www.kabum.com.br/produto/400812/ssd-1tb-kingston-nv2-m-2-2280-pcie-nvme-leitura-3500mb-s-gravacao-2100mb-s-snv2s-1000g",
  "SEED-SSD-07": "https://www.kabum.com.br/produto/920739/ssd-wd-green-480gb-2-5-sata-iii-545mb-s-wds480g3g0a",
  "SEED-SSD-11": "https://www.kabum.com.br/produto/85197/ssd-kingston-a400-240gb-sata-iii-2-5-leitura-500mb-s-gravacao-350mb-s-preto-sa400s37-240g",
  "SEED-SSD-13": "https://www.kabum.com.br/produto/248401/ssd-sata-crucial-bx500-480gb-leitura-540-mb-s-gravacao-500-mb-s-ct480bx500ssd1",
  "SEED-SSD-17": "https://www.kabum.com.br/produto/647831/ssd-500gb-2-5-sata-3-870-evo-560mb-s-leit-530mb-s-grav-mz-77e500b-eu-samsung",
  "SEED-SSD-18": "https://www.kabum.com.br/produto/387181/ssd-m-2-wd-sn570-blue-500gb-3300mbs-",
  "SEED-WCOOL-03": "https://www.kabum.com.br/produto/453551/water-cooler-deepcool-ls320-wh-rgb-120mm-intel-e-amd-branco",
  "SEED-WCOOL-05": "https://www.kabum.com.br/produto/546216/water-cooler-corsair-icue-link-h100i-rgb-240mm-white-aio-cw-9061005-ww",
  "SEED-WCOOL-07": "https://www.kabum.com.br/produto/415797/water-cooler-nzxt-kraken-240-rgb-240mm-amd-intel-branco-rl-kr240-w1",
  "SEED-WCOOL-17": "https://www.kabum.com.br/produto/415804/water-cooler-nzxt-kraken-elite-280-280mm-amd-intel-preto-rl-kn28e-b1",
  "SEED-WCOOL-18": "https://www.kabum.com.br/produto/728412/water-cooler-nzxt-kraken-plus-360-rgb-v2-preto-rl-kr360-b2",
  "SEED-WCOOL-22": "https://www.kabum.com.br/produto/626522/water-cooler-thermaltake-v2-th240-ultra-snow-argb-120mm-amd-intel-branco-cl-w404-pl12sw-a",
}


class PopularPecasService:
  """Insere as pecas da seed que ainda nao existem no banco (por part_number). Nao faz nenhuma chamada de rede."""

  def executar(self) -> None:
    for classe, itens in self._dados_seed().items():
      self._popular_classe(classe, itens)

  def _popular_classe(self, classe, itens: list[dict]) -> None:
    part_numbers = [item["part_number"] for item in itens]
    existentes = {
      row.part_number
      for row in classe.query.filter(classe.part_number.in_(part_numbers)).all()
    }

    novos = [classe(**item) for item in itens if item["part_number"] not in existentes]
    db.session.add_all(novos)
    db.session.commit()

    print(f"[seed] {classe.__name__}: {len(novos)} inseridos, {len(itens) - len(novos)} já existiam")

  def _dados_seed(self) -> dict:
    return {
      Processador: self._processadores(),
      PlacaMae: self._placas_mae(),
      PlacaVideo: self._placas_video(),
      MemoriaRAM: self._memorias_ram(),
      SSD: self._ssds(),
      HD: self._hds(),
      Fonte: self._fontes(),
      Gabinete: self._gabinetes(),
      WaterCooler: self._water_coolers(),
      AirCooler: self._air_coolers(),
      Fan: self._fans(),
      Fone: self._fones(),
      Teclado: self._teclados(),
      Mouse: self._mouses(),
      Monitor: self._monitores(),
    }

  def _processadores(self) -> list[dict]:
    base = [
      ("AMD", "Ryzen 5 5600", "AM4", 6, 12, 3.5, 4.4, True, "Radeon Vega", True, "Wraith Stealth", 65),
      ("AMD", "Ryzen 7 5700X", "AM4", 8, 16, 3.4, 4.6, False, None, False, None, 65),
      ("AMD", "Ryzen 5 7600", "AM5", 6, 12, 3.8, 5.1, True, "Radeon Graphics", True, "Wraith Stealth", 65),
      ("AMD", "Ryzen 7 7700X", "AM5", 8, 16, 4.5, 5.4, True, "Radeon Graphics", False, None, 105),
      ("AMD", "Ryzen 9 7900X", "AM5", 12, 24, 4.7, 5.6, True, "Radeon Graphics", False, None, 170),
      ("Intel", "Core i3-12100F", "LGA1700", 4, 8, 3.3, 4.3, False, None, False, None, 58),
      ("Intel", "Core i5-12400F", "LGA1700", 6, 12, 2.5, 4.4, False, None, False, None, 65),
      ("Intel", "Core i5-13400F", "LGA1700", 10, 16, 2.5, 4.6, False, None, False, None, 65),
      ("Intel", "Core i7-13700K", "LGA1700", 16, 24, 3.4, 5.4, True, "UHD Graphics 770", False, None, 125),
      ("Intel", "Core i9-14900K", "LGA1700", 24, 32, 3.2, 6.0, True, "UHD Graphics 770", False, None, 125),
      ("AMD", "Ryzen 3 4100", "AM4", 4, 8, 3.8, 4.0, False, None, True, "Wraith Stealth", 65),
      ("AMD", "Ryzen 5 5500", "AM4", 6, 12, 3.6, 4.2, False, None, True, "Wraith Stealth", 65),
      ("AMD", "Ryzen 7 5800X3D", "AM4", 8, 16, 3.4, 4.5, False, None, False, None, 105),
      ("AMD", "Ryzen 9 5900X", "AM4", 12, 24, 3.7, 4.8, False, None, False, None, 105),
      ("AMD", "Ryzen 5 7500F", "AM5", 6, 12, 3.7, 5.0, False, None, False, None, 65),
      ("AMD", "Ryzen 7 7800X3D", "AM5", 8, 16, 4.2, 5.0, True, "Radeon Graphics", False, None, 120),
      ("AMD", "Ryzen 9 7950X", "AM5", 16, 32, 4.5, 5.7, True, "Radeon Graphics", False, None, 170),
      ("AMD", "Ryzen 5 8500G", "AM5", 6, 12, 3.5, 5.0, True, "Radeon 740M", True, "Wraith Stealth", 65),
      ("Intel", "Core i3-10100F", "LGA1200", 4, 8, 3.6, 4.3, False, None, False, None, 65),
      ("Intel", "Core i5-10400F", "LGA1200", 6, 12, 2.9, 4.3, False, None, False, None, 65),
      ("Intel", "Core i5-11400F", "LGA1200", 6, 12, 2.6, 4.4, False, None, False, None, 65),
      ("Intel", "Core i5-13600K", "LGA1700", 14, 20, 3.5, 5.1, True, "UHD Graphics 770", False, None, 125),
      ("Intel", "Core i7-12700F", "LGA1700", 12, 20, 2.1, 4.9, False, None, False, None, 65),
      ("Intel", "Core i9-13900K", "LGA1700", 24, 32, 3.0, 5.8, True, "UHD Graphics 770", False, None, 125),
      ("Intel", "Core i3-13100F", "LGA1700", 4, 8, 3.4, 4.5, False, None, False, None, 58),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": consumo,
        "preco": preco,
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "soquete": soquete,
        "nucleo": nucleo,
        "thread": thread,
        "clockbase": clockbase,
        "clockmax": clockmax,
        "videointegrado": videointegrado,
        "modelo_videointegrado": modelo_videointegrado,
        "cooler": cooler,
        "modelo_cooler": modelo_cooler,
      }
      for indice, (
        fabricante, modelo, soquete, nucleo, thread, clockbase, clockmax,
        videointegrado, modelo_videointegrado, cooler, modelo_cooler, consumo,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-CPU-{indice:02d}"]
      for preco in [self._preco(indice, 650, 180)]
    ]

  def _placas_mae(self) -> list[dict]:
    base = [
      ("ASUS", "Prime A520M-K", "AM4", "A520", "mATX", "DDR4", 2, 64, 1),
      ("ASUS", "TUF Gaming B550-Plus", "AM4", "B550", "ATX", "DDR4", 4, 128, 2),
      ("Gigabyte", "B550M DS3H", "AM4", "B550", "mATX", "DDR4", 4, 128, 1),
      ("Gigabyte", "B650M DS3H", "AM5", "B650", "mATX", "DDR5", 4, 128, 2),
      ("ASRock", "B450M Steel Legend", "AM4", "B450", "mATX", "DDR4", 4, 64, 1),
      ("ASUS", "Prime B660M-A", "LGA1700", "B660", "mATX", "DDR4", 4, 128, 2),
      ("MSI", "PRO B760M-P", "LGA1700", "B760", "mATX", "DDR5", 4, 128, 2),
      ("MSI", "MAG B650 Tomahawk", "AM5", "B650", "ATX", "DDR5", 4, 128, 2),
      ("Gigabyte", "Z790 Aorus Elite", "LGA1700", "Z790", "ATX", "DDR5", 4, 128, 3),
      ("ASRock", "X670E Steel Legend", "AM5", "X670E", "ATX", "DDR5", 4, 128, 3),
      ("ASUS", "Prime B450M-A", "AM4", "B450", "mATX", "DDR4", 2, 32, 1),
      ("Gigabyte", "A320M-S2H", "AM4", "A320", "mATX", "DDR4", 2, 32, 0),
      ("ASRock", "A520M-HVS", "AM4", "A520", "mATX", "DDR4", 2, 64, 1),
      ("MSI", "B450M PRO-VDH MAX", "AM4", "B450", "mATX", "DDR4", 4, 64, 1),
      ("Gigabyte", "B450M DS3H", "AM4", "B450", "mATX", "DDR4", 4, 64, 1),
      ("ASUS", "ROG Strix B550-F Gaming", "AM4", "B550", "ATX", "DDR4", 4, 128, 2),
      ("MSI", "PRO B550M-VC", "AM4", "B550", "mATX", "DDR4", 4, 128, 1),
      ("Gigabyte", "A620M Gaming X", "AM5", "A620", "mATX", "DDR5", 2, 96, 1),
      ("ASRock", "B650M-HDV/M.2", "AM5", "B650", "mATX", "DDR5", 2, 96, 1),
      ("ASUS", "TUF Gaming B650-Plus", "AM5", "B650", "ATX", "DDR5", 4, 128, 2),
      ("MSI", "PRO B660M-A", "LGA1700", "B660", "mATX", "DDR4", 4, 128, 2),
      ("ASRock", "H610M-HDV/M.2", "LGA1700", "H610", "mATX", "DDR4", 2, 64, 1),
      ("Gigabyte", "H610M H", "LGA1700", "H610", "mATX", "DDR4", 2, 64, 1),
      ("ASUS", "Prime H610M-E", "LGA1700", "H610", "mATX", "DDR4", 2, 64, 1),
      ("MSI", "MAG B760 Tomahawk", "LGA1700", "B760", "ATX", "DDR5", 4, 192, 3),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 45.0,
        "preco": self._preco(indice, 500, 90),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "socket": socket,
        "chipset": chipset,
        "formato": formato,
        "tipo_memoria": tipo_memoria,
        "quantidade_slots_ram": slots_ram,
        "memoria_maxima_gb": memoria_max,
        "quantidade_slots_m2": slots_m2,
      }
      for indice, (
        fabricante, modelo, socket, chipset, formato, tipo_memoria,
        slots_ram, memoria_max, slots_m2,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-MB-{indice:02d}"]
    ]

  def _placas_video(self) -> list[dict]:
    base = [
      ("NVIDIA", "GeForce GTX 1660 Super", 6, "GDDR6", "192-bit", 125, 1),
      ("NVIDIA", "GeForce RTX 3060", 12, "GDDR6", "192-bit", 170, 2),
      ("NVIDIA", "GeForce RTX 3060 Ti", 8, "GDDR6", "256-bit", 200, 2),
      ("NVIDIA", "GeForce RTX 4060", 8, "GDDR6", "128-bit", 115, 2),
      ("NVIDIA", "GeForce RTX 4060 Ti", 8, "GDDR6", "128-bit", 160, 2),
      ("NVIDIA", "GeForce RTX 4070", 12, "GDDR6X", "192-bit", 200, 3),
      ("NVIDIA", "GeForce RTX 4070 Super", 12, "GDDR6X", "192-bit", 220, 3),
      ("AMD", "Radeon RX 6600", 8, "GDDR6", "128-bit", 132, 2),
      ("AMD", "Radeon RX 6700 XT", 12, "GDDR6", "192-bit", 230, 3),
      ("AMD", "Radeon RX 7600", 8, "GDDR6", "128-bit", 165, 2),
      ("NVIDIA", "GeForce GT 1030", 2, "GDDR5", "64-bit", 30, 1),
      ("NVIDIA", "GeForce GTX 1650", 4, "GDDR6", "128-bit", 75, 1),
      ("NVIDIA", "GeForce GTX 1660", 6, "GDDR5", "192-bit", 120, 2),
      ("NVIDIA", "GeForce RTX 3050", 8, "GDDR6", "128-bit", 130, 2),
      ("NVIDIA", "GeForce RTX 3070", 8, "GDDR6", "256-bit", 220, 3),
      ("NVIDIA", "GeForce RTX 3080", 10, "GDDR6X", "320-bit", 320, 3),
      ("NVIDIA", "GeForce RTX 4070 Ti", 12, "GDDR6X", "192-bit", 285, 3),
      ("NVIDIA", "GeForce RTX 4080", 16, "GDDR6X", "256-bit", 320, 3),
      ("NVIDIA", "GeForce RTX 4090", 24, "GDDR6X", "384-bit", 450, 3),
      ("AMD", "Radeon RX 550", 4, "GDDR5", "128-bit", 50, 1),
      ("AMD", "Radeon RX 6500 XT", 4, "GDDR6", "64-bit", 107, 2),
      ("AMD", "Radeon RX 6650 XT", 8, "GDDR6", "128-bit", 180, 2),
      ("AMD", "Radeon RX 6750 XT", 12, "GDDR6", "192-bit", 250, 3),
      ("AMD", "Radeon RX 7700 XT", 12, "GDDR6", "192-bit", 245, 3),
      ("AMD", "Radeon RX 7800 XT", 16, "GDDR6", "256-bit", 263, 3),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": float(consumo_w),
        "preco": self._preco(indice, 1400, 250),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "memoria_gb": memoria_gb,
        "tipo_memoria": tipo_memoria,
        "interface_memoria": interface_memoria,
        "consumo_w": consumo_w,
        "quantidade_fans": fans,
        "conectores_energia": "1x 8-pin" if consumo_w < 180 else "1x 12-pin",
      }
      for indice, (
        fabricante, modelo, memoria_gb, tipo_memoria, interface_memoria, consumo_w, fans,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-GPU-{indice:02d}"]
    ]

  def _memorias_ram(self) -> list[dict]:
    base = [
      ("Kingston", "Fury Beast 8GB", 8, "DDR4", 3200, "CL16", 1),
      ("Kingston", "Fury Beast 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("Kingston", "Fury Beast 16GB", 16, "DDR5", 5600, "CL36", 1),
      ("Corsair", "Vengeance LPX 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("Corsair", "Vengeance RGB 32GB (2x16GB)", 32, "DDR5", 6000, "CL30", 2),
      ("XPG", "Gammix D30 8GB", 8, "DDR4", 3000, "CL16", 1),
      ("Adata", "XPG Lancer 16GB", 16, "DDR5", 6000, "CL30", 1),
      ("TeamGroup", "T-Force Vulcan 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("Crucial", "Basics 8GB", 8, "DDR4", 2666, "CL19", 1),
      ("G.Skill", "Trident Z5 32GB (2x16GB)", 32, "DDR5", 6400, "CL32", 2),
      ("Kingston", "Fury Beast 32GB (2x16GB)", 32, "DDR4", 3200, "CL16", 2),
      ("Kingston", "Fury Beast 32GB", 32, "DDR5", 6000, "CL36", 1),
      ("Corsair", "Vengeance LPX 8GB", 8, "DDR4", 3000, "CL16", 1),
      ("Corsair", "Vengeance RGB Pro 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("Corsair", "Dominator Platinum 32GB (2x16GB)", 32, "DDR5", 6200, "CL36", 2),
      ("XPG", "Spectrix D35G 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("Adata", "Premier 8GB", 8, "DDR4", 2666, "CL19", 1),
      ("TeamGroup", "T-Force Delta RGB 16GB (2x8GB)", 16, "DDR5", 6000, "CL38", 2),
      ("Crucial", "Ballistix 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("G.Skill", "Ripjaws V 16GB (2x8GB)", 16, "DDR4", 3600, "CL16", 2),
      ("G.Skill", "Trident Z Neo 32GB (2x16GB)", 32, "DDR4", 3600, "CL16", 2),
      ("Kingston", "Fury Renegade 32GB (2x16GB)", 32, "DDR5", 6400, "CL32", 2),
      ("Corsair", "Vengeance 64GB (2x32GB)", 64, "DDR5", 5600, "CL36", 2),
      ("Patriot", "Viper Steel 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("PNY", "XLR8 16GB", 16, "DDR4", 3200, "CL16", 1),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 5.0,
        "preco": self._preco(indice, 700, 90),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "capacidade_gb": capacidade_gb,
        "ddr": ddr,
        "frequencia_mhz": frequencia,
        "latencia": latencia,
        "quantidade_pentes": pentes,
        "iluminacao": False,
      }
      for indice, (
        fabricante, modelo, capacidade_gb, ddr, frequencia, latencia, pentes,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-RAM-{indice:02d}"]
    ]

  def _ssds(self) -> list[dict]:
    base = [
      ("Kingston", "NV2 500GB", 500, "NVMe", "PCIe 4.0", "M.2", 3500, 2100),
      ("Kingston", "NV2 1TB", 1000, "NVMe", "PCIe 4.0", "M.2", 3500, 2800),
      ("Crucial", "MX500 500GB", 500, "SATA", "SATA III", "2.5", 560, 510),
      ("Crucial", "P3 1TB", 1000, "NVMe", "PCIe 3.0", "M.2", 3500, 3000),
      ("Samsung", "970 EVO Plus 500GB", 500, "NVMe", "PCIe 3.0", "M.2", 3500, 3200),
      ("Samsung", "980 1TB", 1000, "NVMe", "PCIe 3.0", "M.2", 3500, 3000),
      ("WD", "Green 480GB", 480, "SATA", "SATA III", "2.5", 545, 465),
      ("WD", "Black SN770 1TB", 1000, "NVMe", "PCIe 4.0", "M.2", 5150, 4900),
      ("Adata", "Legend 800 500GB", 500, "NVMe", "PCIe 4.0", "M.2", 3500, 2200),
      ("TeamGroup", "MP34 512GB", 512, "NVMe", "PCIe 3.0", "M.2", 3400, 3000),
      ("Kingston", "A400 240GB", 240, "SATA", "SATA III", "2.5", 500, 350),
      ("Kingston", "NV2 2TB", 2000, "NVMe", "PCIe 4.0", "M.2", 3500, 2800),
      ("Crucial", "BX500 480GB", 480, "SATA", "SATA III", "2.5", 540, 500),
      ("Crucial", "P5 Plus 1TB", 1000, "NVMe", "PCIe 4.0", "M.2", 6600, 5000),
      ("Samsung", "970 EVO Plus 1TB", 1000, "NVMe", "PCIe 3.0", "M.2", 3500, 3300),
      ("Samsung", "980 PRO 1TB", 1000, "NVMe", "PCIe 4.0", "M.2", 7000, 5000),
      ("Samsung", "870 EVO 500GB", 500, "SATA", "SATA III", "2.5", 560, 530),
      ("WD", "Blue SN570 500GB", 500, "NVMe", "PCIe 3.0", "M.2", 3500, 2300),
      ("WD", "Black SN850X 1TB", 1000, "NVMe", "PCIe 4.0", "M.2", 7300, 6300),
      ("Adata", "Legend 700 512GB", 512, "NVMe", "PCIe 3.0", "M.2", 2000, 1600),
      ("TeamGroup", "MP33 512GB", 512, "NVMe", "PCIe 3.0", "M.2", 1700, 1400),
      ("Lexar", "NM610 1TB", 1000, "NVMe", "PCIe 3.0", "M.2", 2100, 1600),
      ("XPG", "Gammix S11 Pro 512GB", 512, "NVMe", "PCIe 3.0", "M.2", 3500, 3000),
      ("Kingston", "KC3000 1TB", 1000, "NVMe", "PCIe 4.0", "M.2", 7000, 6000),
      ("Crucial", "MX500 1TB", 1000, "SATA", "SATA III", "2.5", 560, 510),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 4.0,
        "preco": self._preco(indice, 450, 50),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "capacidade_gb": capacidade_gb,
        "tipo": tipo,
        "interface": interface,
        "formato": formato,
        "velocidade_leitura_mbps": leitura,
        "velocidade_gravacao_mbps": gravacao,
      }
      for indice, (
        fabricante, modelo, capacidade_gb, tipo, interface, formato, leitura, gravacao,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-SSD-{indice:02d}"]
    ]

  def _hds(self) -> list[dict]:
    base = [
      ("Seagate", "Barracuda 1TB", 1000, 7200, "SATA III", 64),
      ("Seagate", "Barracuda 2TB", 2000, 7200, "SATA III", 256),
      ("WD", "Blue 1TB", 1000, 7200, "SATA III", 64),
      ("WD", "Blue 2TB", 2000, 5400, "SATA III", 256),
      ("WD", "Purple 4TB", 4000, 5400, "SATA III", 256),
      ("Toshiba", "P300 1TB", 1000, 7200, "SATA III", 64),
      ("Toshiba", "P300 2TB", 2000, 7200, "SATA III", 64),
      ("Seagate", "SkyHawk 2TB", 2000, 5900, "SATA III", 256),
      ("WD", "Black 1TB", 1000, 7200, "SATA III", 64),
      ("Seagate", "Barracuda 4TB", 4000, 5400, "SATA III", 256),
      ("Seagate", "Barracuda 500GB", 500, 7200, "SATA III", 32),
      ("Seagate", "Barracuda Compute 8TB", 8000, 5400, "SATA III", 256),
      ("Seagate", "IronWolf 2TB", 2000, 5900, "SATA III", 64),
      ("Seagate", "SkyHawk 4TB", 4000, 5900, "SATA III", 256),
      ("WD", "Blue 500GB", 500, 5400, "SATA III", 32),
      ("WD", "Blue 4TB", 4000, 5400, "SATA III", 256),
      ("WD", "Red Plus 4TB", 4000, 5400, "SATA III", 128),
      ("WD", "Black 4TB", 4000, 7200, "SATA III", 256),
      ("WD", "Purple 2TB", 2000, 5400, "SATA III", 64),
      ("Toshiba", "P300 4TB", 4000, 5400, "SATA III", 128),
      ("Toshiba", "X300 4TB", 4000, 7200, "SATA III", 128),
      ("Seagate", "Barracuda 3TB", 3000, 5400, "SATA III", 256),
      ("Seagate", "Exos 8TB", 8000, 7200, "SATA III", 256),
      ("WD", "Green 1TB", 1000, 5400, "SATA III", 64),
      ("Toshiba", "L200 1TB", 1000, 5400, "SATA III", 8),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 6.5,
        "preco": self._preco(indice, 350, 40),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "capacidade_gb": capacidade_gb,
        "velocidade_rpm": rpm,
        "interface": interface,
        "memoria_cache_mb": cache,
      }
      for indice, (
        fabricante, modelo, capacidade_gb, rpm, interface, cache,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-HDD-{indice:02d}"]
    ]

  def _fontes(self) -> list[dict]:
    base = [
      ("Corsair", "CV450", 450, "ATX", 78.0),
      ("Corsair", "RM650x", 650, "ATX", 87.0),
      ("EVGA", "500 W1", 500, "ATX", 82.0),
      ("XPG", "Core Reactor 650W", 650, "ATX", 82.0),
      ("Cooler Master", "MWE 550 Bronze", 550, "ATX", 82.0),
      ("Cooler Master", "MWE 650 Gold", 650, "ATX", 87.0),
      ("Gigabyte", "P450B", 450, "ATX", 82.0),
      ("Pichau", "Gaming 550W", 550, "ATX", 80.0),
      ("Thermaltake", "Smart 500W", 500, "ATX", 78.0),
      ("Seasonic", "Focus GX-750", 750, "ATX", 90.0),
      ("Corsair", "CV550", 550, "ATX", 80.0),
      ("Corsair", "RM750x", 750, "ATX", 90.0),
      ("EVGA", "600 BQ", 600, "ATX", 82.0),
      ("EVGA", "700 GQ", 700, "ATX", 87.0),
      ("XPG", "Core Reactor 750W", 750, "ATX", 87.0),
      ("Cooler Master", "MWE 450 White", 450, "ATX", 80.0),
      ("Cooler Master", "MWE 750 Gold", 750, "ATX", 90.0),
      ("Gigabyte", "P650B", 650, "ATX", 82.0),
      ("Pichau", "Squadra 650W", 650, "ATX", 82.0),
      ("Thermaltake", "Smart 600W", 600, "ATX", 78.0),
      ("Thermaltake", "Toughpower GF1 750W", 750, "ATX", 90.0),
      ("Seasonic", "Focus GX-650", 650, "ATX", 90.0),
      ("Corsair", "RM1000x", 1000, "ATX", 90.0),
      ("Redragon", "GC-PS001 500W", 500, "ATX", 78.0),
      ("Antec", "NeoECO 650W", 650, "ATX", 82.0),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": consumo,
        "preco": self._preco(indice, 600, 100),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "potencia_w": potencia_w,
        "formato": formato,
      }
      for indice, (
        fabricante, modelo, potencia_w, formato, consumo,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-PSU-{indice:02d}"]
    ]

  def _gabinetes(self) -> list[dict]:
    base = [
      ("Cooler Master", "MasterBox Q300L", "mATX", "ATX, mATX, ITX", 2, 2, 2, True, 360, 160, True),
      ("Cooler Master", "MasterBox TD500", "ATX", "ATX, mATX, ITX", 4, 2, 3, True, 410, 165, True),
      ("Pichau", "Aeron", "ATX", "ATX, mATX, ITX", 4, 2, 2, True, 350, 160, True),
      ("Redragon", "Deepsea", "mATX", "ATX, mATX, ITX", 2, 2, 1, False, 320, 155, False),
      ("Gamemax", "Vega Vision", "ATX", "ATX, mATX, ITX", 4, 2, 4, True, 380, 165, True),
      ("Xtreme Gamer", "Prisma", "mATX", "mATX, ITX", 2, 1, 1, False, 300, 150, False),
      ("Corsair", "4000D Airflow", "ATX", "ATX, mATX, ITX", 4, 2, 2, True, 360, 170, True),
      ("NZXT", "H510", "ATX", "ATX, mATX, ITX", 4, 2, 2, True, 381, 165, True),
      ("Lian Li", "Lancool 205", "mATX", "mATX, ITX", 2, 1, 3, True, 350, 160, True),
      ("Montech", "Air 100", "mATX", "ATX, mATX, ITX", 2, 2, 3, True, 320, 160, True),
      ("Cooler Master", "MasterBox NR200", "ITX", "mATX, ITX", 2, 2, 1, True, 330, 155, False),
      ("Cooler Master", "MasterBox MB520", "ATX", "ATX, mATX, ITX", 4, 2, 3, True, 410, 165, True),
      ("Pichau", "Nix Air", "ATX", "ATX, mATX, ITX", 4, 2, 3, True, 350, 160, True),
      ("Redragon", "Diamond Storm", "mATX", "ATX, mATX, ITX", 2, 2, 3, True, 340, 158, True),
      ("Gamemax", "Infinity", "mATX", "mATX, ITX", 2, 1, 2, False, 300, 150, False),
      ("Corsair", "5000D Airflow", "ATX", "ATX, mATX, ITX", 4, 2, 2, True, 420, 170, True),
      ("NZXT", "H510 Flow", "ATX", "ATX, mATX, ITX", 4, 2, 2, True, 381, 165, True),
      ("Lian Li", "Lancool II Mesh", "ATX", "ATX, mATX, ITX", 4, 2, 4, True, 384, 176, True),
      ("Montech", "Air 903", "ATX", "ATX, mATX, ITX", 4, 2, 4, True, 400, 175, True),
      ("Deepcool", "CC560", "ATX", "ATX, mATX, ITX", 4, 2, 4, True, 350, 165, True),
      ("Xtreme Gamer", "Dust", "mATX", "mATX, ITX", 2, 1, 1, False, 280, 145, False),
      ("Bluecase", "BG-018", "mATX", "ATX, mATX, ITX", 2, 2, 1, False, 320, 150, False),
      ("Aerocool", "Cylon", "ATX", "ATX, mATX, ITX", 4, 2, 3, True, 350, 160, True),
      ("Pichau", "Ryzen Edition", "ATX", "ATX, mATX, ITX", 4, 2, 3, True, 360, 160, True),
      ("Cougar", "MX330", "ATX", "ATX, mATX, ITX", 4, 2, 1, False, 320, 155, True),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 0.0,
        "preco": self._preco(indice, 400, 60),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "formato": formato,
        "formatos_placa_mae": formatos_placa_mae,
        "slots_expansao": slots_expansao,
        "bays_disco": bays_disco,
        "fans_inclusos": fans_inclusos,
        "suporte_water_cooler": suporte_water_cooler,
        "tamanho_max_gpu_mm": tamanho_max_gpu,
        "tamanho_max_cooler_mm": tamanho_max_cooler,
        "painel_vidro": painel_vidro,
      }
      for indice, (
        fabricante, modelo, formato, formatos_placa_mae, slots_expansao, bays_disco,
        fans_inclusos, suporte_water_cooler, tamanho_max_gpu, tamanho_max_cooler, painel_vidro,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-CASE-{indice:02d}"]
    ]

  def _water_coolers(self) -> list[dict]:
    base = [
      ("Cooler Master", "MasterLiquid ML240L", "Intel/AMD", 240, 2, True),
      ("Cooler Master", "MasterLiquid ML360R", "Intel/AMD", 360, 3, True),
      ("Deepcool", "LS320", "Intel/AMD", 240, 2, True),
      ("Deepcool", "LS520", "Intel/AMD", 240, 2, True),
      ("Corsair", "iCUE H100i", "Intel/AMD", 240, 2, True),
      ("Corsair", "iCUE H150i", "Intel/AMD", 360, 3, True),
      ("NZXT", "Kraken 240", "Intel/AMD", 240, 2, True),
      ("Lian Li", "Galahad 240", "Intel/AMD", 240, 2, True),
      ("ID-Cooling", "AURAFLOW X 240", "Intel/AMD", 240, 2, True),
      ("Pichau", "Fenix 240", "Intel/AMD", 240, 2, True),
      ("Cooler Master", "MasterLiquid ML120L", "Intel/AMD", 120, 1, False),
      ("Cooler Master", "MasterLiquid ML280 Mirror", "Intel/AMD", 280, 2, True),
      ("Deepcool", "LE500 Marrs", "Intel/AMD", 240, 2, True),
      ("Deepcool", "LT720", "Intel/AMD", 360, 3, True),
      ("Corsair", "iCUE H60i", "Intel/AMD", 120, 1, True),
      ("Corsair", "iCUE H115i", "Intel/AMD", 280, 2, True),
      ("NZXT", "Kraken 280", "Intel/AMD", 280, 2, True),
      ("NZXT", "Kraken 360", "Intel/AMD", 360, 3, True),
      ("Lian Li", "Galahad 360", "Intel/AMD", 360, 3, True),
      ("ID-Cooling", "AURAFLOW X 360", "Intel/AMD", 360, 3, True),
      ("Pichau", "Fenix 360", "Intel/AMD", 360, 3, True),
      ("Thermaltake", "TH240 ARGB", "Intel/AMD", 240, 2, True),
      ("Rise Mode", "Frost 240", "Intel/AMD", 240, 2, True),
      ("Gamemax", "Iceberg 240", "Intel/AMD", 240, 2, True),
      ("EVGA", "CLC 280", "Intel/AMD", 280, 2, True),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 12.0,
        "preco": self._preco(indice, 550, 90),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "compatibilidade": compatibilidade,
        "tamanho_radiador_mm": radiador,
        "quantidade_fans": fans,
        "iluminacao": iluminacao,
      }
      for indice, (
        fabricante, modelo, compatibilidade, radiador, fans, iluminacao,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-WCOOL-{indice:02d}"]
    ]

  def _air_coolers(self) -> list[dict]:
    base = [
      ("Cooler Master", "Hyper 212 Black", "Intel/AMD", 154, True),
      ("Deepcool", "AK400", "Intel/AMD", 129, False),
      ("Deepcool", "Gammaxx 400", "Intel/AMD", 152, True),
      ("Cooler Master", "Hyper H410R", "Intel/AMD", 130, True),
      ("Thermaltake", "UX200", "Intel/AMD", 121, True),
      ("PCYes", "Fantom Beta", "Intel/AMD", 130, True),
      ("Pichau", "Vortex Air 200", "Intel/AMD", 125, True),
      ("Redragon", "Tyr", "Intel/AMD", 155, True),
      ("ID-Cooling", "SE-224-XT", "Intel/AMD", 154, False),
      ("Cooler Master", "Hyper 212 Halo", "Intel/AMD", 155, True),
      ("Cooler Master", "Hyper 212 EVO", "Intel/AMD", 159, False),
      ("Cooler Master", "MasterAir MA410M", "Intel/AMD", 156, True),
      ("Deepcool", "AK620", "Intel/AMD", 160, False),
      ("Deepcool", "Gammaxx 400 V2", "Intel/AMD", 155, True),
      ("Thermaltake", "Contac Silent 12", "Intel/AMD", 154, False),
      ("PCYes", "Aeon", "Intel/AMD", 120, True),
      ("Pichau", "Ignis Air 100", "Intel/AMD", 120, True),
      ("Redragon", "Vikings", "Intel/AMD", 154, True),
      ("ID-Cooling", "SE-224-XT Basic", "Intel/AMD", 154, False),
      ("Cooler Master", "Hyper T20", "Intel/AMD", 118, False),
      ("Rise Mode", "Storm", "Intel/AMD", 125, True),
      ("Gamemax", "Gamma 300", "Intel/AMD", 130, True),
      ("Vinik", "Air Cooler VX Gamer", "Intel/AMD", 90, False),
      ("Deepcool", "GAMMAXX GT", "Intel/AMD", 153, True),
      ("Cougar", "Forza 50", "Intel/AMD", 128, False),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 3.0,
        "preco": self._preco(indice, 220, 40),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "compatibilidade": compatibilidade,
        "dimensoes": dimensoes,
        "iluminacao": iluminacao,
      }
      for indice, (
        fabricante, modelo, compatibilidade, dimensoes, iluminacao,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-ACOOL-{indice:02d}"]
    ]

  def _fans(self) -> list[dict]:
    base = [
      ("Cooler Master", "SickleFlow 120", 120, 1, True),
      ("Deepcool", "RF120", 120, 1, True),
      ("Corsair", "LL120", 120, 1, True),
      ("NZXT", "Aer RGB 2", 120, 1, True),
      ("Pichau", "Gaming ARGB", 120, 3, True),
      ("Redragon", "GC-F007", 120, 3, True),
      ("Rise Mode", "Wind Z3", 120, 3, True),
      ("Thermaltake", "Riing 12", 120, 1, True),
      ("Cooler Master", "MasterFan MF120", 120, 1, False),
      ("Deepcool", "FC140", 140, 1, True),
      ("Cooler Master", "MasterFan MF120 Halo", 120, 1, True),
      ("Deepcool", "CF120", 120, 3, True),
      ("Corsair", "LL140", 140, 1, True),
      ("Corsair", "QL120", 120, 3, True),
      ("NZXT", "Aer P120", 120, 1, False),
      ("Pichau", "Vortex ARGB", 120, 3, True),
      ("Redragon", "GC-F009", 120, 1, True),
      ("Rise Mode", "Wind Z6", 120, 3, True),
      ("Thermaltake", "Riing Trio 120", 120, 3, True),
      ("Cooler Master", "SickleFlow 120 ARGB", 120, 1, True),
      ("Deepcool", "FC120", 120, 3, True),
      ("Gamemax", "Draco 120", 120, 1, True),
      ("Xtreme Gamer", "Fan RGB 120", 120, 1, True),
      ("PCYes", "Big Fan", 200, 1, False),
      ("Vinik", "Fan Gamer 120", 120, 1, False),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 3.5,
        "preco": self._preco(indice, 120, 25),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "tamanho_mm": tamanho_mm,
        "quantidade": quantidade,
        "iluminacao": iluminacao,
      }
      for indice, (
        fabricante, modelo, tamanho_mm, quantidade, iluminacao,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-FAN-{indice:02d}"]
    ]

  def _fones(self) -> list[dict]:
    base = [
      ("HyperX", "Cloud Stinger", "Com fio", True, False, "P2 3.5mm"),
      ("Logitech", "G335", "Com fio", True, False, "P2 3.5mm"),
      ("Razer", "Kraken X", "Com fio", True, False, "USB"),
      ("Corsair", "HS55", "Com fio", True, False, "P2 3.5mm"),
      ("JBL", "Quantum 100", "Com fio", True, False, "P2 3.5mm"),
      ("HyperX", "Cloud II", "Com fio", True, False, "USB"),
      ("Havit", "H2002d", "Com fio", True, False, "P2 3.5mm"),
      ("Redragon", "Zeus", "Com fio", True, True, "USB"),
      ("Logitech", "G435", "Sem fio", True, False, "Bluetooth"),
      ("SteelSeries", "Arctis 1", "Sem fio", True, False, "USB"),
      ("HyperX", "Cloud Alpha", "Com fio", True, False, "P2 3.5mm"),
      ("HyperX", "Cloud Core II", "Com fio", True, False, "P2 3.5mm"),
      ("Logitech", "G432", "Com fio", True, False, "USB"),
      ("Logitech", "G733", "Sem fio", True, False, "USB"),
      ("Razer", "BlackShark V2 X", "Com fio", True, False, "P2 3.5mm"),
      ("Razer", "Kraken V3", "Com fio", True, False, "USB"),
      ("Corsair", "HS35", "Com fio", True, False, "P2 3.5mm"),
      ("Corsair", "Void RGB Elite", "Sem fio", True, False, "USB"),
      ("JBL", "Quantum 200", "Com fio", True, False, "P2 3.5mm"),
      ("Havit", "Gamenote H2019U", "Com fio", True, False, "USB"),
      ("Redragon", "Zeus X", "Com fio", True, True, "USB"),
      ("SteelSeries", "Arctis Nova 1", "Com fio", True, False, "P2 3.5mm"),
      ("SteelSeries", "Arctis 7", "Sem fio", True, False, "USB"),
      ("Fortrek", "G Pro", "Com fio", True, False, "P2 3.5mm"),
      ("Multilaser", "Warrior PH299", "Com fio", True, False, "P2 3.5mm"),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 1.0,
        "preco": self._preco(indice, 350, 60),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "conexao": conexao,
        "iluminacao": False,
        "tipo": "Headset",
        "microfone": microfone,
        "cancelamento_ruido": cancelamento_ruido,
        "resposta_frequencia": resposta_frequencia,
      }
      for indice, (
        fabricante, modelo, conexao, microfone, cancelamento_ruido, resposta_frequencia,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-HEADSET-{indice:02d}"]
    ]

  def _teclados(self) -> list[dict]:
    base = [
      ("Redragon", "Kumara K552", "ABNT2", "Outemu Blue", True, "Padrão"),
      ("Logitech", "G213 Prodigy", "ABNT2", None, False, "Padrão"),
      ("HyperX", "Alloy Core", "ABNT2", None, False, "Padrão"),
      ("Razer", "Cynosa V2", "ABNT2", None, False, "Padrão"),
      ("Corsair", "K55 RGB", "ABNT2", None, False, "Padrão"),
      ("Fortrek", "GK-702", "ABNT2", "Blue", True, "Padrão"),
      ("Redragon", "Karura", "ABNT2", "Outemu Red", True, "Compacto"),
      ("Logitech", "G413", "ABNT2", "Romer-G", True, "Padrão"),
      ("HyperX", "Alloy Origins Core", "ABNT2", "Red", True, "Compacto"),
      ("Motospeed", "CK62", "ABNT2", "Outemu Red", True, "Compacto"),
      ("Redragon", "Draconic K530", "ABNT2", "Outemu Brown", True, "Compacto"),
      ("Logitech", "G Pro X", "ABNT2", "GX Blue", True, "Compacto"),
      ("HyperX", "Alloy FPS Pro", "ABNT2", "Red", True, "Compacto"),
      ("Razer", "Huntsman Elite", "ABNT2", "Óptico Linear", True, "Padrão"),
      ("Corsair", "K70 RGB Pro", "ABNT2", "Cherry MX Red", True, "Padrão"),
      ("Fortrek", "Black PRO", "ABNT2", None, False, "Padrão"),
      ("Redragon", "Anivia K614", "ABNT2", None, False, "Padrão"),
      ("Logitech", "K120", "ABNT2", None, False, "Padrão"),
      ("HyperX", "Alloy Elite 2", "ABNT2", "Red", True, "Padrão"),
      ("Motospeed", "K82", "ABNT2", "Outemu Blue", True, "Padrão"),
      ("Redragon", "Kumara K552-RGB", "ABNT2", "Outemu Blue", True, "Padrão"),
      ("Vinik", "VX Gamer Scorpion", "ABNT2", None, False, "Padrão"),
      ("C3Tech", "KG-11BSI", "ABNT2", None, False, "Padrão"),
      ("Multilaser", "Warrior TC240", "ABNT2", None, False, "Padrão"),
      ("Razer", "BlackWidow V3", "ABNT2", "Green", True, "Padrão"),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 2.5,
        "preco": self._preco(indice, 350, 60),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "conexao": "USB",
        "iluminacao": mecanico,
        "layout": layout,
        "switch": switch,
        "mecanico": mecanico,
        "tamanho": tamanho,
      }
      for indice, (
        fabricante, modelo, layout, switch, mecanico, tamanho,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-KEYB-{indice:02d}"]
    ]

  def _mouses(self) -> list[dict]:
    base = [
      ("Logitech", "G203", 8000, 6, "Óptico"),
      ("Redragon", "Cobra", 10000, 7, "Óptico"),
      ("Razer", "DeathAdder Essential", 6400, 5, "Óptico"),
      ("HyperX", "Pulsefire Core", 6200, 7, "Óptico"),
      ("Corsair", "Harpoon RGB", 6000, 6, "Óptico"),
      ("Fortrek", "Vickers", 3200, 6, "Óptico"),
      ("Logitech", "G502 Hero", 25600, 11, "Óptico"),
      ("Razer", "Viper Mini", 8500, 6, "Óptico"),
      ("Redragon", "Ranger", 12400, 7, "Óptico"),
      ("Pichau", "Nyx", 10000, 6, "Óptico"),
      ("Logitech", "G102 Lightsync", 8000, 6, "Óptico"),
      ("Logitech", "G305", 12000, 6, "Óptico"),
      ("Redragon", "Griffin", 7200, 7, "Óptico"),
      ("Redragon", "Centrophorus", 7200, 7, "Óptico"),
      ("Razer", "Basilisk V3", 26000, 11, "Óptico"),
      ("HyperX", "Pulsefire Haste", 16000, 6, "Óptico"),
      ("Corsair", "Katar Pro", 12400, 6, "Óptico"),
      ("Corsair", "M65 RGB Elite", 18000, 8, "Óptico"),
      ("Fortrek", "Black", 3200, 6, "Óptico"),
      ("Logitech", "G Pro X Superlight", 25600, 5, "Óptico"),
      ("Razer", "Viper 8K", 20000, 8, "Óptico"),
      ("Pichau", "Zeus", 8000, 6, "Óptico"),
      ("Havit", "MS1001", 4800, 6, "Óptico"),
      ("Xtrike Me", "GM-215", 3200, 6, "Óptico"),
      ("Vinik", "Mouse Gamer VX", 3200, 6, "Óptico"),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 1.0,
        "preco": self._preco(indice, 250, 40),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "conexao": "USB",
        "iluminacao": True,
        "dpi_max": dpi_max,
        "botoes": botoes,
        "sensor": sensor,
      }
      for indice, (
        fabricante, modelo, dpi_max, botoes, sensor,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-MOUSE-{indice:02d}"]
    ]

  def _monitores(self) -> list[dict]:
    base = [
      ("AOC", "24G2", 23.8, "1920x1080", 144, "IPS", 1.0, False),
      ("LG", "24MP400", 23.8, "1920x1080", 75, "IPS", 5.0, False),
      ("Samsung", "T350", 24.0, "1920x1080", 75, "VA", 4.0, False),
      ("AOC", "27G2", 27.0, "1920x1080", 144, "IPS", 1.0, False),
      ("LG", "27GN800", 27.0, "2560x1440", 144, "IPS", 1.0, False),
      ("Dell", "S2721DGF", 27.0, "2560x1440", 165, "IPS", 1.0, False),
      ("Samsung", "Odyssey G5", 27.0, "2560x1440", 144, "VA", 1.0, True),
      ("LG", "UltraGear 24GQ50", 23.8, "1920x1080", 165, "VA", 1.0, False),
      ("BenQ", "GW2480", 23.8, "1920x1080", 60, "IPS", 5.0, False),
      ("AOC", "Q27G3XMN", 27.0, "2560x1440", 165, "VA", 1.0, True),
      ("AOC", "22B2H", 21.5, "1920x1080", 75, "VA", 4.0, False),
      ("LG", "22MK400H", 21.5, "1920x1080", 75, "VA", 5.0, False),
      ("Samsung", "LS24C310", 24.0, "1920x1080", 100, "VA", 4.0, False),
      ("LG", "24GQ50F", 23.8, "1920x1080", 165, "VA", 1.0, False),
      ("Dell", "E2724HS", 27.0, "1920x1080", 75, "IPS", 5.0, False),
      ("AOC", "24G4", 23.8, "1920x1080", 180, "IPS", 1.0, False),
      ("Samsung", "Odyssey G3", 24.0, "1920x1080", 165, "VA", 1.0, False),
      ("LG", "UltraGear 27GP850", 27.0, "2560x1440", 165, "Nano IPS", 1.0, True),
      ("BenQ", "Mobiuz EX2710", 27.0, "1920x1080", 165, "IPS", 1.0, True),
      ("AOC", "Hero 27G4", 27.0, "1920x1080", 180, "IPS", 1.0, False),
      ("Gigabyte", "G27F", 27.0, "1920x1080", 165, "IPS", 1.0, False),
      ("Samsung", "Odyssey G7", 27.0, "2560x1440", 240, "VA", 1.0, True),
      ("LG", "UltraGear 32GP850", 32.0, "2560x1440", 165, "Nano IPS", 1.0, True),
      ("Dell", "S3222DGM", 32.0, "2560x1440", 165, "VA", 2.0, True),
      ("Pichau", "Athena 24", 23.8, "1920x1080", 100, "VA", 4.0, False),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 25.0,
        "preco": self._preco(indice, 1200, 250),
        "part_number": part_number,
        "link": LINKS_KABUM.get(part_number) or _link_busca_kabum(fabricante, modelo),
        "conexao": "HDMI/DP",
        "iluminacao": False,
        "tamanho_polegadas": tamanho_polegadas,
        "resolucao": resolucao,
        "taxa_atualizacao_hz": taxa_atualizacao,
        "tipo_painel": tipo_painel,
        "tempo_resposta_ms": tempo_resposta,
        "hdr": hdr,
      }
      for indice, (
        fabricante, modelo, tamanho_polegadas, resolucao, taxa_atualizacao,
        tipo_painel, tempo_resposta, hdr,
      ) in enumerate(base, start=1)
      for part_number in [f"SEED-MONITOR-{indice:02d}"]
    ]

  @staticmethod
  def _preco(indice: int, base: float, passo: float) -> float:
    return round(base + (indice - 1) * passo, 2)
