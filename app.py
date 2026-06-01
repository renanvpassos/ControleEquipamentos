import streamlit as st
from database import supabase
from datetime import date

st.set_page_config(page_title="Controle Equipamentos", layout="wide")

# Lógica de Login/Cadastro (Autenticação do Supabase)
if "user" not in st.session_state:
    tab1, tab2 = st.tabs(["Login", "Cadastro"])
    with tab1:
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.error("Erro no login")
    # Adicionar lógica de Reset de Senha via supabase.auth.reset_password_email(email)
    st.stop()

# --- Menu Lateral ---
st.sidebar.write(f"Usuário: {st.session_state.user.email}")
menu = st.sidebar.radio("Menu", ["Equipamentos", "Manutenção Equipamentos", "Baixas", "Log"])

# --- Lógica do Menu Equipamentos ---
if menu == "Equipamentos":
    st.subheader("Lista de Equipamentos")
    data = supabase.table("equipamentos").select("*").execute()
    st.dataframe(data.data)

# --- Lógica de Manutenção ---
elif menu == "Manutenção Equipamentos":
    sub_op = st.radio("Ação", ["Adicionar", "Editar"])
    
    if sub_op == "Adicionar":
        with st.form("form_add"):
            nome = st.text_input("Nome")
            # ... outros campos ...
            if st.form_submit_button("Salvar"):
                # Verificar se o código já existe
                # Inserir no Supabase
                st.success("Salvo com sucesso!")
                # Registrar log
