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
import hmac
import streamlit.components.v1 as components
from postgrest.exceptions import APIError

BUCKET_FOTOS = "equipamentos-fotos"
TIPOS_EQUIPAMENTO = ["Monitor", "Computador", "Mouse", "Teclado", "Dispositivo de Áudio", "Adaptador Wi-Fi", "Estação de Trabalho"]
MARCAS_EQUIPAMENTO = ["Dell", "HP", "Positivo", "Microsoft", "MSI", "Acer", "Thin Client", "GIC", "AOC", "TP-LINK", "Samsung", "Logitech", "Knup", "Jebre", "LG", "Philips", "Newlink", "Lenovo", "FEASSO", "LEHMOX"]

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

# --- Acesso público e área administrativa protegida por senha ---
if "admin_access_requested" not in st.session_state:
    st.session_state.admin_access_requested = False
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if st.session_state.admin_access_requested and not st.session_state.admin_authenticated:
    st.title("Acesso à área administrativa")
    st.caption("Informe a senha administrativa configurada nos secrets do Streamlit.")
    with st.form("admin_login_form", clear_on_submit=True):
        senha_admin = st.text_input("Senha administrativa", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)
    if entrar:
        senha_configurada = st.secrets.get("ADMIN_PASSWORD")
        if not senha_configurada:
            st.error("A chave ADMIN_PASSWORD não está definida nos secrets do Streamlit.")
        elif hmac.compare_digest(senha_admin, str(senha_configurada)):
            st.session_state.admin_authenticated = True
            st.session_state.admin_access_requested = False
            st.rerun()
        else:
            st.error("Senha administrativa incorreta.")
    if st.button("Voltar ao cadastro público"):
        st.session_state.admin_access_requested = False
        st.rerun()
    st.stop()

# --- Funções Auxiliares de Log ---
def registrar_log(acao, resumo, colaborador):
    try:
        supabase.table("logs_sistema").insert({
            "colaborador": colaborador,
            "acao": acao,
            "resumo": resumo
        }).execute()
    except APIError as e:
        st.warning(
            "A operação foi concluída, mas não foi possível registrar a atividade. "
            f"Resposta do Supabase: {e}"
        )


def gerar_proximos_codigos_controle(quantidade):
    codigos_cadastrados = []
    inicio = 0
    tamanho_pagina = 1000
    while True:
        resposta = (
            supabase.table("equipamentos")
            .select("codigo_controle")
            .order("id")
            .range(inicio, inicio + tamanho_pagina - 1)
            .execute()
        )
        pagina = resposta.data or []
        codigos_cadastrados.extend(pagina)
        if len(pagina) < tamanho_pagina:
            break
        inicio += tamanho_pagina

    codigos = [
        int(str(item.get("codigo_controle")).strip())
        for item in codigos_cadastrados
        if str(item.get("codigo_controle", "")).strip().isdecimal()
    ]
    proximo_codigo = max(codigos, default=-1) + 1
    return [str(proximo_codigo + indice) for indice in range(quantidade)]


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


# --- Menu da área administrativa ---
if st.session_state.admin_authenticated:
    opcoes_menu = [
        "Cadastrar Equipamento",
        "Editar Cadastro",
        "Lista de Equipamentos",
        "Baixas",
        "Relatórios",
        "Log de Atividades",
    ]

    st.sidebar.title("Área administrativa")
    st.sidebar.info("Acesso autorizado por senha administrativa.")
    menu = st.sidebar.radio("Navegação", opcoes_menu)

    if st.sidebar.button("Voltar ao cadastro público"):
        st.session_state.admin_authenticated = False
        st.rerun()

    if st.sidebar.button("Sair do Sistema"):
        st.session_state.admin_authenticated = False
        st.rerun()
else:
    menu = "Cadastrar Equipamento"

