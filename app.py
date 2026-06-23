import streamlit as st
from supabase import create_client
from datetime import date, datetime
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import ast
import json
import base64
import streamlit.components.v1 as components

BUCKET_FOTOS = "equipamentos-fotos"

def obter_lista_fotos(valor):
    if valor is None:
        return []

    if isinstance(valor, list):
        return [str(f).strip() for f in valor if str(f).strip() not in ["", "None", "nan", "[]"]]

    texto = str(valor).strip()

    if texto in ["", "None", "nan", "[]"]:
        return []

    if texto.startswith("[") and texto.endswith("]"):
        try:
            lista = json.loads(texto)
            return [str(f).strip() for f in lista if str(f).strip()]
        except Exception:
            try:
                lista = ast.literal_eval(texto)
                return [str(f).strip() for f in lista if str(f).strip()]
            except Exception:
                return [texto]

    return [texto]


def obter_caminho_bucket(foto):
    if not foto:
        return None

    foto = str(foto).strip()

    marcador_publico = f"/storage/v1/object/public/{BUCKET_FOTOS}/"
    if marcador_publico in foto:
        return foto.split(marcador_publico, 1)[1]

    marcador_bucket = f"{BUCKET_FOTOS}/"
    if marcador_bucket in foto:
        return foto.split(marcador_bucket, 1)[1]

    if foto.startswith("http"):
        return None

    return foto

