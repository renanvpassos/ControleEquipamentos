import streamlit as st
from supabase import create_client
from datetime import date

# --- Configuração Supabase ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

st.set_page_config(page_title="Gestão de Equipamentos", layout="wide")

# --- Lógica de Login/Cadastro ---
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    tab1, tab2 = st.tabs(["Login", "Cadastro"])
    with tab1:
        email = st.text_input("Email", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = res.user
                st.rerun()
            except Exception:
                st.error("Credenciais inválidas.")
        if st.button("Esqueci minha senha"):
            if email:
                supabase.auth.reset_password_email(email)
                st.info("Verifique seu e-mail para resetar a senha.")
    with tab2:
        c_email = st.text_input("Email", key="cad_email")
        c_senha = st.text_input("Senha", type="password", key="cad_pass")
        if st.button("Cadastrar"):
            supabase.auth.sign_up({"email": c_email, "password": c_senha})
            st.info("Confirmação enviada para o seu e-mail.")
    st.stop()

# --- Funções Auxiliares ---
def registrar_log(acao, resumo):
    supabase.table("logs").insert({
        "usuario_email": st.session_state.user.email,
        "acao": acao,
        "resumo": resumo
    }).execute()

# --- Menu Lateral ---
st.sidebar.title("Menu")
st.sidebar.info(f"Usuário: {st.session_state.user.email}")
menu = st.sidebar.radio("Navegação", ["Equipamentos", "Manutenção Equipamentos", "Baixas", "Log"])

# --- Conteúdo Principal ---
if menu == "Equipamentos":
    st.header("Lista de Equipamentos")
    data = supabase.table("equipamentos").select("*").execute()
    st.dataframe(data.data)

elif menu == "Manutenção Equipamentos":
    sub = st.radio("Ação", ["Adicionar Novo", "Editar/Excluir"])
    
    if sub == "Adicionar Novo":
        with st.form("add_form"):
            codigo = st.text_input("Código Controle Mult")
            nome = st.text_input("Nome")
            marca = st.text_input("Marca"); modelo = st.text_input("Modelo")
            serial = st.text_input("Número de série"); colab = st.text_input("Colaborador")
            desc = st.text_area("Descrição")
            st.text(f"Data de Registro: {date.today().strftime('%d/%m/%Y')}")
            
            if st.form_submit_button("Salvar Cadastro"):
                # Bloqueio de duplicidade de baixa
                check = supabase.table("equipamentos").select("id").eq("codigo_controle", codigo).eq("status", "Baixado").execute()
                if check.data:
                    st.error("Equipamento com este código foi dado em baixa e não pode ser re-cadastrado.")
                else:
                    supabase.table("equipamentos").insert({"codigo_controle": codigo, "nome": nome, "marca": marca, "modelo": modelo, "serial_number": serial, "colaborador": colab, "descricao": desc, "data_registro": str(date.today())}).execute()
                    registrar_log("Adicionar", f"Equipamento {codigo} cadastrado.")
                    st.success("Salvo!")

    elif sub == "Editar/Excluir":
        cod_busca = st.text_input("Digite o código para buscar:")
        if cod_busca:
            item = supabase.table("equipamentos").select("*").eq("codigo_controle", cod_busca).single().execute()
            if item.data:
                with st.form("edit_form"):
                    n_nome = st.text_input("Nome", value=item.data['nome'])
                    if st.form_submit_button("Salvar Alterações"):
                        supabase.table("equipamentos").update({"nome": n_nome}).eq("codigo_controle", cod_busca).execute()
                        registrar_log("Editar", f"Editado: {cod_busca}")
                    if st.form_submit_button("🗑️ Deletar"):
                        supabase.table("equipamentos").delete().eq("codigo_controle", cod_busca).execute()
                        registrar_log("Deletar", f"Excluído: {cod_busca}")

elif menu == "Baixas":
    st.header("Baixa de Equipamento")
    cod = st.text_input("Código Controle Mult")
    if cod:
        item = supabase.table("equipamentos").select("*").eq("codigo_controle", cod).eq("status", "Ativo").single().execute()
        if item.data:
            st.write(f"**Equipamento:** {item.data['nome']} | **Usuário:** {item.data['colaborador']}")
            motivo = st.text_area("Motivo da Baixa (min 5 caracteres)")
            if st.button("Confirmar Baixa") and len(motivo) >= 5:
                supabase.table("equipamentos").update({"status": "Baixado", "motivo_baixa": motivo}).eq("codigo_controle", cod).execute()
                registrar_log("Baixa", f"Baixa no {cod}: {motivo}")
                st.rerun()

elif menu == "Log":
    st.header("Logs do Sistema")
    logs = supabase.table("logs").select("*").order("created_at", desc=True).execute()
    st.table(logs.data)