# --- 1. CADASTRAR EQUIPAMENTO ---
if menu == "Cadastrar Equipamento":
    st.header("Cadastro de Equipamentos")
    if not st.session_state.admin_authenticated:
        st.caption("Cadastre um equipamento sem precisar criar uma conta ou fazer login.")

    if "cadastro_versao" not in st.session_state:
        st.session_state.cadastro_versao = 0
    cadastro_prefixo = f"cadastro_{st.session_state.cadastro_versao}"
    itens_key = f"{cadastro_prefixo}_itens"
    if itens_key not in st.session_state:
        st.session_state[itens_key] = [{"chave": "0"}]

    colaborador = st.text_input(
        "Colaborador Responsável (Nome e Sobrenome) (Obrigatório)*",
        key=f"{cadastro_prefixo}_colaborador",
    )
    descricao = st.text_area(
        "Tem algum detalhe no equipamento? Descreva abaixo (max 240 caracteres).",
        max_chars=240,
        key=f"{cadastro_prefixo}_descricao",
    )

    st.markdown("**Equipamentos do cadastro**")
    itens_cadastro = st.session_state[itens_key]
    dados_itens = []
    for indice, item in enumerate(itens_cadastro):
        chave = item["chave"]
        workstation = (
            st.session_state.get(f"{cadastro_prefixo}_tipo_{chave}")
            == "Estação de Trabalho"
        )
        if workstation:
            col_tipo, col_lixeira = st.columns([8, 0.6])
        else:
            col_tipo, col_marca, col_modelo, col_tag, col_lixeira = st.columns([2, 2, 2, 2, 0.6])
        with col_tipo:
            tipo = st.selectbox(
                "Tipo de equipamento*",
                [""] + TIPOS_EQUIPAMENTO,
                key=f"{cadastro_prefixo}_tipo_{chave}",
            )
        if tipo == "Estação de Trabalho":
            st.session_state.pop(f"{cadastro_prefixo}_marca_{chave}", None)
            st.session_state.pop(f"{cadastro_prefixo}_modelo_{chave}", None)
            st.session_state.pop(f"{cadastro_prefixo}_tag_{chave}", None)
            marca = None
            modelo = ""
            service_tag = ""
        else:
            with col_marca:
                marca = st.selectbox(
                    "Marca*",
                    [""] + MARCAS_EQUIPAMENTO,
                    key=f"{cadastro_prefixo}_marca_{chave}",
                )
            with col_modelo:
                modelo = st.text_input("Modelo", key=f"{cadastro_prefixo}_modelo_{chave}")
            with col_tag:
                service_tag = st.text_input("Etiqueta Patrimônio Mult (se tiver)", key=f"{cadastro_prefixo}_tag_{chave}")
        with col_lixeira:
            st.write("")
            if st.button("🗑️", key=f"{cadastro_prefixo}_remover_{chave}", help="Remover este equipamento"):
                if len(itens_cadastro) > 1:
                    st.session_state[itens_key] = [
                        item_atual for item_atual in itens_cadastro
                        if item_atual["chave"] != chave
                    ]
                    st.rerun()
                else:
                    st.warning("O cadastro precisa ter pelo menos um equipamento.")
        dados_itens.append({
            "tipo": tipo,
            "marca": marca,
            "modelo": modelo.strip(),
            "service_tag": service_tag.strip().upper() or None,
        })

    col_adicionar, _ = st.columns([1, 8])
    with col_adicionar:
        if st.button("➕ Adicionar outro", key=f"{cadastro_prefixo}_adicionar"):
            proxima_chave = str(max(int(item["chave"]) for item in itens_cadastro) + 1)
            st.session_state[itens_key] = itens_cadastro + [{"chave": proxima_chave}]
            st.rerun()

    fotos = st.file_uploader(
        "Fotos do cadastro (Obrigatório - Máx. 10 fotos)*",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"{cadastro_prefixo}_fotos",
    )

    if st.button("Salvar Cadastro", key=f"{cadastro_prefixo}_salvar"):
        codigo = None
        tags = [item["service_tag"] for item in dados_itens if item["service_tag"]]
        tags_repetidas = len(tags) != len(set(tags))
        itens_invalidos = any(
            not item["tipo"]
            or (
                item["tipo"] != "Estação de Trabalho"
                and not item["marca"]
            )
            for item in dados_itens
        )

        if itens_invalidos or not colaborador.strip() or not fotos:
            st.error("Preencha o tipo e a marca dos equipamentos aplicáveis, o colaborador e anexe pelo menos uma foto.")
        elif len(fotos) > 10:
            st.error("Permitido anexar no máximo 10 fotos.")
        elif tags_repetidas:
            st.error("Não é permitido repetir a Etiqueta Patrimônio Mult no mesmo cadastro.")
        else:
            try:
                codigos = gerar_proximos_codigos_controle(len(dados_itens))
                codigo = codigos[0]
                check_tags = (
                    supabase.table("equipamentos")
                    .select("service_tag")
                    .in_("service_tag", tags)
                    .execute()
                    if tags
                    else None
                )
            except Exception as e:
                st.error(f"Erro ao preparar o cadastro no banco de dados: {e}")
                codigo = None
                check_tags = None

            if codigo is not None and check_tags and check_tags.data:
                tags_existentes = {
                    item.get("service_tag")
                    for item in check_tags.data
                    if item.get("service_tag")
                }
                st.error(f"Já existe equipamento cadastrado com a Etiqueta Patrimônio Mult: {', '.join(sorted(tags_existentes))}.")
            elif codigo is not None:
                urls_fotos = []
                erro_upload = False
                with st.spinner("Enviando fotos para o servidor..."):
                    for idx, foto in enumerate(fotos):
                        extensao = foto.name.split(".")[-1]
                        caminho_storage = f"{codigo}/{codigo}_{idx}_{int(datetime.now().timestamp())}.{extensao}"
                        try:
                            supabase.storage.from_("equipamentos-fotos").upload(caminho_storage, foto.read())
                            urls_fotos.append(
                                supabase.storage.from_("equipamentos-fotos").get_public_url(caminho_storage)
                            )
                        except Exception as e:
                            st.error(f"Falha ao enviar a foto {foto.name}: {e}")
                            erro_upload = True
                            break

                if not erro_upload:
                    registros = [
                        {
                            "codigo_controle": codigos[indice],
                            "service_tag": item["service_tag"],
                            "tipo": item["tipo"],
                            "marca": item["marca"],
                            "modelo": item["modelo"] or None,
                            "colaborador": colaborador.strip(),
                            "descricao": descricao.strip() or None,
                            "fotos": urls_fotos,
                            "status": "Ativo",
                            "criado_por": (
                                "Administrador"
                                if st.session_state.admin_authenticated
                                else "Acesso público"
                            ),
                            "data_registro": str(date.today()),
                        }
                        for indice, item in enumerate(dados_itens)
                    ]
                    erro_salvamento = None
                    for tentativa in range(3):
                        try:
                            supabase.table("equipamentos").insert(registros).execute()
                        except Exception as e:
                            erro_salvamento = e
                            if (
                                getattr(e, "code", None) == "23505"
                                and "equipamentos_codigo_controle_key" in str(e)
                                and tentativa < 2
                            ):
                                try:
                                    codigos = gerar_proximos_codigos_controle(len(dados_itens))
                                except Exception as erro_codigo:
                                    erro_salvamento = erro_codigo
                                    break
                                for indice, registro in enumerate(registros):
                                    registro["codigo_controle"] = codigos[indice]
                                continue
                        else:
                            erro_salvamento = None
                        break

                    if erro_salvamento is not None:
                        st.error(f"Erro ao salvar o cadastro no banco de dados: {erro_salvamento}")
                    else:
                        codigo_inicial = codigos[0]
                        codigo_final = codigos[-1]
                        faixa_codigos = (
                            codigo_inicial
                            if codigo_inicial == codigo_final
                            else f"{codigo_inicial} a {codigo_final}"
                        )
                        if st.session_state.admin_authenticated:
                            tipos_cadastrados = ", ".join(item["tipo"] for item in dados_itens)
                            log_msg = f'O administrador cadastrou os equipamentos "{tipos_cadastrados}", Códigos: {faixa_codigos}, Colaborador: "{colaborador.strip()}"'
                            registrar_log("Inserir", log_msg, colaborador.strip())

                        st.success(f"Cadastro salvo com {len(registros)} equipamento(s). Código(s): {faixa_codigos}.")
                        st.session_state.cadastro_versao += 1
                        st.rerun()

