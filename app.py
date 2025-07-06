import streamlit as st
import pandas as pd
import tempfile
import os
from lib import extrator

# Configuração da Página
st.set_page_config(page_title="PANDA_PDF", layout="centered")

# --- Autenticação ---
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

# --- App Principal ---
st.title("🐼 PANDA_PDF - Extração com IA")

if "extraction_results" not in st.session_state:
    st.session_state.extraction_results = None

if st.session_state.extraction_results is None:
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
        st.markdown('<span style="color:hotpink">🌸 Agora é só apertar o botão e iniciar a extração 🚀</span>', unsafe_allow_html=True)

        if st.button("🚀 Iniciar Extração"):
            resultados = []
            erros = []
            progresso = st.progress(0, text="Iniciando extração...")
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

            st.session_state.extraction_results = {
                "df_final": df_final,
                "erros": erros,
                "uploaded_count": len(uploaded_files)
            }
            st.rerun()
else:
    results = st.session_state.extraction_results
    df_final = results["df_final"]
    erros = results["erros"]
    uploaded_count = results["uploaded_count"]

    st.success("✅ Extração finalizada!")

    num_extracted_rows = len(df_final) if not df_final.empty else 0

    st.markdown("---")
    st.markdown(
        f"**📊 Resumo da Extração:**"
        f"\n- PDFs enviados: **{uploaded_count}**"
        f"\n- Autores/e-mails extraídos: **{num_extracted_rows}**"
    )
    if erros:
        st.warning(f"⚠️ {len(erros)} arquivo(s) tiveram erro durante a extração.")
    st.markdown("---")

    if not df_final.empty or erros:
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
                    data=f_excel.read(),
                    file_name="resultado_panda_pdf.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_button"
                )
        finally:
            if excel_file_path and os.path.exists(excel_file_path):
                os.unlink(excel_file_path)

    st.markdown("---")
    if st.button("➕ Novo Upload", key="new_upload_button"):
        st.session_state.extraction_results = None
        st.rerun()
