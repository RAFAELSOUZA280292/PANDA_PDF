import os
import openai
import dotenv
import pandas as pd
from PyPDF2 import PdfReader

# Carrega a chave da API do arquivo .env
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI()  # compatível com openai>=1.0.0

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

def extrair_texto_pdf(caminho_pdf: str) -> str:
    leitor = PdfReader(caminho_pdf)
    texto = ""
    for pagina in leitor.pages:
        texto += pagina.extract_text() or ""
    return texto.strip()

def processar_pdfs(pasta_temp: str) -> pd.DataFrame:
    arquivos = [f for f in os.listdir(pasta_temp) if f.endswith(".pdf")]
    if not arquivos:
        raise Exception("Nenhum PDF encontrado na pasta temporária.")

    caminho_pdf = os.path.join(pasta_temp, arquivos[0])
    texto = extrair_texto_pdf(caminho_pdf)

    prompt = PROMPT_BASE + f"\n\nTexto do artigo:\n'''{texto}'''\n\nResponda somente com a tabela."

    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um assistente especializado em dados científicos."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    conteudo = resposta.choices[0].message.content

    # Converte a tabela Markdown em DataFrame
    return markdown_para_dataframe(conteudo)

def markdown_para_dataframe(tabela_markdown: str) -> pd.DataFrame:
    linhas = tabela_markdown.strip().split("\n")
    linhas = [l for l in linhas if "|" in l]
    
    dados = []
    for linha in linhas[2:]:  # pula cabeçalho e separador
        partes = [parte.strip() for parte in linha.split("|")[1:-1]]
        if len(partes) == 3:
            dados.append(partes)

    return pd.DataFrame(dados, columns=["TÍTULO", "AUTOR", "E-MAIL"])
