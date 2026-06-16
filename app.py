import streamlit as st
from supabase import create_client
from datetime import date, datetime
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- Configuração Supabase ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

st.set_page_config(page_title="Gestão de Equipamentos", layout="wide")

# --- Lógica de Login/Cadastro ---
if "user" not in st.session_state:
    st.session_state.user = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

def get_user_role(user_id):
    try:
        # Busca o cargo do usuário na tabela 'perfis'
        res = supabase.table("perfis").select("cargo").eq("id", user_id).single().execute()
        if res.data:
            return res.data.get("cargo")
        return None
    except Exception:
        return None

if not st.session_state.user:
    tab1, tab2 = st.tabs(["Login", "Cadastro"])
    with tab1:
        email = st.text_input("Email", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = res.user
                st.session_state.user_role = get_user_role(res.user.id)
                st.rerun()
            except Exception:
                st.error("Credenciais inválidas.")
        if st.button("Esqueci minha senha"):
            if email:
                try:
                    supabase.auth.reset_password_email(email)
                    st.info("Verifique seu e-mail para resetar a senha.")
                except Exception as e:
                    st.error(f"Erro ao enviar e-mail: {e}")
    with tab2:
        c_email = st.text_input("Email", key="cad_email")
        c_senha = st.text_input("Senha", type="password", key="cad_pass")
        if st.button("Cadastrar"):
            try:
                res = supabase.auth.sign_up({"email": c_email, "password": c_senha})
                if res.user:
                    # Cria o perfil padrão com cargo 'Nenhum'
                    supabase.table("perfis").insert({
                        "id": res.user.id,
                        "email": c_email,
                        "cargo": "Nenhum"
                    }).execute()
                st.info("Confirmação enviada para o seu e-mail. Verifique sua caixa de entrada.")
            except Exception as e:
                st.error(f"Erro ao cadastrar: {e}")
    st.stop()

# --- Verificação de Permissão Bloqueante ---
if not st.session_state.user_role or st.session_state.user_role == "Nenhum":
    st.sidebar.title("Menu")
    st.sidebar.info(f"Usuário: {st.session_state.user.email}")
    st.sidebar.warning("Cargo: Nenhum")
    st.error("Você não possui permissões (Supervisor/Master) para acessar as funcionalidades do sistema. Solicite acesso ao administrador.")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.session_state.user_role = None
        st.rerun()
    st.stop()

# --- Funções Auxiliares de Log ---
def registrar_log(acao, resumo):
    supabase.table("logs").insert({
        "usuario_email": st.session_state.user.email,
        "acao": acao,
        "resumo": resumo
    }).execute()

# --- Funções de Geração de Arquivos (PDF e Excel) ---
def gerar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Equipamentos')
    return output.getvalue()

def gerar_pdf(df, titulo_relatorio="Relatório de Equipamentos"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor("#1A365D"), spaceAfter=20)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, leading=10)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, leading=11, textColor=colors.white, fontName="Helvetica-Bold")
    
    story.append(Paragraph(titulo_relatorio, title_style))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    colunas_pdf = ['codigo_controle', 'service_tag', 'tipo', 'marca', 'colaborador', 'status', 'data_registro']
    
    colunas_existentes = [c for c in colunas_pdf if c in df.columns]
    
    if len(colunas_existentes) < len(colunas_pdf):
        st.warning(f"Algumas colunas não foram encontradas: {set(colunas_pdf) - set(colunas_existentes)}")
        
    df_pdf = df[colunas_existentes].copy()
    
    table_data = [[Paragraph(col.upper(), header_style) for col in df_pdf.columns]]
    
    for _, row in df_pdf.iterrows():
        row_cells = []
        for val in row.values:
            row_cells.append(Paragraph(str(val) if pd.notnull(val) else "", cell_style))
        # CORREÇÃO: O append foi movido para fora do loop das colunas (recuo ajustado)
        table_data.append(row_cells)
    
    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t)
    doc.build(story)
    return buffer.getvalue()