# --- 2. EDITAR CADASTRO ---
elif menu == "Editar Cadastro":
    st.header("Editar / Remover Cadastro de Equipamento")
    
    res_busca = supabase.table("equipamentos").select("*").execute()
    todos_equipamentos = res_busca.data if res_busca.data else []
    grupos_por_codigo = {}
    for equipamento in todos_equipamentos:
        codigo_grupo = str(equipamento.get("codigo_controle") or f"sem_codigo_{equipamento.get('id')}")
        grupos_por_codigo.setdefault(codigo_grupo, []).append(equipamento)

    equip_selecionado = None
    if not todos_equipamentos:
        st.warning("Nenhum equipamento cadastrado no banco de dados.")
    else:
        metodo_busca = st.radio("Como deseja localizar o cadastro?", ["Por busca textual", "Por Colaborador/Tipo"])
        opcoes_grupos = {
            f"{codigo} - {grupo[0].get('colaborador') or 'Sem colaborador'} ({len(grupo)} equipamento(s))": grupo
            for codigo, grupo in grupos_por_codigo.items()
        }

        if metodo_busca == "Por busca textual":
            busca_ref = st.text_input("Buscar cadastro (Código, Etiqueta Patrimônio Mult, tipo, marca, modelo ou colaborador):")
            if busca_ref:
                ref_lower = busca_ref.lower()
                codigos_encontrados = {
                    str(item.get("codigo_controle") or f"sem_codigo_{item.get('id')}")
                    for item in todos_equipamentos
                    if any(
                        ref_lower in str(item.get(campo, "")).lower()
                        for campo in (
                            "codigo_controle",
                            "service_tag",
                            "tipo",
                            "marca",
                            "modelo",
                            "colaborador",
                        )
                    )
                }
                opcoes_encontradas = {
                    label: grupo
                    for label, grupo in opcoes_grupos.items()
                    if str(grupo[0].get("codigo_controle") or f"sem_codigo_{grupo[0].get('id')}")
                    in codigos_encontrados
                }
                if not opcoes_encontradas:
                    st.warning("Nenhum cadastro foi localizado com essa referência.")
                else:
                    escolha = st.selectbox("Selecione o cadastro para editar:", list(opcoes_encontradas.keys()))
                    equip_selecionado = opcoes_encontradas[escolha]
        else:
            colaboradores_disponiveis = sorted({
                item["colaborador"]
                for item in todos_equipamentos
                if item.get("colaborador")
            })
            colab_escolhido = st.selectbox(
                "Selecione o Colaborador:",
                ["Selecione..."] + colaboradores_disponiveis,
            )
            if colab_escolhido != "Selecione...":
                equips_do_colab = [
                    item for item in todos_equipamentos
                    if item.get("colaborador") == colab_escolhido
                ]
                tipos_disponiveis = sorted({
                    item["tipo"] for item in equips_do_colab if item.get("tipo")
                })
                tipo_escolhido = st.selectbox(
                    "Selecione o Tipo de Equipamento:",
                    ["Todos"] + tipos_disponiveis,
                )
                grupos_encontrados = {
                    str(item.get("codigo_controle") or f"sem_codigo_{item.get('id')}")
                    for item in equips_do_colab
                    if tipo_escolhido == "Todos" or item.get("tipo") == tipo_escolhido
                }
                opcoes_encontradas = {
                    label: grupo
                    for label, grupo in opcoes_grupos.items()
                    if str(grupo[0].get("codigo_controle") or f"sem_codigo_{grupo[0].get('id')}")
                    in grupos_encontrados
                }
                if opcoes_encontradas:
                    escolha = st.selectbox("Selecione o cadastro:", list(opcoes_encontradas.keys()))
                    equip_selecionado = opcoes_encontradas[escolha]

    if equip_selecionado:
        st.markdown("---")
        equipamento_base = equip_selecionado[0]
        grupo_key = str(equipamento_base.get("id") or equipamento_base.get("codigo_controle"))
        itens_key = f"edicao_itens_{grupo_key}"
        ids_grupo = {item.get("id") for item in equip_selecionado if item.get("id") is not None}
        if itens_key not in st.session_state:
            st.session_state[itens_key] = [
                {**item, "chave_ui": str(item.get("id") or f"legado_{indice}")}
                for indice, item in enumerate(equip_selecionado)
            ]
            st.session_state[f"{itens_key}_contador"] = 0

        ed_codigo = st.text_input(
            "Código do Cadastro*",
            value=str(equipamento_base.get("codigo_controle") or ""),
            key=f"{itens_key}_codigo",
        )
        ed_colab = st.text_input(
            "Colaborador Responsável*",
            value=equipamento_base.get("colaborador") or "",
            key=f"{itens_key}_colaborador",
        )
        ed_desc = st.text_area(
            "Descrição (Máx. 240 car.)",
            value=equipamento_base.get("descricao") or "",
            max_chars=240,
            key=f"{itens_key}_descricao",
        )

        st.markdown("**Equipamentos do cadastro**")
        dados_itens_edicao = []
        itens_edicao = st.session_state[itens_key]
        for indice, item in enumerate(itens_edicao):
            chave = item["chave_ui"]
            tipos_opcoes = [""] + TIPOS_EQUIPAMENTO
            if item.get("tipo") and item["tipo"] not in tipos_opcoes:
                tipos_opcoes.append(item["tipo"])
            marcas_opcoes = [""] + MARCAS_EQUIPAMENTO
            if item.get("marca") and item["marca"] not in marcas_opcoes:
                marcas_opcoes.append(item["marca"])
            tipo_key = f"{itens_key}_tipo_{chave}"
            tipo_atual = st.session_state.get(tipo_key, item.get("tipo") or "")
            if tipo_atual == "Estação de Trabalho":
                col_tipo, col_status, col_lixeira = st.columns([5, 1.3, 0.6])
            else:
                col_tipo, col_marca, col_modelo, col_tag, col_status, col_lixeira = st.columns([1.7, 1.7, 1.7, 1.7, 1.3, 0.6])
            with col_tipo:
                tipo = st.selectbox(
                    "Tipo*",
                    tipos_opcoes,
                    index=tipos_opcoes.index(item.get("tipo") or ""),
                    key=tipo_key,
                )
            if tipo == "Estação de Trabalho":
                st.session_state.pop(f"{itens_key}_marca_{chave}", None)
                st.session_state.pop(f"{itens_key}_modelo_{chave}", None)
                st.session_state.pop(f"{itens_key}_tag_{chave}", None)
                marca = None
                modelo = ""
                service_tag = ""
            else:
                with col_marca:
                    marca = st.selectbox(
                        "Marca*",
                        marcas_opcoes,
                        index=marcas_opcoes.index(item.get("marca") or ""),
                        key=f"{itens_key}_marca_{chave}",
                    )
                with col_modelo:
                    modelo = st.text_input(
                        "Modelo",
                        value=item.get("modelo") or "",
                        key=f"{itens_key}_modelo_{chave}",
                    )
                with col_tag:
                    service_tag = st.text_input(
                        "Etiqueta Patrimônio Mult",
                        value=item.get("service_tag") or "",
                        key=f"{itens_key}_tag_{chave}",
                    )
            with col_status:
                status_opcoes = ["Ativo", "Baixado", "Inativo"]
                status_atual = item.get("status") or "Ativo"
                if status_atual not in status_opcoes:
                    status_opcoes.append(status_atual)
                status = st.selectbox(
                    "Status",
                    status_opcoes,
                    index=status_opcoes.index(status_atual),
                    key=f"{itens_key}_status_{chave}",
                )
            with col_lixeira:
                st.write("")
                if st.button("🗑️", key=f"{itens_key}_remover_{chave}", help="Remover este equipamento"):
                    if len(itens_edicao) > 1:
                        st.session_state[itens_key] = [
                            item_atual for item_atual in itens_edicao
                            if item_atual["chave_ui"] != chave
                        ]
                        st.rerun()
                    else:
                        st.warning("O cadastro precisa ter pelo menos um equipamento.")
            dados_itens_edicao.append({
                "id": item.get("id"),
                "chave_ui": chave,
                "tipo": tipo,
                "marca": marca,
                "modelo": modelo.strip(),
                "service_tag": service_tag.strip().upper() or None,
                "status": status,
            })

        if st.button("➕ Adicionar equipamento", key=f"{itens_key}_adicionar"):
            contador_key = f"{itens_key}_contador"
            contador = st.session_state[contador_key]
            st.session_state[contador_key] += 1
            st.session_state[itens_key] = itens_edicao + [{
                "id": None,
                "chave_ui": f"novo_{contador}",
                "tipo": "",
                "marca": "",
                "modelo": "",
                "service_tag": None,
                "status": "Ativo",
            }]
            st.rerun()

        fotos_por_grupo = []
        for item in equip_selecionado:
            for foto in obter_lista_fotos(item.get("fotos")):
                if foto not in fotos_por_grupo:
                    fotos_por_grupo.append(foto)
        st.write("**Fotos salvas atualmente:**")
        fotos_para_manter = []
        if fotos_por_grupo:
            cols = st.columns(10)
            for i, url_f in enumerate(fotos_por_grupo):
                with cols[i % 10]:
                    try:
                        caminho_relative = url_f.split("equipamentos-fotos/")[-1] if "equipamentos-fotos/" in url_f else url_f
                        bytes_foto = supabase.storage.from_("equipamentos-fotos").download(caminho_relative)
                        st.image(bytes_foto, use_container_width=True)
                    except Exception:
                        st.caption("⚠️ Erro")
                    if st.checkbox("Manter", value=True, key=f"{itens_key}_foto_{i}"):
                        fotos_para_manter.append(url_f)
        else:
            st.caption("Nenhuma foto cadastrada.")

        novas_fotos = st.file_uploader(
            "Adicionar Novas Fotos (Máx. 10 no cadastro)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"{itens_key}_novas_fotos",
        )
        col_salvar, col_deletar = st.columns(2)
        with col_salvar:
            btn_salvar = st.button("Atualizar Cadastro", key=f"{itens_key}_salvar")
        with col_deletar:
            btn_deletar = st.button("🗑️ Excluir Cadastro Completo", key=f"{itens_key}_deletar")

        if btn_salvar:
            codigo_novo = ed_codigo.strip().upper()
            tags = [item["service_tag"] for item in dados_itens_edicao if item["service_tag"]]
            tags_repetidas = len(tags) != len(set(tags))
            itens_invalidos = any(
                not item["tipo"]
                or (
                    item["tipo"] != "Estação de Trabalho"
                    and not item["marca"]
                )
                for item in dados_itens_edicao
            )
            codigo_duplicado = False
            if codigo_novo and codigo_novo != str(equipamento_base.get("codigo_controle") or "").upper():
                res_codigo = (
                    supabase.table("equipamentos")
                    .select("id")
                    .eq("codigo_controle", codigo_novo)
                    .execute()
                )
                codigo_duplicado = any(item.get("id") not in ids_grupo for item in (res_codigo.data or []))

            res_tags = (
                supabase.table("equipamentos")
                .select("id,service_tag")
                .in_("service_tag", tags)
                .execute()
                if tags
                else None
            )
            tags_existentes = {
                item.get("service_tag")
                for item in (res_tags.data if res_tags else [])
                if item.get("service_tag") and item.get("id") not in ids_grupo
            }

            if not codigo_novo:
                st.error("O campo Código do Cadastro é obrigatório.")
            elif not ed_colab.strip():
                st.error("O campo Colaborador Responsável é obrigatório.")
            elif not dados_itens_edicao:
                st.error("O cadastro precisa ter pelo menos um equipamento.")
            elif itens_invalidos:
                st.error("Selecione o tipo e a marca dos equipamentos aplicáveis.")
            elif tags_repetidas:
                st.error("Não é permitido repetir a Etiqueta Patrimônio Mult no mesmo cadastro.")
            elif tags_existentes:
                st.error(f"Já existe equipamento cadastrado com a Etiqueta Patrimônio Mult: {', '.join(sorted(tags_existentes))}.")
            elif codigo_duplicado:
                st.error(f"Já existe outro cadastro com o código {codigo_novo}.")
            else:
                urls_finais = list(fotos_para_manter)
                erro_upload = False
                if novas_fotos:
                    if len(urls_finais) + len(novas_fotos) > 10:
                        st.error("A soma das fotos salvas com as novas excede o limite máximo de 10.")
                        erro_upload = True
                    else:
                        for idx, foto in enumerate(novas_fotos):
                            extensao = foto.name.split(".")[-1]
                            caminho_storage = f"{codigo_novo}/{codigo_novo}_edit_{idx}_{int(datetime.now().timestamp())}.{extensao}"
                            try:
                                supabase.storage.from_("equipamentos-fotos").upload(caminho_storage, foto.read())
                                urls_finais.append(
                                    supabase.storage.from_("equipamentos-fotos").get_public_url(caminho_storage)
                                )
                            except Exception as e:
                                st.error(f"Erro ao subir foto complementar: {e}")
                                erro_upload = True
                                break

                if not erro_upload:
                    try:
                        ids_mantidos = {
                            item["id"] for item in dados_itens_edicao if item["id"] is not None
                        }
                        ids_removidos = ids_grupo - ids_mantidos
                        novos_registros = []
                        for item in dados_itens_edicao:
                            registro = {
                                "codigo_controle": codigo_novo,
                                "service_tag": item["service_tag"],
                                "tipo": item["tipo"],
                                "marca": item["marca"],
                                "modelo": item["modelo"] or None,
                                "colaborador": ed_colab.strip(),
                                "descricao": ed_desc.strip() or None,
                                "status": item["status"],
                                "fotos": urls_finais,
                            }
                            if item["id"] is None:
                                registro.update({
                                    "criado_por": "Administrador",
                                    "data_registro": str(date.today()),
                                })
                                novos_registros.append(registro)
                            else:
                                supabase.table("equipamentos").update(registro).eq("id", item["id"]).execute()
                        if novos_registros:
                            supabase.table("equipamentos").insert(novos_registros).execute()
                        if ids_removidos:
                            supabase.table("equipamentos").delete().in_("id", list(ids_removidos)).execute()
                    except Exception as e:
                        st.error(f"Erro ao atualizar o cadastro no banco de dados: {e}")
                    else:
                        registrar_log(
                            "Atualizar",
                            f'O administrador atualizou o cadastro {equipamento_base.get("codigo_controle")} (Novo código: {codigo_novo}; equipamentos: {len(dados_itens_edicao)}).',
                            ed_colab.strip(),
                        )
                        st.success("Cadastro atualizado com sucesso!")
                        st.rerun()

        if btn_deletar:
            try:
                supabase.table("equipamentos").delete().in_("id", list(ids_grupo)).execute()
            except Exception as e:
                st.error(f"Erro ao excluir o cadastro no banco de dados: {e}")
            else:
                registrar_log(
                    "Deletar",
                    f'O administrador deletou o cadastro {equipamento_base.get("codigo_controle")} com {len(ids_grupo)} equipamento(s).',
                    equipamento_base.get("colaborador", "Não informado"),
                )
                st.success("Cadastro removido do banco de dados!")
                st.rerun()

