import streamlit as st
import pandas as pd
import tempfile
import os
from lib import extrator  # Seu extrator.py deve estar dentro da pasta lib/

st.set_page_config(page_title="PANDA_PDF", layout="centered")
st.title("🐼 PANDA_PDF - Extração com ChatGPT")

uploaded_files = st.file_uploader("Selecione até 100 arquivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) > 100:
        st.warning("⚠️ Apenas os 100 primeiros arquivos serão processados.")
        uploaded_files = uploaded_files[:100]

    st.markdown(f"📁 {len(uploaded_files)} arquivos PDF selecionados.")
    st.markdown('<span style="color:hotpink">🌸 Agora é só apertar o botão e iniciar a extração 🚀</span>', unsafe_allow_html=True)

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

                        # Verifica se houve erro no conteúdo
                        if "Erro no arquivo" in df_parcial["TÍTULO"].iloc[0]:
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

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            with pd.ExcelWriter(tmp.name, engine="xlsxwriter") as writer:
                if not df_final.empty:
                    df_final.to_excel(writer, index=False, sheet_name="dados")
                if erros:
                    pd.DataFrame(erros).to_excel(writer, index=False, sheet_name="erros")
            st.download_button("💾 Baixar Excel", data=open(tmp.name, "rb"), file_name="resultado_panda_pdf.xlsx")
