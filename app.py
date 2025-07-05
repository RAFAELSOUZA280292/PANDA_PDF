import streamlit as st
import pandas as pd
import tempfile
import os
from lib import extrator

# 1. Configuração da Página do Streamlit
st.set_page_config(page_title="PANDA_PDF", layout="centered")

# --- Lógica de Autenticação ---
senha_correta = st.secrets.get("SENHA_APP", "Luna_Pipoca") 

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
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
st.title("🐼 PANDA_PDF - Extração com Inteligência Artificial")

# Inicializa o estado para armazenar os resultados da extração
# Isso permite que os resultados e botões pós-extração persistam entre reruns
if "extraction_results" not in st.session_state:
    st.session_state.extraction_results = None

# Mostra o uploader de arquivos e o botão "Iniciar Extração"
# APENAS se não houver resultados pendentes da extração anterior
if st.session_state.extraction_results is None:
    uploaded_files = st.file_uploader(
        "Selecione até 100 arquivos PDF",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files: # Este bloco só aparece se arquivos foram carregados
        if len(uploaded_files) > 100:
            st.warning("⚠️ Apenas os 100 primeiros arquivos serão processados.")
            uploaded_files = uploaded_files[:100]

        st.markdown(f"📁 {len(uploaded_files)} arquivos PDF selecionados.")
        st.markdown(
            '<span style="color:hotpink">🐵 Agora é só apertar o botão e iniciar a extração 🚀</span>',
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

            # Armazena os resultados no session_state e força um rerun para exibir
            st.session_state.extraction_results = {
                "df_final": df_final,
                "erros": erros,
                "uploaded_count": len(uploaded_files) # Armazena a contagem inicial de PDFs enviados
            }
            st.rerun() # Reinicia o script para mostrar os resultados
else: # Este bloco é executado SE houver resultados de extração armazenados no session_state
    # Recupera os resultados do session_state
    results = st.session_state.extraction_results
    df_final = results["df_final"]
    erros = results["erros"]
    uploaded_count = results["uploaded_count"]

    st.success("✅ Extração finalizada!")
    
    # Resumo do contador de extrações
    num_extracted_rows = 0
    if not df_final.empty:
        num_extracted_rows = len(df_final)

    st.markdown("---") 
    st.markdown(
        f"**📊 Resumo da Extração:**"
        f"\n- Total de PDFs enviados: **{uploaded_count}**" # Usa a contagem armazenada
        f"\n- Total de Autores/E-mails extraídos: **{num_extracted_rows}**"
    )
    if erros:
        st.warning(f"⚠️ {len(erros)} arquivo(s) PDF tiveram erros durante a extração.")
    st.markdown("---")

    # Botão de download do Excel (agora persistente)
    if not df_final.empty or erros: # Só mostra o download se houver dados ou erros
        # A cada rerun, o arquivo temporário precisa ser recriado para o download_button
        excel_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                excel_file_path = tmp.name
                with pd.ExcelWriter(excel_file_path, engine="xlsxwriter") as writer:
                    if not df_final.empty:
                        df_final.to_excel(writer, index=False, sheet_name="dados")
                    if erros:
                        pd.DataFrame(erros).to_excel(writer, index=False, sheet_name="erros")
            
            with open(excel_file_path, "rb") as f_excel:
                st.download_button(
                    "💾 Baixar Excel",
                    data=f_excel.read(), # Lê o conteúdo do arquivo para passar como bytes
                    file_name="resultado_panda_pdf.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", # Tipo MIME para Excel
                    key="download_excel_button" # Chave para identificar o widget
                )
        finally:
            # Garante que o arquivo temporário seja removido, mesmo se houver erro no download
            if excel_file_path and os.path.exists(excel_file_path):
                os.unlink(excel_file_path)

    # Botão "Novo Upload" (agora persistente)
    st.markdown("---")
    if st.button("➕ Novo Upload", key="new_upload_button"): # Chave para identificar o widget
        # Limpa o estado dos resultados da extração para voltar à tela inicial de upload
        st.session_state.extraction_results = None
        st.rerun() # Reinicia o script para mostrar o uploader de arquivos
