import streamlit as st

st.set_page_config(page_title="PANDA_PDF", layout="centered")

SENHA = "rosa123"

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🐼 PANDA_PDF - Login")
    senha = st.text_input("Digite a senha para acessar:", type="password")

    st.write(f"Senha digitada (para debug): '{senha}'")  # Para mostrar espaços ou caracteres invisíveis

    if st.button("Entrar"):
        if senha == SENHA:
            st.session_state.logado = True
            st.experimental_rerun()
        else:
            st.error("Senha incorreta! Tente novamente.")
    st.stop()

st.title("🐼 PANDA_PDF - App Principal")
st.write("Se você está vendo isso, fez login com sucesso!")
