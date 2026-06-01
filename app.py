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