def mostrar_carrossel_fotos(caminhos_fotos, codigo_card):
    slides = []

    for caminho_foto in caminhos_fotos:
        bytes_foto = supabase.storage.from_(BUCKET_FOTOS).download(caminho_foto)
        ext = caminho_foto.split(".")[-1].lower()

        mime = "image/jpeg"
        if ext == "png":
            mime = "image/png"
        elif ext == "webp":
            mime = "image/webp"

        img_base64 = base64.b64encode(bytes_foto).decode("utf-8")
        slides.append(f"data:{mime};base64,{img_base64}")

    slides_js = json.dumps(slides)

    components.html(
        f"""
        <div class="carousel" id="carousel-{codigo_card}">
            <img id="img-{codigo_card}" src="" onclick="openExpanded_{codigo_card}()" />

            <button class="arrow left" onclick="prev_{codigo_card}(event)">‹</button>
            <button class="arrow right" onclick="next_{codigo_card}(event)">›</button>
        </div>

        <script>
            const slides_{codigo_card} = {slides_js};
            let index_{codigo_card} = 0;

            const img_{codigo_card} = document.getElementById("img-{codigo_card}");
            const left_{codigo_card} = document.querySelector("#carousel-{codigo_card} .left");
            const right_{codigo_card} = document.querySelector("#carousel-{codigo_card} .right");

            function render_{codigo_card}() {{
                img_{codigo_card}.src = slides_{codigo_card}[index_{codigo_card}];

                if (slides_{codigo_card}.length <= 1) {{
                    left_{codigo_card}.style.display = "none";
                    right_{codigo_card} = "none";
                }}
            }}

            function prev_{codigo_card}(event) {{
                event.stopPropagation();
                index_{codigo_card} = (index_{codigo_card} - 1 + slides_{codigo_card}.length) % slides_{codigo_card}.length;
                render_{codigo_card}();
            }}

            function next_{codigo_card}(event) {{
                event.stopPropagation();
                index_{codigo_card} = (index_{codigo_card} + 1) % slides_{codigo_card}.length;
                render_{codigo_card}();
            }}

            function closeExpanded_{codigo_card}() {{
                const existing = window.parent.document.getElementById("expanded-photo-{codigo_card}");
                if (existing) {{
                    existing.remove();
                }}
            }}

            function openExpanded_{codigo_card}() {{
                const parentDoc = window.parent.document;

                const oldModal = parentDoc.getElementById("expanded-photo-{codigo_card}");
                if (oldModal) {{
                    oldModal.remove();
                }}

                const overlay = parentDoc.createElement("div");
                overlay.id = "expanded-photo-{codigo_card}";
                overlay.style.position = "fixed";
                overlay.style.inset = "0";
                overlay.style.zIndex = "999999";
                overlay.style.background = "rgba(0, 0, 0, 0.86)";
                overlay.style.display = "flex";
                overlay.style.alignItems = "center";
                overlay.style.justifyContent = "center";
                overlay.style.padding = "24px";
                overlay.style.boxSizing = "border-box";
                overlay.style.cursor = "zoom-out";

                const expandedImg = parentDoc.createElement("img");
                expandedImg.src = slides_{codigo_card}[index_{codigo_card}];
                expandedImg.style.maxWidth = "96vw";
                expandedImg.style.maxHeight = "92vh";
                expandedImg.style.objectFit = "contain";
                expandedImg.style.borderRadius = "10px";
                expandedImg.style.boxShadow = "0 20px 70px rgba(0, 0, 0, 0.55)";
                expandedImg.style.cursor = "default";

                const closeBtn = parentDoc.createElement("button");
                closeBtn.innerHTML = "×";
                closeBtn.style.position = "fixed";
                closeBtn.style.top = "18px";
                closeBtn.style.right = "24px";
                closeBtn.style.width = "44px";
                closeBtn.style.height = "44px";
                closeBtn.style.border = "0";
                closeBtn.style.borderRadius = "999px";
                closeBtn.style.background = "rgba(255, 255, 255, 0.18)";
                closeBtn.style.color = "#fff";
                closeBtn.style.fontSize = "34px";
                closeBtn.style.lineHeight = "34px";
                closeBtn.style.cursor = "pointer";
                closeBtn.style.paddingBottom = "4px";

                overlay.onclick = function() {{
                    overlay.remove();
                }};

                expandedImg.onclick = function(event) {{
                    event.stopPropagation();
                }};

                closeBtn.onclick = function(event) {{
                    event.stopPropagation();
                    overlay.remove();
                }};

                overlay.appendChild(expandedImg);
                overlay.appendChild(closeBtn);
                parentDoc.body.appendChild(overlay);
            }}

            render_{codigo_card}();
        </script>

        <style>
            .carousel {{
                position: relative;
                width: 100%;
                height: 220px;
                overflow: hidden;
                border-radius: 8px;
                background: #f3f4f6;
            }}

            .carousel img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
                cursor: zoom-in;
            }}

            .arrow {{
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                width: 34px;
                height: 46px;
                border: 0;
                border-radius: 999px;
                background: rgba(0, 0, 0, 0.18);
                color: white;
                font-size: 32px;
                line-height: 32px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                padding-bottom: 5px;
            }}

            .arrow:hover {{
                background: rgba(0, 0, 0, 0.32);
            }}

            .left {{
                left: 8px;
            }}

            .right {{
                right: 8px;
            }}
        </style>
        """,
        height=232,
    )
    
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


