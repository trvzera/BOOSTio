from services.scapring_service.buscar_dados_scapring_service import BuscarDadosScapringService

url = "https://www.kabum.com.br/produto/636960/console-playstation-5-pro-sony-ssd-2tb-com-controle-sem-fio-dualsense-branco-1000046552"

service = BuscarDadosScapringService()
preco = service.executar(url)

print(preco)