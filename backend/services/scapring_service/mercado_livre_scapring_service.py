import requests
import os
from dotenv import load_dotenv

load_dotenv()

class MercadoLivreScapringService:
    def executar(self, termo_busca: str):
        # URL oficial do Mercado Livre Brasil bem estruturada
        # /items/bulk?ids=ITEMID1,ITEM_ID2
        url = f"https://api.mercadolibre.com/items?ids=MLA599260060,MLA594239600"

        print(f"DEBUG - A URL QUE VAI SER CHAMADA É: {url}")
        
        headers = {
            "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN_KEY')}"
        } 
        
        try:
            resposta = requests.get(url, headers=headers)
            data = resposta.json()
            
            if "error" in data:
                print(f"Erro da API: {data.get('message')}")
                return None
                
            produtos = data.get("results")
            
            if produtos:
                for produto in produtos:
                    titulo = produto.get("title")
                    preco = produto.get("price")
                    link = produto.get("permalink")
                          
                    print(f"Produto: {titulo}")
                    print(f"Preço: R$ {preco}")
                    print(f"Link: {link}")
                    print("-" * 50)
            else:
                print("Nenhum produto encontrado para este termo.")
                
            return produtos

        except Exception as e:
            print(f"Ocorreu um erro na requisição: {e}")
            return None
