import os
import openai
import dotenv
import pandas as pd
from PyPDF2 import PdfReader
import requests

# Carrega a chave da API do arquivo .env (local) ou do ambiente Streamlit
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=api_key)

PROMPT_BASE = """
Você é a IA PANDA, especializada em extrair informações de artigos científicos. 
Sua função é ler o texto de um artigo científico e devolver uma tabela com três colunas:
TÍTULO | AUTOR | E-MAIL

Regras:
- Cada linha da tabela deve conter o título do artigo (repetido se houver vários autores), 
  o nome de um autor e o e-mail correspondente (ou em branco, se não houver).
- Nunca invente, complete ou interprete nomes ou e-mails.
- Se o título estiver em inglês e também houver uma versão em português, use o em português.
- A resposta deve ser sempre uma tabela legível em Markdown.
"""

def extrair_texto_pdf(caminho_pdf: str, max_paginas: int = 3) -> str:
    leitor = PdfReader(caminho_pdf)
    texto = ""
    for i, pagina in enumerate(leitor.pages):
        if i >= max_paginas:
            break
        texto += pagina.extract_text() or ""
    return texto.strip()

def processar_pdfs(pasta_temp: str) -> pd.DataFrame:
    arquivos = [f for f in os.listdir(pasta_temp) if f.endswith(".pdf")]
    if not arquivos:
        raise Exception("Nenhum PDF encontrado na pasta temporária.")

    caminho_pdf = os.path.join(pasta_temp, arquivos[0])
    texto = extrair_texto_pdf(caminho_pdf)

    if not texto:
        return pd.DataFrame([{
            "TÍTULO": "Erro no arquivo",
            "AUTOR": "",
            "E-MAIL": "PDF sem texto extraível"
        }])

    prompt = PROMPT_BASE + f"\n\nTexto do artigo:\n'''{texto}'''\n\nResponda somente com a tabela."

    try:
        resposta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em dados científicos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        conteudo = resposta.choices[0].message.content
        return markdown_para_dataframe(conteudo)

    except Exception as e:
        return pd.DataFrame([{
            "TÍTULO": "Erro no arquivo",
            "AUTOR": "",
            "E-MAIL": str(e)
        }])

def markdown_para_dataframe(tabela_markdown: str) -> pd.DataFrame:
    linhas = tabela_markdown.strip().split("\n")
    linhas = [l for l in linhas if "|" in l]

    dados = []
    for linha in linhas[2:]:  # pula cabeçalho e separador
        partes = [parte.strip() for parte in linha.split("|")[1:-1]]
        if len(partes) == 3:
            dados.append(partes)

    return pd.DataFrame(dados, columns=["TÍTULO", "AUTOR", "E-MAIL"])

def obter_saldo_usado() -> float:
    """Consulta o uso de créditos da API da OpenAI (sem consumir tokens)."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
        }
        response = requests.get(
            "https://api.openai.com/v1/dashboard/billing/usage",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            return float(data.get("total_usage", 0)) / 100.0  # vem em centavos
    except Exception:
        pass
    return 0.0
