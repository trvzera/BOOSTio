from services.scapring_service.buscar_dados_scapring_service import BuscarDadosScapringService

url = "https://www.terabyteshop.com.br/produto/25610/microfone-gamer-fifine-superframe-edition-sfm1-rgb-usb-black-com-braco-articulado"

service = BuscarDadosScapringService()
preco = service.executar(url)

print(preco)