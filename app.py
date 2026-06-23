
                    for col, (_, item) in zip(cols, df_pagina.iloc[i:i + 4].iterrows()):
                        with col:
                            with st.container(border=True):
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
                                status_item = item.get('status') or '-'
                                if str(status_item).lower() == "inativo":
                                    st.markdown("**Status:** <span style='color:#c53030; font-weight:700;'>Inativo</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"**Status:** {status_item}")

                                descricao = item.get("descricao")
                                if descricao and str(descricao).strip() not in ["", "None", "nan"]:
                                    st.caption(str(descricao))

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
