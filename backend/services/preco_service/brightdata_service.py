import os

import requests


class ColetaPendenteError(Exception):
    def __init__(self, snapshot_id):
        self.snapshot_id = snapshot_id
        super().__init__("Coleta ainda em processamento na Bright Data")


class BrightDataService:
    URL = "https://api.brightdata.com/datasets/v3"
    DATASET_MELI = "gd_m7re62tb1w88ymy86r"

    def executar(self, url: str, snapshot_id: str | None = None):
        chave = os.getenv("BRIGHTDATA_API_KEY", "").strip()
        if not chave:
            raise ValueError("Configure BRIGHTDATA_API_KEY no backend/.env")
        headers = {"Authorization": f"Bearer {chave}"}
        if snapshot_id:
            return self._obter_snapshot(snapshot_id, headers)
        # Não repetir POST automaticamente: um timeout pode já ter iniciado a coleta.
        response = requests.post(
            f"{self.URL}/scrape", headers=headers,
            params={"dataset_id": self.DATASET_MELI, "format": "json", "include_errors": "true"},
            json={"input": [{"url": url}], "limit_per_input": 1}, timeout=(10, 90),
        )
        response.raise_for_status()
        dados = response.json()
        if response.status_code == 202:
            if not isinstance(dados, dict) or not dados.get("snapshot_id"):
                raise ValueError("Bright Data retornou 202 sem snapshot_id")
            raise ColetaPendenteError(dados["snapshot_id"])
        return self._obter_registro(dados)

    def _obter_snapshot(self, snapshot_id, headers):
        response = requests.get(f"{self.URL}/progress/{snapshot_id}", headers=headers, timeout=(10, 30))
        response.raise_for_status()
        status = response.json().get("status")
        if status in {"starting", "running"}:
            raise ColetaPendenteError(snapshot_id)
        if status != "ready":
            raise ValueError("A coleta da Bright Data falhou ou retornou estado inesperado")
        response = requests.get(
            f"{self.URL}/snapshot/{snapshot_id}", headers=headers,
            params={"format": "json"}, timeout=(10, 60),
        )
        response.raise_for_status()
        if response.status_code == 202:
            raise ColetaPendenteError(snapshot_id)
        return self._obter_registro(response.json())

    def _obter_registro(self, dados):
        if not isinstance(dados, list) or len(dados) != 1 or not isinstance(dados[0], dict):
            raise ValueError("Esperado exatamente um produto na resposta da Bright Data")
        if dados[0].get("error") or dados[0].get("error_code"):
            raise ValueError("A Bright Data não conseguiu coletar este produto")
        return dados[0]