# --- NOVA FUNÇÃO: GERA APENAS 1 PDF CONSOLIDADO COM 1 PAGINA POR COLABORADOR ---
def gerar_pdf_consolidado(df_ordenado, titulo_geral="Relatório Geral Consolidado de Equipamentos"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
    colab_style = ParagraphStyle('ColabStyle', parent=styles['Heading2'], fontSize=13, leading=16, textColor=colors.HexColor("#2C5282"), spaceBefore=10, spaceAfter=10)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, leading=10)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, leading=11, textColor=colors.white, fontName="Helvetica-Bold")
    
    # Colunas selecionadas para o PDF
    colunas_pdf = ['codigo_controle', 'service_tag', 'tipo', 'marca', 'status', 'data_registro']
    
    # Agrupa por colaborador sem alterar a ordenação alfabética prévia do Pandas
    grupos = list(df_ordenado.groupby('colaborador', sort=False))
    
    for i, (colaborador, group) in enumerate(grupos):
        # Título do Relatório Geral e metadados apenas na primeira página
        if i == 0:
            story.append(Paragraph(titulo_geral, title_style))
            story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 15))
            
        # Nome do Colaborador atual em destaque na página dele
        story.append(Paragraph(f"Colaborador: {colaborador}", colab_style))
        story.append(Spacer(1, 5))
        
        df_pdf = group[colunas_pdf].copy() if all(c in group.columns for c in colunas_pdf) else group.iloc[:, :6]
        
        # Monta a estrutura da tabela do colaborador
        table_data = [[Paragraph(col.upper(), header_style) for col in df_pdf.columns]]
        
        for _, row in df_pdf.iterrows():
            row_cells = []
            for val in row.values:
                row_cells.append(Paragraph(str(val) if pd.notnull(val) else "", cell_style))
            # CORREÇÃO: O append foi movido para fora do loop das colunas (recuo ajustado)
            table_data.append(row_cells)
            
        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t)
        
        # Se não for o último colaborador da lista, insere uma quebra de página
        if i < len(grupos) - 1:
            story.append(PageBreak())
            
    doc.build(story)
    return buffer.getvalue()


# --- Configuração Dinâmica de Menus baseada no Cargo ---
opcoes_menu = []
if st.session_state.user_role in ["Supervisor", "Master"]:
    opcoes_menu.append("Cadastrar Equipamento")
if st.session_state.user_role == "Master":
    opcoes_menu.append("Editar Cadastro")
if st.session_state.user_role in ["Supervisor", "Master"]:
    opcoes_menu.append("Lista de Equipamentos")
if st.session_state.user_role == "Master":
    opcoes_menu.append("Relatórios")
    opcoes_menu.append("Log de Atividades")

# --- Menu Lateral ---
st.sidebar.title("Menu")
st.sidebar.info(f"Usuário: {st.session_state.user.email}\n\nCargo: {st.session_state.user_role}")
menu = st.sidebar.radio("Navegação", opcoes_menu)

if st.sidebar.button("Sair do Sistema"):
    st.session_state.user = None
    st.session_state.user_role = None
    st.rerun()