def gerar_pdf_consolidado(df_ordenado, titulo_geral="Relatório Geral Consolidado de Equipamentos"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
    colab_style = ParagraphStyle('ColabStyle', parent=styles['Heading2'], fontSize=13, leading=16, textColor=colors.HexColor("#2C5282"), spaceBefore=10, spaceAfter=10)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, leading=10)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, leading=11, textColor=colors.white, fontName="Helvetica-Bold")
    
    colunas_pdf = ['codigo_controle', 'service_tag', 'tipo', 'marca', 'status', 'data_registro']
    grupos = list(df_ordenado.groupby('colaborador', sort=False))
    
    for i, (colaborador, group) in enumerate(grupos):
        if i == 0:
            story.append(Paragraph(titulo_geral, title_style))
            story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 15))
            
        story.append(Paragraph(f"Colaborador: {colaborador}", colab_style))
        story.append(Spacer(1, 5))
        
        df_pdf = group[colunas_pdf].copy() if all(c in group.columns for c in colunas_pdf) else group.iloc[:, :6]
        table_data = [[Paragraph(col.upper(), header_style) for col in df_pdf.columns]]
        
        for _, row in df_pdf.iterrows():
            row_cells = []
            for val in row.values:
                row_cells.append(Paragraph(str(val) if pd.notnull(val) else "", cell_style))
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
    opcoes_menu.append("Baixas")
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
        tipo = st.selectbox("Tipo de Equipamento (Obrigatório)*", ["", "Monitor", "Computador", "Mouse", "Teclado", "Dispositivo de Áudio", "Adaptador Wi-Fi", "Estação de Trabalho"])
        marca = st.selectbox("Marca (Obrigatório)*", ["", "Estação", "Dell", "HP", "Positivo", "Microsoft", "MSI", "Acer", "Thin Client", "GIC", "AOC", "TP-LINK", "Samsung", "Logitech", "Knup", "Jebre", "LG", "Philips", "Newlink", "Lenovo", "FEASSO", "LEHMOX"])
        modelo = st.text_input("Modelo (Opcional)")
        colaborador = st.text_input("Colaborador Responsável (Nome e Sobrenome) (Obrigatório)*")
        descricao = st.text_area("Descrição (Opcional - Máx. 240 caracteres)", max_chars=240)
        
        col1, col2 = st.columns(2)
        with col1:
            codigo_input = st.text_input("Código do Equipamento (Obrigatório)*")
        with col2:
            service_tag_input = st.text_input("Service Tag (Obrigatório)*")
        
        fotos = st.file_uploader("Fotos do equipamento (Obrigatório - Máx 10 fotos)*", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        
        if st.form_submit_button("Salvar Cadastro"):
            codigo = codigo_input.strip().upper()
            service_tag = service_tag_input.strip().upper()
            
            if not tipo or not marca or not colaborador.strip() or not codigo or not service_tag or not fotos or len(fotos) == 0:
                st.error("Por favor, preencha todos os campos obrigatórios (*) e anexe pelo menos uma foto.")
            elif len(fotos) > 10:
                st.error("Permitido anexar no máximo 10 fotos.")
            else:
                check_codigo = supabase.table("equipamentos").select("id").eq("codigo_controle", codigo).execute()
                check_service_tag = supabase.table("equipamentos").select("id").eq("service_tag", service_tag).execute()
                
                if check_codigo.data:
                    st.error(f"Já existe um equipamento cadastrado com o código {codigo}.")
                elif check_service_tag.data:
                    st.error(f"Já existe um equipamento cadastrado com a Service Tag {service_tag}.")
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
                            "service_tag": service_tag,
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
    
    res_busca = supabase.table("equipamentos").select("*").execute()
    todos_equipamentos = res_busca.data if res_busca.data else []
    equip_selecionado = None

    metodo_busca = st.radio("Como deseja localizar o equipamento?", ["Por busca textual", "Por Colaborador/Tipo"])

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

    else:
        if not todos_equipamentos:
            st.warning("Nenhum equipamento cadastrado no banco de dados.")
        else:
            colaboradores_disponiveis = sorted(list(set([item["colaborador"] for item in todos_equipamentos if item.get("colaborador")])))
            colab_escolhido = st.selectbox("Selecione o Colaborador:", ["Selecione..."] + colaboradores_disponiveis)
            
            if colab_escolhido != "Selecione...":
                equips_do_colab = [item for item in todos_equipamentos if item.get("colaborador") == colab_escolhido]
                tipos_disponiveis = sorted(list(set([item["tipo"] for item in equips_do_colab if item.get("tipo")])))
                tipo_escolhido = st.selectbox("Selecione o Tipo de Equipamento:", ["Selecione..."] + tipos_disponiveis)
                
                if tipo_escolhido != "Selecione...":
                    equips_finais = [item for item in equips_do_colab if item.get("tipo") == tipo_escolhido]
                    opcoes_finais = {f"{i['codigo_controle']} - {i['marca']} {i.get('modelo', '')}": i for i in equips_finais}
                    
                    if len(opcoes_finais) == 1:
                        equip_selecionado = list(opcoes_finais.values())[0]
                    else:
                        escolha_final = st.selectbox("Mais de um equipamento encontrado. Selecione pelo Código/Marca:", list(opcoes_finais.keys()))
                        equip_selecionado = opcoes_finais[escolha_final]

    if equip_selecionado:
        st.markdown("---")
        
        with st.form("form_edicao_master"):
            ed_codigo = st.text_input("Código do Equipamento*", value=str(equip_selecionado.get('codigo_controle') or ""))
            ed_st = st.text_input("Service Tag", value=str(equip_selecionado.get('service_tag') or ""))
            
            tipos_padrao = ["Monitor", "Computador", "Mouse", "Teclado", "Dispositivo de Áudio", "Adaptador Wi-Fi", "Estação de Trabalho"]
            ed_tipo_idx = tipos_padrao.index(equip_selecionado['tipo']) if equip_selecionado['tipo'] in tipos_padrao else 0
            ed_tipo = st.selectbox("Tipo de Equipamento*", tipos_padrao, index=ed_tipo_idx)
            
            marcas_padrao = ["Estação", "Dell", "HP", "Positivo", "Microsoft", "MSI", "Acer", "Thin Client", "GIC", "AOC", "TP-LINK", "Samsung", "Logitech", "Knup", "Jebre", "LG", "Philips", "Newlink", "Lenovo", "FEASSO", "LEHMOX"]
            ed_marca_idx = marcas_padrao.index(equip_selecionado['marca']) if equip_selecionado['marca'] in marcas_padrao else 0
            ed_marca = st.selectbox("Marca*", marcas_padrao, index=ed_marca_idx)
            
            ed_modelo = st.text_input("Modelo", value=equip_selecionado.get('modelo') or "")
            ed_colab = st.text_input("Colaborador Responsável*", value=equip_selecionado.get('colaborador') or "")
            ed_desc = st.text_area("Descrição (Máx. 240 car.)", value=equip_selecionado.get('descricao') or "", max_chars=240)
            ed_status = st.selectbox("Status", ["Ativo", "Baixado", "Inativo"], index=["Ativo", "Baixado", "Inativo"].index(equip_selecionado.get('status', 'Ativo')) if equip_selecionado.get('status') in ["Ativo", "Baixado", "Inativo"] else 0)
            
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
            pesquisa = st.text_input("Pesquisar na lista (Qualquer referencia):")

        with col_filtro2:
            if "colaborador" in df_completo.columns:
                lista_colaboradores = df_completo["colaborador"].dropna().unique().tolist()
                lista_colaboradores = sorted([str(c) for c in lista_colaboradores if str(c).strip() != ""])
            else:
                lista_colaboradores = []

            opcoes_colaboradores = ["Todos"] + lista_colaboradores
            colaborador_selecionado = st.selectbox("Filtrar por Colaborador:", options=opcoes_colaboradores)

        filtro_ativo = bool(pesquisa) or colaborador_selecionado != "Todos"
        df_exibicao = df_completo.copy()

        if colaborador_selecionado != "Todos":
            df_exibicao = df_exibicao[df_exibicao["colaborador"] == colaborador_selecionado]

        if pesquisa:
            p_lower = pesquisa.lower()
            mascara = df_exibicao.astype(str).apply(
                lambda x: x.str.lower().str.contains(p_lower, na=False)
            ).any(axis=1)
            df_exibicao = df_exibicao[mascara]

        colunas_ordenadas = [
            "codigo_controle",
            "service_tag",
            "tipo",
            "marca",
            "modelo",
            "colaborador",
            "descricao",
            "data_registro",
            "criado_por",
            "status",
            "fotos",
        ]

        for c in colunas_ordenadas:
            if c not in df_exibicao.columns:
                df_exibicao[c] = None

        df_exibicao = df_exibicao[colunas_ordenadas]

        if not filtro_ativo:
            st.info("Use a barra de pesquisa ou o filtro de colaborador para visualizar os equipamentos.")
        else:
            total_registros = len(df_exibicao)
            itens_por_pagina = 15
            total_paginas = max(1, (total_registros + itens_por_pagina - 1) // itens_por_pagina)

            filtro_paginacao = f"{pesquisa}|{colaborador_selecionado}|{total_registros}"
            if st.session_state.get("filtro_lista_equipamentos") != filtro_paginacao:
                st.session_state.filtro_lista_equipamentos = filtro_paginacao
                st.session_state.pagina_lista_equipamentos = 1

            pagina_atual = st.session_state.get("pagina_lista_equipamentos", 1)
            pagina_atual = min(max(1, pagina_atual), total_paginas)
            st.session_state.pagina_lista_equipamentos = pagina_atual

            inicio = (pagina_atual - 1) * itens_por_pagina
            fim = inicio + itens_por_pagina
            df_pagina = df_exibicao.iloc[inicio:fim]

            st.write(
                f"Exibindo {inicio + 1 if total_registros else 0} a "
                f"{min(fim, total_registros)} de {total_registros} registros:"
            )

            if df_exibicao.empty:
                st.warning("Nenhum equipamento encontrado com os filtros informados.")
            else:
                _, col_pag1, col_pag2, col_pag3, _ = st.columns([3, 1, 1.4, 1, 3])

                with col_pag1:
                    if st.button(
                        "Anterior",
                        use_container_width=True,
                        disabled=pagina_atual <= 1,
                        key="btn_pagina_anterior_equipamentos",
                    ):
                        st.session_state.pagina_lista_equipamentos = pagina_atual - 1
                        st.rerun()
                
                with col_pag2:
                    st.markdown(
                        f"""
                        <div style='text-align:center; padding-top: 0.45rem; white-space: nowrap;'>
                            Pagina {pagina_atual} de {total_paginas}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                
                with col_pag3:
                    if st.button(
                        "Proxima",
                        use_container_width=True,
                        disabled=pagina_atual >= total_paginas,
                        key="btn_pagina_proxima_equipamentos",
                    ):
                        st.session_state.pagina_lista_equipamentos = pagina_atual + 1
                        st.rerun()

                for i in range(0, len(df_pagina), 4):
                    cols = st.columns(4)

                    for col, (_, item) in zip(cols, df_pagina.iloc[i:i + 4].iterrows()):
                        with col:
                            status_atual = item.get('status') or '-'
                            is_inativo = str(status_atual).lower() == "inativo"
                            
                            with st.container(border=True):
                                # CORREÇÃO SOLICITADA: Se o equipamento estiver Inativo, aplica opacidade/transparência em todo o card
                                if is_inativo:
                                    st.markdown("<div style='opacity: 0.55; filter: grayscale(20%);'>", unsafe_allow_html=True)
                                
                                codigo_card = str(item.get("codigo_controle") or "sem_codigo").replace(" ", "_").replace("/", "_")
                                fotos = obter_lista_fotos(item.get("fotos"))

                                caminhos_fotos = []
                                for foto in fotos:
                                    caminho_foto = obter_caminho_bucket(foto)
                                    if caminho_foto:
                                        caminhos_fotos.append(caminho_foto)

                                if caminhos_fotos:
                                    try:
                                        mostrar_carrossel_fotos(caminhos_fotos, codigo_card)
                                        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                                    except Exception:
                                        st.warning("Foto encontrada, mas nao foi possivel carregar.")
                                else:
                                    st.info("Sem foto cadastrada")

                                st.markdown(f"**Codigo:** {item.get('codigo_controle') or '-'}")
                                st.markdown(f"**Tipo:** {item.get('tipo') or '-'}")
                                st.markdown(f"**Marca/Modelo:** {item.get('marca') or '-'} / {item.get('modelo') or '-'}")
                                st.markdown(f"**Service Tag:** {item.get('service_tag') or '-'}")
                                st.markdown(f"**Colaborador:** {item.get('colaborador') or '-'}")
                                
                                # Status Inativo com fonte em Vermelho em negrito
                                if is_inativo:
                                    st.markdown(f"**Status:** <span style='color:red; font-weight:bold;'>{status_atual}</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"**Status:** {status_atual}")

                                descricao = item.get("descricao")
                                if descricao and str(descricao).strip() not in ["", "None", "nan"]:
                                    st.caption(str(descricao))
                                    
                                if is_inativo:
                                    st.markdown("</div>", unsafe_allow_html=True)

                col_btn1, col_btn2, _ = st.columns([1, 1, 6])

                with col_btn1:
                    dados_excel = gerar_excel(df_exibicao)
                    st.download_button(
                        label="Extrair em EXCEL",
                        data=dados_excel,
                        file_name="lista_equipamentos.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                with col_btn2:
                    dados_pdf = gerar_pdf(df_exibicao, "Relacao de Equipamentos - Lista Geral")
                    st.download_button(
                        label="Extrair em PDF",
                        data=dados_pdf,
                        file_name="lista_equipamentos.pdf",
                        mime="application/pdf",
                    )
    else:
        st.info("Nenhum equipamento cadastrado ate o momento.")

# --- 4. MENU: BAIXAS (Supervisor e Master) ---
elif menu == "Baixas" and st.session_state.user_role in ["Supervisor", "Master"]:
    st.header("Gerenciamento de Baixas de Equipamentos")
    
    tab_listar, tab_nova = st.tabs(["Pesquisar Baixas", "➕ Nova Baixa"])
    
    with tab_listar:
        pesquisa_baixa = st.text_input("Pesquisar baixas criadas (Digite a Service Tag ou Motivo):")
        
        # 1. Filtra trazendo APENAS baixas que NÃO foram arquivadas (ativas no painel)
        res_baixas = supabase.table("baixas").select("*").eq("arquivado", False).order("data_baixa", desc=True).execute()
        
        if res_baixas.data:
            df_baixas = pd.DataFrame(res_baixas.data)
            
            res_equips = supabase.table("equipamentos").select("*").execute()
            df_equips = pd.DataFrame(res_equips.data) if res_equips.data else pd.DataFrame()
            
            if pesquisa_baixa:
                p_lower = pesquisa_baixa.lower()
                mascara = df_baixas.astype(str).apply(
                    lambda x: x.str.lower().str.contains(p_lower, na=False)
                ).any(axis=1)
                df_baixas = df_baixas[mascara]
            
            if df_baixas.empty:
                st.warning("Nenhuma baixa correspondente localizada.")
            else:
                # Loop para renderizar cada baixa
                for _, linha in df_baixas.iterrows():
                    st_atual = linha["service_tag"]
                    id_baixa = linha.get("id", "sem_id")
                    
                    # Localiza os dados do equipamento correspondente
                    dados_equip = {}
                    if not df_equips.empty:
                        equip_filtrado = df_equips[df_equips["service_tag"].astype(str).str.upper() == str(st_atual).upper()]
                        if not equip_filtrado.empty:
                            dados_equip = equip_filtrado.iloc[0].to_dict()
                    
                    status_atual_equip = dados_equip.get('status', 'N/A')
                    
                    # --- CONTAINER PRINCIPAL DA BAIXA ---
                    with st.container(border=True):
                        col_foto, col_dados_baixa, col_dados_equip = st.columns([1.5, 2, 1.5])
                        
                        # --- COLUNA DA ESQUERDA: FOTOS ---
                        with col_foto:
                            codigo_card = f"baixa_{str(id_baixa)}"
                            fotos_raw = obter_lista_fotos(linha.get("fotos"))
                            caminhos_fotos = []
                            for foto in fotos_raw:
                                caminho_foto = obter_caminho_bucket(foto)
                                if caminho_foto:
                                    caminhos_fotos.append(caminho_foto)
                            
                            if caminhos_fotos:
                                try:
                                    mostrar_carrossel_fotos(caminhos_fotos, codigo_card)
                                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                                except Exception:
                                    st.warning("Foto encontrada, mas não foi possível carregar.")
                            else:
                                st.info("Sem foto cadastrada nesta baixa.")
                        
                        # --- COLUNA DO CENTRO: DADOS DA BAIXA ---
                        with col_dados_baixa:
                            st.markdown(f"### Baixa: {st_atual}")
                            st.markdown(f"**Motivo:** {str(linha['motivo']).capitalize()}")
                            st.markdown(f"**Data da Baixa:** {linha.get('data_baixa', 'Não informada')}")
                            st.markdown(f"**Criado por:** {linha.get('criado_por', 'N/A')}")
                            if linha.get('observacao'):
                                st.markdown(f"**Observação:** *{linha['observacao']}*")
                        
                        # --- COLUNA DA DIREITA: DADOS DO EQUIPAMENTO ---
                        with col_dados_equip:
                            st.markdown("**Dados do Equipamento**") 
                            if dados_equip:
                                st.markdown(f"**Tipo:** {dados_equip.get('tipo', 'N/A')}")
                                st.markdown(f"**Colaborador:** {dados_equip.get('colaborador', 'N/A')}")
                                st.markdown(f"**Status:** {status_atual_equip}")
                                
                                # SÓ MOSTRA O BOTÃO SE FOR MASTER E SE O EQUIPAMENTO ESTIVER INATIVO
                                if st.session_state.user_role == "Master" and status_atual_equip == "Inativo":
                                    st.markdown("---")
                                    if st.button("🔄 Reativar Equipamento", key=f"btn_reativar_{id_baixa}", type="primary", use_container_width=True):
                                        with st.spinner("Reativando equipamento e removendo da lista..."):
                                            try:
                                                # 1. Altera o equipamento correspondente de volta para "Ativo"
                                                supabase.table("equipamentos").update({"status": "Ativo"}).eq("service_tag", st_atual).execute()
                                                
                                                # 2. Arquiva esta baixa específica para sumir da aba Pesquisar Baixas
                                                supabase.table("baixas").update({"arquivado": True}).eq("id", id_baixa).execute()
                                                
                                                # 3. Registra a reativação no Log do sistema
                                                registrar_log("Reativação", f'O usuário Master "{st.session_state.user.email}" finalizou e ocultou a baixa do equipamento ST: {st_atual}.')
                                                
                                                st.success(f"Equipamento {st_atual} reativado e baixa removida do painel!")
                                                import time
                                                time.sleep(1)
                                                st.rerun() # Atualiza a tela para sumir o card instantaneamente
                                            except Exception as e:
                                                st.error(f"Erro ao reativar equipamento: {e}")
                            else:
                                st.caption("Equipamento não localizado no banco.")
        else:
            st.info("Nenhum registro de baixa ativo no momento.")

    with tab_nova:
        st.subheader("Registrar Nova Baixa")
        
        res_equips_ativos = supabase.table("equipamentos").select("service_tag", "tipo", "colaborador").eq("status", "Ativo").execute()
        
        if not res_equips_ativos.data:
            st.warning("Não há equipamentos ativos cadastrados disponíveis para baixa.")
        else:
            lista_ativos = res_equips_ativos.data
            dict_equips = {}
            
            for item in lista_ativos:
                st_val = item.get("service_tag")
                if st_val and str(st_val).strip():
                    dict_equips[str(st_val).strip().upper()] = item
                    
            opcoes_st = ["Selecione..."] + sorted(list(dict_equips.keys()))
            st_selecionada = st.selectbox("Selecione a Service Tag (Obrigatório)*", options=opcoes_st)
            
            if st_selecionada != "Selecione...":
                dados_prev = dict_equips[st_selecionada]
                st.info(f"**Prévia do Equipamento:**\n* **Tipo:** {dados_prev['tipo']}\n* **Colaborador Responsável:** {dados_prev['colaborador']}")
            
            with st.form("form_registro_baixa", clear_on_submit=True):
                motivo = st.selectbox("Selecione o motivo da baixa (Obrigatório)*", ["", "manutenção", "descarte", "troca"])
                observacao = st.text_area("Observação (Opcional - Máx. 240 caracteres)", max_chars=240)
                fotos_baixa = st.file_uploader("Anexar fotos da baixa (Opcional - Máx 10 fotos)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="fotos_baixa_input")
                
                if st.form_submit_button("Confirmar Baixa"):
                    if st_selecionada == "Selecione..." or not motivo:
                        st.error("Por favor, preencha todos os campos obrigatórios (*).")
                    elif fotos_baixa and len(fotos_baixa) > 10:
                        st.error("Permitido anexar no máximo 10 fotos.")
                    else:
                        # -----------------------------------------------------------------
                        # VALIDAÇÃO CRÍTICA: IMPEDIR SERVICE_TAG DUPLICADA EM BAIXAS EM ABERTO
                        # -----------------------------------------------------------------
                        checar_duplicado = supabase.table("baixas").select("id").eq("service_tag", st_selecionada).eq("arquivado", False).execute()
                        
                        if checar_duplicado.data:
                            st.error(f"⚠️ O equipamento {st_selecionada} já possui uma baixa em andamento! Resolva a baixa anterior antes de abrir uma nova.")
                        else:
                            urls_fotos_baixa = []
                            erro_upload_baixa = False
                            
                            if fotos_baixa:
                                with st.spinner("Fazendo upload das fotos da baixa..."):
                                    for idx, foto in enumerate(fotos_baixa):
                                        ext = foto.name.split(".")[-1]
                                        caminho_storage = f"baixas/{st_selecionada}/{st_selecionada}_{idx}_{int(datetime.now().timestamp())}.{ext}"
                                        try:
                                            supabase.storage.from_(BUCKET_FOTOS).upload(caminho_storage, foto.read())
                                            url = supabase.storage.from_(BUCKET_FOTOS).get_public_url(caminho_storage)
                                            urls_fotos_baixa.append(url)
                                        except Exception as e:
                                            st.error(f"Falha ao enviar a foto {foto.name}: {e}")
                                            erro_upload_baixa = True
                                            break
                            
                            if not erro_upload_baixa:
                                try:
                                    supabase.table("baixas").insert({
                                        "service_tag": st_selecionada,
                                        "motivo": motivo,
                                        "observacao": observacao if observacao else None,
                                        "fotos": urls_fotos_baixa,
                                        "criado_por": st.session_state.user.email,
                                        "arquivado": False # Garante que entra visível
                                    }).execute()
                                    
                                    supabase.table("equipamentos").update({"status": "Inativo"}).eq("service_tag", st_selecionada).execute()
                                    registrar_log("Baixa", f'O usuário "{st.session_state.user.email}" deu baixa no equipamento ST: {st_selecionada} por motivo de {motivo}.')
                                    
                                    st.success(f"Baixa efetuada e equipamento (ST: {st_selecionada}) definido como Inativo com sucesso!")
                                    import time
                                    time.sleep(2)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao processar a requisição no banco de dados: {e}")

# --- 5. RELATÓRIOS (Apenas Master) ---
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


# --- 6. LOG DE ATIVIDADES (Apenas Master) ---
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