# --- 3. LISTA DE EQUIPAMENTOS ---
elif menu == "Lista de Equipamentos":
    st.header("Lista Geral de Equipamentos")
    itens_por_consulta = 1000
    dados_equipamentos = []
    inicio_consulta = 0

    while True:
        res_equip = (
            supabase.table("equipamentos")
            .select("*")
            .order("data_registro", desc=False)
            .range(inicio_consulta, inicio_consulta + itens_por_consulta - 1)
            .execute()
        )
        dados_pagina_consulta = res_equip.data or []
        dados_equipamentos.extend(dados_pagina_consulta)
        if len(dados_pagina_consulta) < itens_por_consulta:
            break
        inicio_consulta += itens_por_consulta

    if dados_equipamentos:
        df_completo = pd.DataFrame(dados_equipamentos)

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
        grupos_exibicao = {}
        for indice_linha, item in df_exibicao.iterrows():
            codigo_item = item.get("codigo_controle")
            chave_grupo = (
                str(codigo_item)
                if pd.notna(codigo_item) and str(codigo_item).strip()
                else f"sem_codigo_{item.get('id', indice_linha)}"
            )
            grupos_exibicao.setdefault(chave_grupo, []).append(item)
        lista_grupos = list(grupos_exibicao.values())

        if not filtro_ativo and df_exibicao.empty:
            st.info("Nenhum equipamento cadastrado ate o momento.")
        else:
            total_registros = len(lista_grupos)
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
            df_pagina = lista_grupos[inicio:fim]

            st.write(
                f"Exibindo {inicio + 1 if total_registros else 0} a "
                f"{min(fim, total_registros)} de {total_registros} cadastros:"
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

                    for deslocamento, (col, itens_grupo) in enumerate(
                        zip(cols, df_pagina[i:i + 4])
                    ):
                        with col:
                            item = itens_grupo[0]
                            status_grupo = [str(registro.get("status") or "-") for registro in itens_grupo]
                            is_inativo = all(status.lower() == "inativo" for status in status_grupo)
                            
                            with st.container(border=True):
                                # CORREÇÃO SOLICITADA: Se o equipamento estiver Inativo, aplica opacidade/transparência em todo o card
                                if is_inativo:
                                    st.markdown("<div style='opacity: 0.55; filter: grayscale(20%);'>", unsafe_allow_html=True)
                                
                                codigo_card = f"cadastro_{inicio + i + deslocamento}"
                                fotos = []
                                for registro in itens_grupo:
                                    for foto in obter_lista_fotos(registro.get("fotos")):
                                        if foto not in fotos:
                                            fotos.append(foto)

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
                                st.markdown(f"**Colaborador:** {item.get('colaborador') or '-'}")
                                for registro in itens_grupo:
                                    st.markdown(
                                        f"**Tipo:** {registro.get('tipo') or '-'}  \n"
                                        f"**Marca/Modelo:** {registro.get('marca') or '-'} / {registro.get('modelo') or '-'}  \n"
                                        f"**Etiqueta Patrimônio Mult:** {registro.get('service_tag') or '-'}"
                                    )
                                    status_atual = registro.get("status") or "-"
                                    if str(status_atual).lower() == "inativo":
                                        st.markdown(
                                            f"**Status:** <span style='color:red; font-weight:bold;'>{status_atual}</span>",
                                            unsafe_allow_html=True,
                                        )
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
elif menu == "Baixas":
    st.header("Gerenciamento de Baixas de Equipamentos")
    
    tab_listar, tab_nova = st.tabs(["Pesquisar Baixas", "➕ Nova Baixa"])
    
    with tab_listar:
        pesquisa_baixa = st.text_input("Pesquisar baixas criadas (Digite a Etiqueta Patrimônio Mult ou Motivo):")
        
        # 1. Filtra trazendo apenas as baixas que NÃO foram arquivadas historicamente
        res_baixas = supabase.table("baixas").select("*").eq("arquivado", False).order("data_baixa", desc=True).execute()
        
        if res_baixas.data:
            df_baixas = pd.DataFrame(res_baixas.data)
            
            # -----------------------------------------------------------------
            # SOLUÇÃO PARA DUPLICADOS: Mantém apenas a baixa mais recente de cada Etiqueta Patrimônio Mult
            # -----------------------------------------------------------------
            df_baixas = df_baixas.drop_duplicates(subset=["service_tag"], keep="first")
            
            # Busca todos os equipamentos para cruzar os dados de status
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
                # Contador para verificar se alguma baixa válida será exibida
                baixas_exibidas = 0
                
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
                    
                    # REGRA DE FILTRO: PULA A RENDERIZAÇÃO SE O EQUIPAMENTO NÃO FOR INATIVO
                    if status_atual_equip != "Inativo":
                        continue
                    
                    # Se chegou até aqui, incrementa o contador de baixas visíveis
                    baixas_exibidas += 1
                    
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
                                
                                # SÓ MOSTRA O BOTÃO SE FOR MASTER
                                st.markdown("---")
                                if st.button("🔄 Reativar Equipamento", key=f"btn_reativar_{id_baixa}", type="primary", use_container_width=True):
                                    with st.spinner("Reativando equipamento e removendo da lista..."):
                                        try:
                                            supabase.table("equipamentos").update({"status": "Ativo"}).eq("service_tag", st_atual).execute()
                                            supabase.table("baixas").update({"arquivado": True}).eq("id", id_baixa).execute()
                                            registrar_log(
                                                "Reativação",
                                                f'O administrador finalizou e ocultou a baixa do equipamento ST: {st_atual}.',
                                                dados_equip.get("colaborador", "Não informado"),
                                            )
                                            st.success(f"Equipamento {st_atual} reativado e removido do painel!")
                                            import time
                                            time.sleep(1)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao reativar equipamento: {e}")
                            else:
                                st.caption("Equipamento não localizado no banco.")
                
                # Caso existam baixas no banco mas todas já estejam com equipamentos Ativos
                if baixas_exibidas == 0:
                    st.info("Nenhum equipamento inativo listado nas baixas atuais.")
        else:
            st.info("Nenhum registro de baixa ativo no momento.")

    with tab_nova:
        st.subheader("Registrar Nova Baixa")
        
        # Mantemos a busca trazendo todos os equipamentos para que, caso dê algum erro, o usuário possa visualizar,
        # mas no selectbox exibiremos as opções disponíveis.
        res_equips_todos = supabase.table("equipamentos").select("service_tag", "tipo", "colaborador", "status").execute()
        
        if not res_equips_todos.data:
            st.warning("Não há equipamentos cadastrados disponíveis para baixa.")
        else:
            lista_equips = res_equips_todos.data
            dict_equips = {}
            
            for item in lista_equips:
                st_val = item.get("service_tag")
                if st_val and str(st_val).strip():
                    dict_equips[str(st_val).strip().upper()] = item
                    
            opcoes_st = ["Selecione..."] + sorted(list(dict_equips.keys()))
            st_selecionada = st.selectbox("Selecione a Etiqueta Patrimônio Mult (Obrigatório)*", options=opcoes_st)
            
            if st_selecionada != "Selecione...":
                dados_prev = dict_equips[st_selecionada]
                cor_status = "green" if dados_prev['status'] == "Ativo" else "red"
                st.info(f"**Prévia do Equipamento:**\n* **Tipo:** {dados_prev['tipo']}\n* **Colaborador Responsável:** {dados_prev['colaborador']}\n* **Status Atual:** :{cor_status}[{dados_prev['status']}]")
            
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
                        # VALIDAÇÃO DIRETA E EXATA: BLOQUEIA APENAS SE ESTIVER INATIVO NO BANCO
                        # -----------------------------------------------------------------
                        status_atual = dict_equips[st_selecionada].get("status")
                        
                        if status_atual == "Inativo":
                            st.error(f"⚠️ O equipamento {st_selecionada} já está Inativo! Resolva a baixa anterior (reative o equipamento) antes de abrir uma nova.")
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
                                        "criado_por": "Administrador",
                                        "arquivado": False
                                    }).execute()
                                    
                                    # Altera para Inativo
                                    supabase.table("equipamentos").update({"status": "Inativo"}).eq("service_tag", st_selecionada).execute()
                                    registrar_log(
                                        "Baixa",
                                        f'O administrador deu baixa no equipamento ST: {st_selecionada} por motivo de {motivo}.',
                                        dict_equips[st_selecionada].get("colaborador", "Não informado"),
                                    )
                                    
                                    st.success(f"Baixa efetuada e equipamento (ST: {st_selecionada}) definido como Inativo com sucesso!")
                                    import time
                                    time.sleep(2)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao processar a requisição no banco de dados: {e}")

