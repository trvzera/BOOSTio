import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("BRIGHTDATA_API_KEY", "").strip()
if not api_key:
    raise ValueError("Configure BRIGHTDATA_API_KEY no .env")

url_produto = (
    "https://www.mercadolivre.com.br/"
    "placa-de-video-geforce-nvidia-palit-rtx3050-6gb-stormx-gddr6/"
    "p/MLB64959148?pdp_filters=item_id:MLB4771805087"
)

response = requests.post(
    "https://api.brightdata.com/datasets/v3/scrape",
    params={
        "dataset_id": "gd_m7re62tb1w88ymy86r",
        "notify": "false",
        "include_errors": "true",
        "format": "json",
    },
    headers={"Authorization": f"Bearer {api_key}"},
    json={"input": [{"url": url_produto}]},
    timeout=(10, 90),
)

print("HTTP:", response.status_code)
print(response.text)
response.raise_for_status()