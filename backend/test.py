from services.scapring_service.buscar_dados_scapring_service import BuscarDadosScapringService

url = "https://www.kabum.com.br/produto/725947/placa-de-video-xfx-swift-rx-9070-xt-triple-fan-gaming-edition-with-amd-radeon-16gb-gddr6-hdmi-3xdp-rdna-4-rx-97tswf3b9"

service = BuscarDadosScapringService()
preco = service.executar(url)

print(preco)