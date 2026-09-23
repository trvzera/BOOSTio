from services.scapring_service.buscar_dados_scapring_service import BuscarDadosScapringService

url = "https://www.kabum.com.br/produto/398510/placa-mae-asus-prime-a520m-k-amd-am3-matx-ddr4-1500-m0eay0"

service = BuscarDadosScapringService()
preco = service.executar(url)

print(preco)