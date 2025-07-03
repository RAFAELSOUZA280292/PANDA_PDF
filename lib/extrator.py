import os
import openai
import pandas as pd
from PyPDF2 import PdfReader

# Cria o cliente OpenAI usando a chave da variável de ambiente
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Prompt de instruções fixo
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

    todos_dados = []

    for arquivo in arquivos:
        try:
            caminho_pdf = os.path.join(pasta_temp, arquivo)
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
            df = markdown_para_dataframe(conteudo)
            todos_dados.append(df)
        
        except Exception as e:
            # Em caso de erro, adiciona linha com erro no DataFrame
            todos_dados.append(pd.DataFrame([{
                "TÍTULO": f"Erro no arquivo: {arquivo}",
                "AUTOR": "",
                "E-MAIL": f"{str(e)}"
            }]))

    return pd.concat(todos_dados, ignore_index=True)

def markdown_para_dataframe(tabela_markdown: str) -> pd.DataFrame:
    linhas = tabela_markdown.strip().split("\n")
    linhas = [l for l in linhas if "|" in l]
    
    dados = []
    for linha in linhas[2:]:  # pula cabeçalho e separador
        partes = [parte.strip() for parte in linha.split("|")[1:-1]]
        if len(partes) == 3:
            dados.append(partes)

    return pd.DataFrame(dados, columns=["TÍTULO", "AUTOR", "E-MAIL"])