# --- 5. RELATÓRIOS ---
elif menu == "Relatórios":
    st.header("Central de Relatórios de Equipamentos")
    
    op_relatorio = st.selectbox("Selecione o tipo de relatório desejado:", [
        "1. Relação de equipamentos cadastrados por período",
        "2. Relação de equipamentos por usuário específico",
        "3. Relação consolidada de todos os usuários",
        "4. Relatório de Todas as Baixas (por período)",
        "5. Relatório de Baixa por colaborador (por período)",
        "6. Relatório de Baixa por equipamento (por período)",
        "7. Relatório de Estatísticas de Baixa",
        "8. Relatório de Estatísticas Gerais"
    ])
    
    df_filtrado = pd.DataFrame()
    titulo_doc = ""
    is_consolidado_pdf = False
    is_estatisticas_gerais = False  # Flag para controle do novo relatório
    
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
                
    elif op_relatorio.startswith("4"):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_inicio = st.date_input("Data de Início Baixas", date.today())
        with col_d2:
            d_fim = st.date_input("Data de Fim Baixas", date.today())
            
        if st.button("Filtrar Todas as Baixas"):
            res = supabase.table("baixas").select("*").gte("data_baixa", str(d_inicio)).lte("data_baixa", str(d_fim)).execute()
            if res.data:
                df_filtrado = pd.DataFrame(res.data)
                titulo_doc = f"Histórico Geral de Baixas de {d_inicio.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}"
            else:
                st.warning("Nenhuma baixa cadastrada neste período.")

    elif op_relatorio.startswith("5"):
        res_colab = supabase.table("equipamentos").select("colaborador").execute()
        lista_colabs = list(set([item['colaborador'] for item in res_colab.data if item.get('colaborador')])) if res_colab.data else []
        lista_colabs = sorted(lista_colabs, key=str.lower)
        
        colab_selecionado = st.selectbox("Selecione o Colaborador para buscar baixas:", lista_colabs)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_inicio = st.date_input("Data de Início", date.today())
        with col_d2:
            d_fim = st.date_input("Data de Fim", date.today())
            
        if st.button("Filtrar Baixas por Colaborador") and colab_selecionado:
            res_eq = supabase.table("equipamentos").select("service_tag").eq("colaborador", colab_selecionado).execute()
            if res_eq.data:
                tags = [item["service_tag"] for item in res_eq.data]
                res_baixas = supabase.table("baixas").select("*").in_("service_tag", tags).gte("data_baixa", str(d_inicio)).lte("data_baixa", str(d_fim)).execute()
                if res_baixas.data:
                    df_filtrado = pd.DataFrame(res_baixas.data)
                    titulo_doc = f"Baixas do Colaborador {colab_selecionado} ({d_inicio.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')})"
                else:
                    st.warning(f"Nenhuma baixa encontrada para equipamentos deste colaborador no período.")
            else:
                st.warning("Esse colaborador não possui equipamentos registrados para rastrear baixas.")

    elif op_relatorio.startswith("6"):
        res_eq = supabase.table("equipamentos").select("service_tag").execute()
        lista_tags = list(set([item['service_tag'] for item in res_eq.data if item.get('service_tag')])) if res_eq.data else []
        lista_tags = sorted(lista_tags)
        
        st_selecionada = st.selectbox("Selecione a Etiqueta Patrimônio Mult do Equipamento:", lista_tags)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_inicio = st.date_input("Data de Início", date.today())
        with col_d2:
            d_fim = st.date_input("Data de Fim", date.today())
            
        if st.button("Filtrar Histórico do Equipamento") and st_selecionada:
            res = supabase.table("baixas").select("*").eq("service_tag", st_selecionada).gte("data_baixa", str(d_inicio)).lte("data_baixa", str(d_fim)).execute()
            if res.data:
                df_filtrado = pd.DataFrame(res.data)
                titulo_doc = f"Histórico de Baixas do Equipamento ST {st_selecionada} ({d_inicio.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')})"
            else:
                st.warning("Nenhuma baixa registrada para este equipamento no período selecionado.")

    elif op_relatorio.startswith("7"):
        st.subheader("📊 Indicadores e Estatísticas Gerais de Baixas")
        res_all_baixas = supabase.table("baixas").select("*").execute()
        if res_all_baixas.data:
            df_estatisticas = pd.DataFrame(res_all_baixas.data)
            
            total_baixas = len(df_estatisticas)
            baixas_arquivadas = len(df_estatisticas[df_estatisticas["arquivado"] == True])
            baixas_em_aberto = total_baixas - baixas_arquivadas
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Baixas no Histórico", total_baixas)
            m2.metric("Baixas Resolvidas (Reativados)", baixas_arquivadas)
            m3.metric("Equipamentos Atualmente Inativos", baixas_em_aberto)
            
            st.markdown("---")
            col_e1, col_e2 = st.columns(2)
            
            with col_e1:
                st.markdown("**🏆 Equipamentos com mais registros de Baixa:**")
                top_equipamentos = df_estatisticas["service_tag"].value_counts().reset_index()
                top_equipamentos.columns = ["Etiqueta Patrimônio Mult", "Quantidade de Baixas"]
                st.dataframe(top_equipamentos.head(5), use_container_width=True, hide_index=True)
                
            with col_e2:
                st.markdown("**👤 Usuários que mais registraram Baixas:**")
                top_usuarios = df_estatisticas["criado_por"].value_counts().reset_index()
                top_usuarios.columns = ["Responsável (E-mail)", "Baixas Criadas"]
                st.dataframe(top_usuarios.head(5), use_container_width=True, hide_index=True)
                
            st.markdown("**📋 Motivos mais frequentes de Baixas:**")
            top_motivos = df_estatisticas["motivo"].value_counts().reset_index()
            top_motivos.columns = ["Motivo", "Total"]
            st.dataframe(top_motivos, use_container_width=True, hide_index=True)
            
            df_filtrado = df_estatisticas
            titulo_doc = "Relatório Consolidado de Estatísticas de Baixas"
        else:
            st.info("Não há dados de baixas suficientes no banco para gerar estatísticas.")

    # --- OPÇÃO 8: RELATÓRIO DE ESTATÍSTICAS GERAIS ---
    elif op_relatorio.startswith("8"):
        st.subheader("📈 Relatório de Estatísticas Gerais")
        is_estatisticas_gerais = True
        titulo_doc = "Relatório de Estatísticas Gerais"
        
        res_eq = supabase.table("equipamentos").select("*").execute()
        res_bx = supabase.table("baixas").select("*").execute()
        
        if res_eq.data:
            df_eq_raw = pd.DataFrame(res_eq.data)
            df_bx_raw = pd.DataFrame(res_bx.data) if res_bx.data else pd.DataFrame()
            
            if 'id' in df_eq_raw.columns:
                df_eq_raw = df_eq_raw.drop_duplicates(subset=['id'], keep='last')
                
            # Filtro: Ignora equipamentos que contêm 'ESTAÇÃO' (case-insensitive)
            if 'tipo' in df_eq_raw.columns:
                filtro_estacao = df_eq_raw['tipo'].astype(str).str.contains('ESTAÇÃO|ESTACAO', case=False, na=False)
                df_eq_raw = df_eq_raw[~filtro_estacao]
                
                # Normalizar nome da coluna 'tipo' após o filtro
                df_eq_raw['tipo'] = df_eq_raw['tipo'].astype(str).str.strip().str.title()
            
            # --- PROCESSAMENTO DOS DADOS ---
            st_inativas = []
            if not df_bx_raw.empty:
                st_inativas = df_bx_raw[df_bx_raw["arquivado"] == False]["service_tag"].unique().tolist()
            
            df_eq_raw["Status"] = df_eq_raw["service_tag"].apply(lambda x: "Inativo" if x in st_inativas else "Ativo")
            
            total_cadastrados = len(df_eq_raw)
            total_ativos = len(df_eq_raw[df_eq_raw["Status"] == "Ativo"])
            
            df_com_colab = df_eq_raw.dropna(subset=['colaborador'])
            df_com_colab = df_com_colab[df_com_colab['colaborador'].str.strip() != ""]
            colaboradores_unicos = df_com_colab['colaborador'].nunique()
            
            df_ativos = df_com_colab[df_com_colab["Status"] == "Ativo"]
            
            colabs_alertas = []
            
            if 'colaborador' in df_ativos.columns and 'tipo' in df_ativos.columns:
                df_perifericos = df_ativos.groupby(['colaborador', 'tipo']).size().unstack(fill_value=0)
                
                for col_nome in ['Mouse', 'Teclado', 'Monitor']:
                    if col_nome not in df_perifericos.columns:
                        df_perifericos[col_nome] = 0
                
                for colab, row in df_perifericos.iterrows():
                    motivos_alerta = []
                    if row['Mouse'] == 0: motivos_alerta.append("Sem Mouse")
                    if row['Teclado'] == 0: motivos_alerta.append("Sem Teclado")
                    if row['Monitor'] > 1: motivos_alerta.append(f"Mais de 1 Monitor ({row['Monitor']})")
                    
                    if motivos_alerta:
                        colabs_alertas.append({
                            "Colaborador (Nome Completo)": colab,
                            "Inconsistência": ", ".join(motivos_alerta)
                        })
            df_alertas_perifericos = pd.DataFrame(colabs_alertas)
            
            # Ajuste definitivo apontando para 'codigo_controle'
            df_eq_raw['codigo_controle'] = df_eq_raw['codigo_controle'].astype(str).str.strip()
            df_codigos_nao_zero = df_eq_raw[~df_eq_raw['codigo_controle'].str.startswith('0', na=False)]
            df_codigos_nao_zero_filtrado = df_codigos_nao_zero[['colaborador', 'tipo', 'codigo_controle', 'Status']].rename(
                columns={'colaborador': 'Colaborador', 'tipo': 'Tipo Equipamento', 'codigo_controle': 'Código'}
            )
            
            df_inativos_lista = df_com_colab[df_com_colab["Status"] == "Inativo"][['colaborador', 'tipo', 'service_tag']].rename(
                columns={'colaborador': 'Colaborador', 'tipo': 'Tipo Equipamento', 'service_tag': 'Etiqueta Patrimônio Mult'}
            )
            
            # --- RENDERIZAÇÃO NA TELA ---
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Colaboradores com Equipamentos", colaboradores_unicos)
            kpi2.metric("Equipamentos Cadastrados", total_cadastrados)
            kpi3.metric("Equipamentos Ativos", total_ativos)
            
            st.markdown("---")
            
            # 🔄 MODIFICADO: Removido o gráfico de Status e transformado a Volumetria em Tabela
            st.markdown("**📊 Volumetria por Tipo de Equipamento (Geral)**")
            if 'tipo' in df_eq_raw.columns:
                tipo_counts = df_eq_raw["tipo"].value_counts().reset_index()
                tipo_counts.columns = ["Tipo de Equipamento", "Quantidade"]
                st.dataframe(tipo_counts, use_container_width=True, hide_index=True)
                
            st.markdown("---")
            
            st.markdown(f"#### 🚨 Kit de Periféricos Incompleto ou Excedente (Total: {len(df_alertas_perifericos)})")
            if not df_alertas_perifericos.empty:
                st.dataframe(df_alertas_perifericos, use_container_width=True, hide_index=True)
            else:
                st.success("Todos os colaboradores ativos possuem Mouse, Teclado e até 1 Monitor.")
                
            st.markdown("---")
            
            col_tab1, col_tab2 = st.columns(2)
            with col_tab1:
                st.markdown(f"#### 🏷️ Equipamentos sem etiqueta de patrimônio Mult (Total: {len(df_codigos_nao_zero_filtrado)})")
                if not df_codigos_nao_zero_filtrado.empty:
                    st.dataframe(df_codigos_nao_zero_filtrado, use_container_width=True, hide_index=True)
                    
                    # 🔄 MODIFICADO: Gráfico de "Tipos afetados" alterado para estilo Tabela
                    st.markdown("**Tipos afetados:**")
                    tipos_afetados = df_codigos_nao_zero_filtrado["Tipo Equipamento"].value_counts().reset_index()
                    tipos_afetados.columns = ["Tipo Equipamento", "Quantidade"]
                    st.dataframe(tipos_afetados, use_container_width=True, hide_index=True)
                else:
                    st.success("Todos os códigos de equipamentos começam com 0.")
                    
            with col_tab2:
                st.markdown(f"#### ⚠️ Equipamentos Atualmente em Baixa / Inativos (Total: {len(df_inativos_lista)})")
                if not df_inativos_lista.empty:
                    st.dataframe(df_inativos_lista, use_container_width=True, hide_index=True)
                    
                    # 🔄 MODIFICADO: Gráfico de "Tipos de equipamentos inativos" alterado para estilo Tabela
                    st.markdown("**Tipos de equipamentos inativos:**")
                    tipos_inativos = df_inativos_lista["Tipo Equipamento"].value_counts().reset_index()
                    tipos_inativos.columns = ["Tipo Equipamento", "Quantidade"]
                    st.dataframe(tipos_inativos, use_container_width=True, hide_index=True)
                else:
                    st.success("Não há equipamentos em baixa no momento.")
            
            df_filtrado = df_eq_raw 
            
        else:
            st.warning("Não há equipamentos cadastrados na base de dados para gerar as estatísticas.")
            
    # --- BLOCO DE DOWNLOAD E VISUALIZAÇÃO DOS RESULTADOS ---
    if not df_filtrado.empty:
        # Se for o relatório de estatísticas gerais, removemos o botão de PDF
        if is_estatisticas_gerais:
            st.markdown("---")
            # O bloco antigo com "Exportação do Dashboard" e o botão de PDF foi totalmente removido daqui.
        else:
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


# --- 6. LOG DE ATIVIDADES ---
elif menu == "Log de Atividades":
    st.header("Log de Atividades do Sistema")
    st.caption("Exibe todas as inserções, atualizações e exclusões em tempo real.")
    
    try:
        logs = supabase.table("logs_sistema").select("*").execute()
    except APIError as e:
        st.error(f"Erro ao consultar a tabela `logs_sistema` no Supabase: {e}")
        st.stop()
    
    if logs.data:
        df_logs = pd.DataFrame(logs.data)
        if "created_at" in df_logs.columns:
            df_logs = df_logs.sort_values("created_at", ascending=False)
        df_logs = df_logs.rename(columns={
            "created_at": "Data/Hora Evento",
            "colaborador": "Colaborador Responsável",
            "acao": "Operação",
            "resumo": "Histórico Detalhado"
        })
        if "id" in df_logs.columns:
            df_logs = df_logs.drop(columns=["id"])
            
        st.table(df_logs)
    else:
        st.info("Nenhuma atividade registrada nos logs.")


# --- Acesso à área administrativa no rodapé ---
st.markdown("---")
if not st.session_state.admin_authenticated:
    if st.button("Acessar área admin"):
        st.session_state.admin_access_requested = True
        st.rerun()
