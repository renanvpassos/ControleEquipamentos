import streamlit as st
from supabase import create_client
from datetime import date

# --- Configuração Supabase ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- Sistema de Login/Cadastro ---
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    choice = st.radio("Acesso", ["Login", "Cadastro"])
    if choice == "Login":
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            try:
                auth = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = auth.user
                st.rerun()
            except Exception as e:
                st.error("Erro: Verifique e-mail ou senha.")
    else:
        # Lógica de Cadastro
        email = st.text_input("E-mail para cadastro")
        senha = st.text_input("Senha", type="password")
        if st.button("Criar Conta"):
            supabase.auth.sign_up({"email": email, "password": senha})
            st.info("Verifique seu e-mail para confirmar o cadastro.")
    st.stop()

# --- Menu Lateral ---
st.sidebar.title("Gerenciamento")
st.sidebar.write(f"**Usuário:** {st.session_state.user.email}")

menu = st.sidebar.radio("Navegação", [
    "Equipamentos", "Manutenção Equipamentos", "Baixas", "Log"
])

# --- Funções de Log ---
def registrar_log(acao, resumo):
    supabase.table("logs").insert({
        "usuario_email": st.session_state.user.email,
        "acao": acao,
        "resumo": resumo
    }).execute()

# --- Lógica por Menu ---
if menu == "Equipamentos":
    st.header("Equipamentos")
    data = supabase.table("equipamentos").select("*").execute()
    st.dataframe(data.data)

elif menu == "Manutenção Equipamentos":
    st.header("Manutenção")
    sub_menu = st.radio("Ação", ["Adicionar Novo", "Editar/Excluir"])
    
    if sub_menu == "Adicionar Novo":
        with st.form("add_form"):
            # Campos conforme solicitado
            codigo = st.text_input("Código Controle Mult (Obrigatório)")
            nome = st.text_input("Nome do Equipamento")
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            serial = st.text_input("Número de Série")
            descricao = st.text_area("Descrição")
            colaborador = st.text_input("Colaborador que irá utilizar")
            
            # Data de registro fixa (apenas visualização)
            data_hoje = date.today().strftime("%d/%m/%Y")
            st.text(f"Data de Registro: {data_hoje}")
            
            # Validação de baixa prévia
            if codigo:
                existe = supabase.table("equipamentos").select("status, motivo_baixa").eq("codigo_controle", codigo).execute()
                if existe.data and existe.data[0]['status'] == 'Baixado':
                    st.error(f"⚠️ Equipamento baixado! Motivo: {existe.data[0]['motivo_baixa']}")
                    st.warning("Este equipamento não pode ser cadastrado novamente.")
            
            if st.form_submit_button("Salvar Cadastro"):
                if not codigo or not nome:
                    st.error("Preencha os campos obrigatórios!")
                else:
                    try:
                        supabase.table("equipamentos").insert({
                            "codigo_controle": codigo,
                            "nome": nome,
                            "marca": marca,
                            "modelo": modelo,
                            "serial_number": serial,
                            "descricao": descricao,
                            "colaborador": colaborador,
                            "data_registro": date.today().isoformat(),
                            "status": "Ativo"
                        }).execute()
                        
                        registrar_log("Adicionar", f"Novo equipamento cadastrado: {codigo} - {nome}")
                        st.success("Cadastro realizado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

elif menu == "Baixas":
    st.header("Baixa de Equipamento")
    codigo = st.text_input("Código Controle Mult para Baixa")
    # Busca e exibe dados...
    motivo = st.text_area("Motivo da Baixa (mín. 5 caracteres)")
    if len(motivo) >= 5:
        if st.button("Confirmar Baixa"):
            supabase.table("equipamentos").update({"status": "Baixado", "motivo_baixa": motivo}).eq("codigo_controle", codigo).execute()
            registrar_log("Baixa", f"Equipamento {codigo} baixado.")
            st.rerun()

elif menu == "Log":
    st.header("Log de Alterações")
    logs = supabase.table("logs").select("*").order("created_at", desc=True).execute()
    st.table(logs.data)
