import streamlit as st
import pandas as pd
import tempfile
import os
from lib import extrator

# 1. Configuração da Página do Streamlit
st.set_page_config(page_title="PANDA_PDF", layout="centered")

# --- Lógica de Autenticação ---
# 2. Gerenciamento de Senha (USAR st.secrets EM PRODUÇÃO!)
# Se você estiver rodando localmente e não tiver configurado st.secrets,
# pode usar uma senha hardcoded APENAS para testes LOCAIS.
# Em implantação no Streamlit Cloud, SEMPRE use st.secrets.
# Exemplo de uso de st.secrets:
# No arquivo .streamlit/secrets.toml no seu repositório:
# SENHA_APP = "sua_senha_segura_aqui"
# E no código:
senha_correta = st.secrets.get("SENHA_APP", "Luna_Pipoca") # "Luna_Pipoca" é um fallback para teste local, remova em produção!

# 3. Gerenciamento de Estado da Sessão para Login
# Verifica se a chave 'logado' existe no session_state. Se não, inicializa como False.
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# 4. Bloco de Controle de Acesso (Login)
# Se o usuário não estiver logado, exibe o formulário de login e interrompe a execução do restante do app.
if not st.session_state["logado"]:
    st.title("�� PANDA_PDF - Login")
    
    with st.form("login_form"):
        senha_digitada = st.text_input("Digite a senha para acessar:", type="password")
        submitted = st.form_submit_button("Entrar")
    
    if submitted:
        if senha_digitada == senha_correta:
            st.session_state["logado"] = True
            # st.rerun() é a forma oficial e estável de reiniciar o aplicativo após o login
            st.rerun() 
        else:
            st.error("Senha incorreta! Tente novamente.")
    st.stop() # Interrompe a execução aqui se o usuário não estiver logado

# --- APP PRINCIPAL (Só será executado se o usuário estiver logado) ---
# 5. Título Principal da Aplicação
st.title("🐼 PANDA_PDF - Extração com ChatGPT")

# 6. Carregador de Arquivos PDF
uploaded_files = st.file_uploader(
    "Selecione até 100 arquivos PDF",
    type="pdf",
    accept_multiple_files=True
)

# 7. Lógica de Processamento de Arquivos
if uploaded_files:
    if len(uploaded_files) > 100:
        st.warning("⚠️ Apenas os 100 primeiros arquivos serão processados.")
        uploaded_files = uploaded_files[:100]

    st.markdown(f"📁 {len(uploaded_files)} arquivos PDF selecionados.")
    st.markdown(
        '<span style="color:hotpink">🌸 Agora é só apertar o botão e iniciar a extração 🚀</span>',
        unsafe_allow_html=True
    )

    if st.button("🚀 Iniciar Extração"):
        resultados = []
        erros = []

        # 8. Barra de Progresso e Spinner
        progresso = st.progress(0, text="Iniciando...")
        total = len(uploaded_files)

        with st.spinner("🔍 Extraindo informações dos PDFs..."):
            for i, file in enumerate(uploaded_files, 1):
                try:
                    # 9. Gerenciamento de Arquivos Temporários
                    with tempfile.TemporaryDirectory() as tempdir:
                        caminho_pdf = os.path.join(tempdir, file.name)
                        with open(caminho_pdf, "wb") as f:
                            f.write(file.read())

                        # 10. Chamada à Lógica de Extração (do extrator.py)
                        df_parcial = extrator.processar_pdfs(tempdir)

                        # 11. Verificação e Armazenamento de Resultados/Erros
                        # A condição df_parcial["TÍTULO"].iloc[0] verifica se o primeiro item da coluna 'TÍTULO'
                        # contém a string "Erro no arquivo", que é como o seu extrator sinaliza um erro.
                        if not df_parcial.empty and "Erro no arquivo" in df_parcial["TÍTULO"].iloc[0]:
                            erros.append({
                                "arquivo": file.name,
                                "erro": df_parcial["E-MAIL"].iloc[0] # A mensagem de erro é armazenada na coluna E-MAIL
                            })
                        else:
                            resultados.append(df_parcial)
                except Exception as e:
                    # Captura qualquer outra exceção durante o processamento do arquivo
                    erros.append({"arquivo": file.name, "erro": str(e)})

                # 12. Atualização da Barra de Progresso
                progresso.progress(i / total, text=f"Processando {i} de {total} PDFs")

        # 13. Concatenação dos Resultados Finais
        df_final = pd.concat(resultados, ignore_index=True) if resultados else pd.DataFrame()

        st.success("✅ Extração finalizada!")

        # 14. Geração e Download do Arquivo Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            with pd.ExcelWriter(tmp.name, engine="xlsxwriter") as writer:
                if not df_final.empty:
                    df_final.to_excel(writer, index=False, sheet_name="dados")
                if erros:
                    pd.DataFrame(erros).to_excel(writer, index=False, sheet_name="erros")
            st.download_button(
                "💾 Baixar Excel",
                data=open(tmp.name, "rb"),
                file_name="resultado_panda_pdf.xlsx"
            )
            os.unlink(tmp.name) # Limpa o arquivo temporário após o download
