import os
import openai
import dotenv
import pandas as pd
from PyPDF2 import PdfReader
import requests
from datetime import date

# Carrega a chave da API
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

# ... extrair_texto_pdf, processar_pdfs e markdown_para_dataframe como antes ...

def obter_saldo_usado() -> float:
    """
    Consulta o uso acumulado do dia corrente da API OpenAI (em USD).
    """
    try:
        hoje = date.today().isoformat()
        url = f"https://api.openai.com/v1/dashboard/billing/usage?start_date={hoje}&end_date={hoje}"
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            total = float(data.get("total_usage", 0)) / 100.0  # valor em centavos
            return total
    except Exception:
        pass
    return 0.0