# --- 1. CADASTRAR EQUIPAMENTO (Supervisor e Master) ---
if menu == "Cadastrar Equipamento":
    st.header("Cadastrar Novo Equipamento")
    
    with st.form("cadastro_equipamento_form"):
        tipo = st.selectbox("Tipo de Equipamento (Obrigatório)*", ["", "Monitor", "Computador", "Mouse", "Teclado", "Dispositivo de Áudio", "Adaptador Wi-Fi"])
        marca = st.selectbox("Marca (Obrigatório)*", ["", "Dell", "HP", "Positivo", "Microsoft", "MSI", "Acer", "Thin Client", "GIC", "AOC", "TP-LINK", "Samsung", "Logitech", "Knup", "Jebre", "LG", "Philips"])
        modelo = st.text_input("Modelo (Opcional)")
        colaborador = st.text_input("Colaborador Responsável (Nome e Sobrenome) (Obrigatório)*")
        descricao = st.text_area("Descrição (Opcional - Máx. 240 caracteres)", max_chars=240)
        
        # Criando colunas para colocar os campos lado a lado
        col1, col2 = st.columns(2)
        with col1:
            codigo_input = st.text_input("Código do Equipamento (Obrigatório)*")
        with col2:
            service_tag_input = st.text_input("Service Tag (Obrigatório)*")
        
        fotos = st.file_uploader("Fotos do equipamento (Obrigatório - Máx 10 fotos)*", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        
        if st.form_submit_button("Salvar Cadastro"):
            codigo = codigo_input.strip().upper()
            service_tag = service_tag_input.strip().upper() # Padronizando também a Service Tag
            
            # Adicionado service_tag na validação
            if not tipo or not marca or not colaborador.strip() or not codigo or not service_tag or not fotos or len(fotos) == 0:
                st.error("Por favor, preencha todos os campos obrigatórios (*) e anexe pelo menos uma foto.")
            elif len(fotos) > 10:
                st.error("Permitido anexar no máximo 10 fotos.")
            else:
                check = supabase.table("equipamentos").select("id").eq("codigo_controle", codigo).execute()
                if check.data:
                    st.error(f"Já existe um equipamento cadastrado com o código {codigo}.")
                else:
                    urls_fotos = []
                    erro_upload = False
                    
                    with st.spinner("Enviando fotos para o servidor..."):
                        for idx, foto in enumerate(fotos):
                            extensao = foto.name.split(".")[-1]
                            caminho_storage = f"{codigo}/{codigo}_{idx}_{int(datetime.now().timestamp())}.{extensao}"
                            try:
                                supabase.storage.from_("equipamentos-fotos").upload(caminho_storage, foto.read())
                                url = supabase.storage.from_("equipamentos-fotos").get_public_url(caminho_storage)
                                urls_fotos.append(url)
                            except Exception as e:
                                st.error(f"Falha ao enviar a foto {foto.name}: {e}")
                                erro_upload = True
                                break
                    
                    if not erro_upload:
                        supabase.table("equipamentos").insert({
                            "codigo_controle": codigo,
                            "service_tag": service_tag, # Adicionado campo para o Supabase
                            "tipo": tipo,
                            "marca": marca,
                            "modelo": modelo if modelo else None,
                            "colaborador": colaborador.strip(),
                            "descricao": descricao if descricao else None,
                            "fotos": urls_fotos,
                            "status": "Ativo",
                            "criado_por": st.session_state.user.email,
                            "data_registro": str(date.today())
                        }).execute()
                        
                        log_msg = f'O usuário: "{st.session_state.user.email}" cadastrou o equipamento: "{tipo}", "Código": {codigo}, "Service Tag": {service_tag}, "Colaborador": "{colaborador.strip()}"'
                        registrar_log("Inserir", log_msg)
                        
                        st.success(f"Equipamento {codigo} (ST: {service_tag}) cadastrado com sucesso!")
                        import time
                        time.sleep(2)
                        st.rerun()

# --- 2. EDITAR CADASTRO (Apenas Master) ---
elif menu == "Editar Cadastro" and st.session_state.user_role == "Master":
    st.header("Editar / Remover Cadastro de Equipamento")
    
    # 1. Buscar todos os dados para alimentar os filtros dinâmicos
    res_busca = supabase.table("equipamentos").select("*").execute()
    todos_equipamentos = res_busca.data if res_busca.data else []
    
    # Criar uma variável para armazenar o equipamento que será editado no final
    equip_selecionado = None

    # 2. Opção de escolha do método de busca
    metodo_busca = st.radio("Como deseja localizar o equipamento?", ["Por busca textual", "Por Colaborador/Tipo"])

    # --- MÉTODO 1: BUSCA TEXTUAL ---
    if metodo_busca == "Por busca textual":
        busca_ref = st.text_input("Buscar equipamento para edição (Digite qualquer referência: Código, Nome, Colaborador, Marca...):")
        
        if busca_ref:
            resultados = []
            ref_lower = busca_ref.lower()
            
            for item in todos_equipamentos:
                if (ref_lower in str(item.get("codigo_controle", "")).lower() or
                    ref_lower in str(item.get("service_tag", "")).lower() or
                    ref_lower in str(item.get("tipo", "")).lower() or
                    ref_lower in str(item.get("marca", "")).lower() or
                    ref_lower in str(item.get("modelo", "")).lower() or
                    ref_lower in str(item.get("colaborador", "")).lower()):
                    resultados.append(item)
                    
            if not resultados:
                st.warning("Nenhum equipamento foi localizado com essa referência.")
            else:
                opcoes_select = {f"{i['codigo_controle']} - {i['tipo']} ({i['colaborador']})": i for i in resultados}
                escolha = st.selectbox("Selecione o equipamento exato para manipular:", list(opcoes_select.keys()))
                equip_selecionado = opcoes_select[escolha]

    # --- MÉTODO 2: FILTRO POR COLABORADOR E TIPO ---
    else:
        if not todos_equipamentos:
            st.warning("Nenhum equipamento cadastrado no banco de dados.")
        else:
            # Extrair colaboradores únicos (removendo nulos/vazios) e ordenar
            colaboradores_disponiveis = sorted(list(set([item["colaborador"] for item in todos_equipamentos if item.get("colaborador")])))
            
            colab_escolhido = st.selectbox("Selecione o Colaborador:", ["Selecione..."] + colaboradores_disponiveis)
            
            if colab_escolhido != "Selecione...":
                # Filtrar equipamentos do colaborador selecionado
                equips_do_colab = [item for item in todos_equipamentos if item.get("colaborador") == colab_escolhido]
                
                # Listar os tipos de equipamentos que ESSE colaborador possui
                tipos_disponiveis = sorted(list(set([item["tipo"] for item in equips_do_colab if item.get("tipo")])))
                
                tipo_escolhido = st.selectbox("Selecione o Tipo de Equipamento:", ["Selecione..."] + tipos_disponiveis)
                
                if tipo_escolhido != "Selecione...":
                    # Filtrar pelo tipo escolhido
                    equips_finais = [item for item in equips_do_colab if item.get("tipo") == tipo_escolhido]
                    
                    # Se houver mais de um equipamento do mesmo tipo para o mesmo colaborador (ex: 2 Monitores)
                    opcoes_finais = {f"{i['codigo_controle']} - {i['marca']} {i.get('modelo', '')}": i for i in equips_finais}
                    
                    if len(opcoes_finais) == 1:
                        equip_selecionado = list(opcoes_finais.values())[0]
                    else:
                        escolha_final = st.selectbox("Mais de um equipamento encontrado. Selecione pelo Código/Marca:", list(opcoes_finais.keys()))
                        equip_selecionado = opcoes_finais[escolha_final]

    # --- 3. FORMULÁRIO DE EDIÇÃO (Executa se um equipamento foi encontrado/selecionado) ---
    if equip_selecionado:
        st.markdown("---")
        
        with st.form("form_edicao_master"):
            ed_codigo = st.text_input("Código do Equipamento*", value=str(equip_selecionado.get('codigo_controle') or ""))
            ed_st = st.text_input("Service Tag", value=str(equip_selecionado.get('service_tag') or ""))
            
            # Validação preventiva caso o tipo/marca não estejam nas listas padrões
            tipos_padrao = ["Monitor", "Computador", "Mouse", "Teclado", "Dispositivo de Áudio", "Adaptador Wi-Fi"]
            ed_tipo_idx = tipos_padrao.index(equip_selecionado['tipo']) if equip_selecionado['tipo'] in tipos_padrao else 0
            ed_tipo = st.selectbox("Tipo de Equipamento*", tipos_padrao, index=ed_tipo_idx)
            
            marcas_padrao = ["Dell", "HP", "Positivo", "Microsoft", "MSI", "Acer", "Thin Client", "GIC", "AOC", "TP-LINK", "Samsung", "Logitech", "Knup", "Jebre", "LG", "Philips"]
            ed_marca_idx = marcas_padrao.index(equip_selecionado['marca']) if equip_selecionado['marca'] in marcas_padrao else 0
            ed_marca = st.selectbox("Marca*", marcas_padrao, index=ed_marca_idx)
            
            ed_modelo = st.text_input("Modelo", value=equip_selecionado.get('modelo') or "")
            ed_colab = st.text_input("Colaborador Responsável*", value=equip_selecionado.get('colaborador') or "")
            ed_desc = st.text_area("Descrição (Máx. 240 car.)", value=equip_selecionado.get('descricao') or "", max_chars=240)
            ed_status = st.selectbox("Status", ["Ativo", "Baixado"], index=0 if equip_selecionado.get('status') == "Ativo" else 1)
            
            lista_fotos_atual = equip_selecionado.get("fotos", [])
            st.write("**Fotos salvas atualmente (Passe o mouse e clique nas setas ⤢ para ver em tamanho real):**")
            fotos_para_manter = []
            
            if lista_fotos_atual:
                cols = st.columns(10)
                for i, url_f in enumerate(lista_fotos_atual):
                    with cols[i % 10]:
                        try:
                            caminho_relative = url_f.split("equipamentos-fotos/")[-1] if "equipamentos-fotos/" in url_f else url_f
                            bytes_foto = supabase.storage.from_("equipamentos-fotos").download(caminho_relative)
                            st.image(bytes_foto, use_container_width=True)
                        except Exception:
                            st.caption("⚠️ Erro")
                        if st.checkbox("Manter", value=True, key=f"foto_{i}"):
                            fotos_para_manter.append(url_f)
            else:
                st.caption("Nenhuma foto cadastrada.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            novas_fotos = st.file_uploader("Adicionar Novas Fotos (Máx Total 10 fotos acumuladas)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="novas_fotos_edit")
            
            btn_salvar = st.form_submit_button("Atualizar Informações")
            btn_deletar = st.form_submit_button("🗑️ Excluir Equipamento Permanentemente")
            
            if btn_salvar:
                if not ed_codigo.strip():
                    st.error("O campo Código do Equipamento é obrigatório.")
                elif not ed_colab.strip():
                    st.error("O campo Colaborador Responsável é obrigatório.")
                else:
                    urls_finais = list(fotos_para_manter)
                    erro_upload = False
                    
                    if novas_fotos:
                        if (len(urls_finais) + len(novas_fotos)) > 10:
                            st.error("A soma de fotos salvas com as novas excede o limite máximo de 10.")
                            erro_upload = True
                        else:
                            for idx, foto in enumerate(novas_fotos):
                                extensao = foto.name.split(".")[-1]
                                caminho_storage = f"{ed_codigo.strip()}/{ed_codigo.strip()}_edit_{idx}_{int(datetime.now().timestamp())}.{extensao}"
                                try:
                                    supabase.storage.from_("equipamentos-fotos").upload(caminho_storage, foto.read())
                                    url = supabase.storage.from_("equipamentos-fotos").get_public_url(caminho_storage)
                                    urls_finais.append(url)
                                except Exception as e:
                                    st.error(f"Erro ao subir foto complementar: {e}")
                                    erro_upload = True
                                    break
                    
                    if not erro_upload:
                        try:
                            supabase.table("equipamentos").update({
                                "codigo_controle": ed_codigo.strip(),
                                "service_tag": ed_st.strip(),
                                "tipo": ed_tipo,
                                "marca": ed_marca,
                                "modelo": ed_modelo if ed_modelo else None,
                                "colaborador": ed_colab.strip(),
                                "descricao": ed_desc if ed_desc else None,
                                "status": ed_status,
                                "fotos": urls_finais
                            }).eq("codigo_controle", equip_selecionado['codigo_controle']).execute()
                            
                            registrar_log("Atualizar", f'O usuário "{st.session_state.user.email}" alterou dados do equipamento {equip_selecionado["codigo_controle"]} (Novo código: {ed_codigo.strip()}).')
                            st.success("Cadastro atualizado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar no banco de dados. Verifique se este novo código já não está em uso: {e}")
                            
            if btn_deletar:
                supabase.table("equipamentos").delete().eq("codigo_controle", equip_selecionado['codigo_controle']).execute()
                registrar_log("Deletar", f'O usuário "{st.session_state.user.email}" deletou o equipamento {equip_selecionado["codigo_controle"]}.')
                st.success("Equipamento removido do banco de dados!")
                st.rerun()

# --- 3. LISTA DE EQUIPAMENTOS (Supervisor e Master) ---
elif menu == "Lista de Equipamentos":
    st.header("Lista Geral de Equipamentos")
    res_equip = supabase.table("equipamentos").select("*").order("data_registro", desc=False).execute()
    
    if res_equip.data:
        df_completo = pd.DataFrame(res_equip.data)
        col_filtro1, col_filtro2 = st.columns([2, 1])
        
        with col_filtro1:
            pesquisa = st.text_input("Pesquisar na lista (Qualquer referência):")
            
        with col_filtro2:
            if 'colaborador' in df_completo.columns:
                lista_colaboradores = df_completo['colaborador'].dropna().unique().tolist()
                lista_colaboradores = sorted([str(c) for c in lista_colaboradores if str(c).strip() != ""])
            else:
                lista_colaboradores = []
                
            opcoes_colaboradores = ["Todos"] + lista_colaboradores
            colaborador_selecionado = st.selectbox("Filtrar por Colaborador:", options=opcoes_colaboradores)
        
        df_exibicao = df_completo.copy()
        if colaborador_selecionado != "Todos":
            df_exibicao = df_exibicao[df_exibicao['colaborador'] == colaborador_selecionado]
        if pesquisa:
            p_lower = pesquisa.lower()
            mascara = df_exibicao.astype(str).apply(lambda x: x.str.lower().str.contains(p_lower)).any(axis=1)
            df_exibicao = df_exibicao[mascara]
            
        colunas_ordenadas = ['codigo_controle', 'service_tag', 'tipo', 'marca', 'modelo', 'colaborador', 'descricao', 'data_registro', 'criado_por', 'status', 'fotos']
        for c in colunas_ordenadas:
            if c not in df_exibicao.columns:
                df_exibicao[c] = None
                
        df_exibicao = df_exibicao[colunas_ordenadas]
        st.write(f"Exibindo {len(df_exibicao)} registros:")
        st.dataframe(df_exibicao, use_container_width=True)
        
        col_btn1, col_btn2, _ = st.columns([1, 1, 6])
        with col_btn1:
            dados_excel = gerar_excel(df_exibicao)
            st.download_button(label="📥 Extrair em EXCEL", data=dados_excel, file_name="lista_equipamentos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_btn2:
            dados_pdf = gerar_pdf(df_exibicao, "Relação de Equipamentos - Lista Geral")
            st.download_button(label="📥 Extrair em PDF", data=dados_pdf, file_name="lista_equipamentos.pdf", mime="application/pdf")
    else:
        st.info("Nenhum equipamento cadastrado até o momento.")


# --- 4. RELATÓRIOS CORRIGIDO (Apenas Master) ---
elif menu == "Relatórios" and st.session_state.user_role == "Master":
    st.header("Central de Relatórios de Equipamentos")
    
    op_relatorio = st.selectbox("Selecione o tipo de relatório desejado:", [
        "1. Relação de equipamentos cadastrados por período",
        "2. Relação de equipamentos por usuário específico",
        "3. Relação consolidada de todos os usuários"
    ])
    
    df_filtrado = pd.DataFrame()
    titulo_doc = ""
    is_consolidado_pdf = False
    
    if op_relatorio.startswith("1"):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_inicio = st.date_input("Data de Início", date.today())
        with col_d2:
            d_fim = st.date_input("Data de Fim", date.today())
            
        if st.button("Filtrar Período"):
            res = supabase.table("equipamentos").select("*").gte("data_registro", str(d_inicio)).lte("data_registro", str(d_fim)).execute()
            if res.data:
                df_filtrado = pd.DataFrame(res.data)
                
                if 'id' in df_filtrado.columns:
                    df_filtrado = df_filtrado.drop_duplicates(subset=['id'], keep='last')
                
                if 'colaborador' in df_filtrado.columns:
                    df_filtrado = df_filtrado.sort_values(by='colaborador', key=lambda col: col.str.lower(), na_position='last')
                titulo_doc = f"Equipamentos Cadastrados de {d_inicio.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}"
            else:
                st.warning("Nenhum dado retornado para este período.")
                
    elif op_relatorio.startswith("2"):
        res_colab = supabase.table("equipamentos").select("colaborador").execute()
        lista_colabs = list(set([item['colaborador'] for item in res_colab.data if item.get('colaborador')])) if res_colab.data else []
        lista_colabs = sorted(lista_colabs, key=str.lower)
        
        colab_selecionado = st.selectbox("Selecione o Colaborador Responsável:", lista_colabs)
        
        if st.button("Filtrar por Usuário") and colab_selecionado:
            res = supabase.table("equipamentos").select("*").eq("colaborador", colab_selecionado).execute()
            if res.data:
                df_filtrado = pd.DataFrame(res.data)
                
                if 'id' in df_filtrado.columns:
                    df_filtrado = df_filtrado.drop_duplicates(subset=['id'], keep='last')
                
                if 'colaborador' in df_filtrado.columns:
                    df_filtrado = df_filtrado.sort_values(by='colaborador', key=lambda col: col.str.lower())
                titulo_doc = f"Equipamentos sob Responsabilidade de: {colab_selecionado}"
            else:
                st.warning("Nenhum equipamento localizado para este colaborador.")
                
    elif op_relatorio.startswith("3"):
        if st.button("Filtrar Todos os Usuários"):
            res = supabase.table("equipamentos").select("*").execute()
            if res.data:
                df_filtrado = pd.DataFrame(res.data)
                
                if 'colaborador' in df_filtrado.columns:
                    df_filtrado = df_filtrado.dropna(subset=['colaborador'])
                    if 'id' in df_filtrado.columns:
                        df_filtrado = df_filtrado.drop_duplicates(subset=['id'], keep='last')
                        
                    df_filtrado = df_filtrado.sort_values(by='colaborador', key=lambda col: col.str.lower())
                    titulo_doc = "Relatório Geral Consolidado de Equipamentos"
                    is_consolidado_pdf = True  
                else:
                    st.error("A coluna 'colaborador' não foi encontrada.")
            else:
                st.warning("Banco de dados vazio.")
                
    # Apresentação do frame filtrado e opções dinâmicas de download
    if not df_filtrado.empty:
        st.markdown("---")
        st.subheader("Prévia dos Resultados Filtrados")
        st.dataframe(df_filtrado, use_container_width=True)
        
        c_down1, c_down2, _ = st.columns([1, 1, 6])
        with c_down1:
            ex_data = gerar_excel(df_filtrado)
            st.download_button("📥 Baixar EXCEL", data=ex_data, file_name="relatorio.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c_down2:
            if is_consolidado_pdf:
                pdf_data = gerar_pdf_consolidado(df_filtrado, titulo_doc)
                nome_arquivo = "relatorio_consolidado_usuarios.pdf"
            else:
                pdf_data = gerar_pdf(df_filtrado, titulo_doc)
                nome_arquivo = "relatorio.pdf"
                
            st.download_button("📥 Baixar PDF", data=pdf_data, file_name=nome_arquivo, mime="application/pdf")


# --- 5. LOG DE ATIVIDADES (Apenas Master) ---
elif menu == "Log de Atividades" and st.session_state.user_role == "Master":
    st.header("Log de Atividades do Sistema")
    st.caption("Exibe todas as inserções, atualizações e exclusões em tempo real.")
    
    logs = supabase.table("logs").select("*").order("created_at", desc=True).execute()
    
    if logs.data:
        df_logs = pd.DataFrame(logs.data)
        df_logs = df_logs.rename(columns={
            "created_at": "Data/Hora Evento",
            "usuario_email": "Operador",
            "acao": "Operação",
            "resumo": "Histórico Detalhado"
        })
        if "id" in df_logs.columns:
            df_logs = df_logs.drop(columns=["id"])
            
        st.table(df_logs)
    else:
        st.info("Nenhuma atividade registrada nos logs.")
