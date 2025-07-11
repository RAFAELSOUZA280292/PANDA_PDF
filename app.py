import streamlit as st
import pandas as pd
import tempfile
import os
from lib import extrator
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="PANDA_PDF", layout="centered")

# ----- Login simples -----
senha_correta = st.secrets.get("SENHA_APP", "Luna_Pipoca")

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 PANDA_PDF - Login")
    with st.form("login_form"):
        senha = st.text_input("Digite a senha para acessar:", type="password")
        if st.form_submit_button("Entrar"):
            if senha == senha_correta:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Senha incorreta! Tente novamente.")
    st.stop()

# Estado inicial da extração
if "extraction_results" not in st.session_state:
    st.session_state.extraction_results = None

# Interface principal
st.title("🐼 PANDA_PDF - Extração com IA")

if st.session_state.extraction_results is None:
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
            tokens_total = 0
            custo_total_usd = 0.0
            progresso = st.progress(0, text="Iniciando...")
            total = len(uploaded_files)

            with st.spinner("🔍 Extraindo informações dos PDFs..."):
                lotes = [uploaded_files[i:i+50] for i in range(0, total, 50)]
                atual = 0

                for idx, lote in enumerate(lotes):
                    st.info(f"📦 Processando lote {idx+1} de {len(lotes)} ({len(lote)} arquivos)")
                    for file in lote:
                        atual += 1
                        try:
                            with tempfile.TemporaryDirectory() as tempdir:
                                caminho_pdf = os.path.join(tempdir, file.name)
                                with open(caminho_pdf, "wb") as f:
                                    f.write(file.read())

                                df_parcial, tokens_usados = extrator.processar_pdfs(tempdir)
                                tokens_total += tokens_usados
                                custo_total_usd += (tokens_usados / 1000) * 0.0015

                                if not df_parcial.empty and "Erro no arquivo" in df_parcial["TÍTULO"].iloc[0]:
                                    erros.append({"arquivo": file.name, "erro": df_parcial["E-MAIL"].iloc[0]})
                                else:
                                    resultados.append(df_parcial)
                        except Exception as e:
                            erros.append({"arquivo": file.name, "erro": str(e)})

                        progresso.progress(atual / total, text=f"Processando {atual} de {total} PDFs")

            df_final = pd.concat(resultados, ignore_index=True) if resultados else pd.DataFrame()
            st.session_state.extraction_results = {
                "df_final": df_final,
                "erros": erros,
                "uploaded_count": total,
                "tokens_total": tokens_total,
                "custo_usd": round(custo_total_usd, 4)
            }
            st.rerun()
else:
    results = st.session_state.extraction_results
    df_final = results["df_final"]
    erros = results["erros"]
    uploaded_count = results["uploaded_count"]
    tokens_total = results["tokens_total"]
    custo_usd = results["custo_usd"]

    st.success("✅ Extração finalizada!")

    st.markdown("---")
    st.markdown(
        f"**📊 Resumo da Extração:**\n- Total de PDFs enviados: **{uploaded_count}**\n- Total de Autores/E-mails extraídos: **{len(df_final)}**"
    )
    if erros:
        st.warning(f"⚠️ {len(erros)} arquivo(s) tiveram erro durante a extração.")
    st.markdown("---")

    custo_reais = custo_usd * 6
    custo_por_email = (custo_reais / len(df_final)) if not df_final.empty else 0

    custo_usd_fmt = f"{custo_usd:.4f}"
    custo_reais_fmt = f"{custo_reais:.2f}".replace(".", ",")
    custo_por_email_fmt = f"{custo_por_email:.2f}".replace(".", ",")

    st.markdown(f"""
    💰 **Consumo da API OpenAI:**

    - Tokens usados: `{tokens_total}`
    - Custo estimado: ≈ USD {custo_usd_fmt}  ⇒  R$ {custo_reais_fmt}
    - Custo médio por e-mail: R$ {custo_por_email_fmt}
    """)

    if not df_final.empty or erros:
        now = datetime.now().strftime("%d.%m.%Y_%H.%M")
        nome_arquivo = f"Panda_PDF_{now}.xlsx"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            with pd.ExcelWriter(tmp.name, engine="xlsxwriter") as writer:
                if not df_final.empty:
                    df_final.to_excel(writer, index=False, sheet_name="dados")
                if erros:
                    pd.DataFrame(erros).to_excel(writer, index=False, sheet_name="erros")

            with open(tmp.name, "rb") as f_excel:
                st.download_button(
                    "💾 Baixar Excel",
                    data=f_excel.read(),
                    file_name=nome_arquivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_button"
                )

    if st.button("➕ Novo Upload", key="new_upload_button"):
        st.session_state.extraction_results = None
        st.rerun()
