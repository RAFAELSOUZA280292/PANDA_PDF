import streamlit as st
import pandas as pd
import tempfile
import os
from lib import extrator

# 1. Configuração da Página do Streamlit
st.set_page_config(page_title="PANDA_PDF", layout="centered")

# --- Lógica de Autenticação ---
# Gerenciamento de Senha (USAR st.secrets EM PRODUÇÃO!)
# No arquivo .streamlit/secrets.toml no seu repositório, adicione:
# SENHA_APP = "sua_senha_segura_aqui"
senha_correta = st.secrets.get("SENHA_APP", "Luna_Pipoca") 

# Gerenciamento de Estado da Sessão para Login
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# Bloco de Controle de Acesso (Login)
if not st.session_state["logado"]:
    # Melhoria 1: Título com EMOJI para a página de login
    st.title("🔑 PANDA_PDF - Login")
    
    with st.form("login_form"):
        senha_digitada = st.text_input("Digite a senha para acessar:", type="password")
        submitted = st.form_submit_button("Entrar")
    
    if submitted:
        if senha_digitada == senha_correta:
            st.session_state["logado"] = True
            st.rerun() 
        else:
            st.error("Senha incorreta! Tente novamente.")
    st.stop() 

# --- APP PRINCIPAL (Só será executado se o usuário estiver logado) ---
# Melhoria 2: Título principal alterado após login
st.title("🐼 PANDA_PDF - Extração com Inteligência Artificial")

uploaded_files = st.file_uploader(
    "Selecione até 100 arquivos PDF",
    type="pdf",
    accept_multiple_files=True
)

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

        progresso = st.progress(0, text="Iniciando...")
        total = len(uploaded_files)

        with st.spinner("🔍 Extraindo informações dos PDFs..."):
            for i, file in enumerate(uploaded_files, 1):
                try:
                    with tempfile.TemporaryDirectory() as tempdir:
                        caminho_pdf = os.path.join(tempdir, file.name)
                        with open(caminho_pdf, "wb") as f:
                            f.write(file.read())

                        df_parcial = extrator.processar_pdfs(tempdir)

                        if not df_parcial.empty and "Erro no arquivo" in df_parcial["TÍTULO"].iloc[0]:
                            erros.append({
                                "arquivo": file.name,
                                "erro": df_parcial["E-MAIL"].iloc[0]
                            })
                        else:
                            resultados.append(df_parcial)
                except Exception as e:
                    erros.append({"arquivo": file.name, "erro": str(e)})

                progresso.progress(i / total, text=f"Processando {i} de {total} PDFs")

        df_final = pd.concat(resultados, ignore_index=True) if resultados else pd.DataFrame()

        st.success("✅ Extração finalizada!")
        
        # Melhoria 3: Resumo do contador de extrações
        num_extracted_rows = 0
        if not df_final.empty:
            num_extracted_rows = len(df_final)

        st.markdown("---") # Linha separadora para melhor visualização
        st.markdown(
            f"**📊 Resumo da Extração:**"
            f"\n- Total de PDFs enviados: **{len(uploaded_files)}**"
            f"\n- Total de Autores/E-mails extraídos: **{num_extracted_rows}**"
        )
        if erros:
            st.warning(f"⚠️ {len(erros)} arquivo(s) PDF tiveram erros durante a extração.")
        st.markdown("---") # Linha separadora para melhor visualização

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            with pd.ExcelWriter(tmp.name, engine="xlsxwriter") as writer:
                if not df_final.empty:
                    df_final.to_excel(writer, index=False, sheet_name="dados")
                if erros:
                    pd.DataFrame(erros).to_excel(writer, index=False, sheet_name="erros")
            st.download_button(
                "�� Baixar Excel",
                data=open(tmp.name, "rb"),
                file_name="resultado_panda_pdf.xlsx"
            )
            os.unlink(tmp.name) 
        
        # Melhoria 4: Botão "+ 100" para novo upload
        st.markdown("---") # Linha separadora para melhor visualização
        if st.button("➕ Novo Upload"): # Alterei para algo mais intuitivo que "+ 100"
            st.rerun() # Limpa o uploader e reinicia o fluxo para um novo upload
