import tkinter as tk
from tkinter import filedialog, messagebox
import unicodedata
import re
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill


def normalizar_nome(texto):
    """Remove acentos, pontuação, espaços extras e deixa tudo em minúsculo."""
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def obter_chaves_flexiveis(texto_normalizado):
    """Gera várias formas de reconhecimento para o nome (completo, iniciais/parciais e primeiro+último)."""
    partes = texto_normalizado.split()
    chaves = {texto_normalizado}  # Chave completa
    
    if len(partes) >= 2:
        # 1. Dois primeiros nomes (ex: joao silva)
        chaves.add(f"{partes[0]} {partes[1]}")
        # 2. Primeiro e último nome (ex: maria andrade)
        chaves.add(f"{partes[0]} {partes[-1]}")
        
    return chaves


def limpar_anydesk(valor):
    """Remove espaços em branco de dentro do número do AnyDesk."""
    if pd.isna(valor):
        return ""
    # Remove qualquer tipo de espaço em branco
    return re.sub(r'\s+', '', str(valor)).strip()


def main():
    root = tk.Tk()
    root.withdraw()

    # 1. Selecionar a planilha de origem
    caminho_origem = filedialog.askopenfilename(
        title="1. Selecione a PLANILHA DE ORIGEM",
        filetypes=[("Arquivos Excel", "*.xlsx *.xls")]
    )
    if not caminho_origem:
        return

    # 2. Selecionar a segunda planilha (com os dados do Anydesk)
    caminho_anydesk = filedialog.askopenfilename(
        title="2. Selecione a SEGUNDA PLANILHA (com a coluna do Anydesk)",
        filetypes=[("Arquivos Excel", "*.xlsx *.xls")]
    )
    if not caminho_anydesk:
        return

    try:
        df_origem = pd.read_excel(caminho_origem, dtype=str)
        df_anydesk = pd.read_excel(caminho_anydesk, dtype=str)

        col_nome_origem = "Nome do Colaborador"
        col_nome_anydesk = "Qual seu nome completo?"
        col_num_anydesk = "Informe o número do anydesk da sua máquina"

        if col_nome_origem not in df_origem.columns:
            messagebox.showerror("Erro", f"Coluna '{col_nome_origem}' não encontrada na planilha de origem.")
            return
        if col_nome_anydesk not in df_anydesk.columns or col_num_anydesk not in df_anydesk.columns:
            messagebox.showerror("Erro", "Colunas esperadas não encontradas na segunda planilha.")
            return

        # Padroniza visualmente os nomes da origem em CAIXA ALTA
        df_origem[col_nome_origem] = df_origem[col_nome_origem].fillna("").astype(str).str.upper().str.strip()

        # Dicionários de mapeamento
        mapa_anydesk_direto = {}
        mapa_anydesk_flexivel = {}
        mapa_nome_mais_longo = {}

        # Processa a segunda planilha (Anydesk) ordenando do maior para o menor nome
        df_anydesk_limpo = df_anydesk[df_anydesk[col_nome_anydesk].notna()].copy()
        df_anydesk_limpo["_completo_norm"] = df_anydesk_limpo[col_nome_anydesk].apply(normalizar_nome)
        df_anydesk_limpo = df_anydesk_limpo[df_anydesk_limpo["_completo_norm"] != ""]
        
        # Limpa os espaços dos números do AnyDesk
        df_anydesk_limpo[col_num_anydesk] = df_anydesk_limpo[col_num_anydesk].apply(limpar_anydesk)

        # Ordena por tamanho do texto (decrescente) para priorizar o nome mais completo
        df_anydesk_limpo["_tamanho"] = df_anydesk_limpo["_completo_norm"].str.len()
        df_anydesk_limpo = df_anydesk_limpo.sort_values("_tamanho", ascending=False)

        for _, row in df_anydesk_limpo.iterrows():
            c_comp = row["_completo_norm"]
            any_val = row[col_num_anydesk]
            nome_original = str(row[col_nome_anydesk]).strip().upper()
            
            if any_val:
                mapa_anydesk_direto[c_comp] = any_val
                
            chaves = obter_chaves_flexiveis(c_comp)
            for chave in chaves:
                if any_val:
                    mapa_anydesk_flexivel[chave] = any_val
                if chave not in mapa_nome_mais_longo or len(nome_original) > len(mapa_nome_mais_longo[chave]):
                    mapa_nome_mais_longo[chave] = nome_original

        # Aplica os cruzamentos na planilha de origem
        anydesk_resultados = []
        chaves_encontradas_origem = set()

        for idx, row in df_origem.iterrows():
            nome_orig = str(row[col_nome_origem])
            c_comp_orig = normalizar_nome(nome_orig)
            chaves_orig = obter_chaves_flexiveis(c_comp_orig)

            valor_any = ""
            nome_escolhido = nome_orig

            # 1. Tenta bater direto pela chave completa
            if c_comp_orig in mapa_anydesk_direto:
                valor_any = mapa_anydesk_direto[c_comp_orig]
                chaves_encontradas_origem.update(chaves_orig)
            else:
                # 2. Tenta bater pelas chaves flexíveis
                for chave in chaves_orig:
                    if chave in mapa_anydesk_flexivel:
                        valor_any = mapa_anydesk_flexivel[chave]
                        if chave in mapa_nome_mais_longo:
                            nome_escolhido = mapa_nome_mais_longo[chave]
                        chaves_encontradas_origem.update(chaves_orig)
                        break

            df_origem.at[idx, col_nome_origem] = nome_escolhido
            anydesk_resultados.append(valor_any)

        df_origem["Anydesk"] = anydesk_resultados

        # Identifica quem está no AnyDesk mas não casou na origem
        novas_linhas = []
        for _, row_any in df_anydesk_limpo.iterrows():
            c_comp = row_any["_completo_norm"]
            chaves_any = obter_chaves_flexiveis(c_comp)
            
            if not any(chave in chaves_encontradas_origem for chave in chaves_any):
                nome_maiusculo = str(row_any[col_nome_anydesk]).strip().upper()
                nova_linha = {
                    col_nome_origem: nome_maiusculo,
                    "Anydesk": row_any[col_num_anydesk]
                }
                for col in df_origem.columns:
                    if col not in nova_linha:
                        nova_linha[col] = ""
                novas_linhas.append(nova_linha)
                chaves_encontradas_origem.update(chaves_any)

        linha_inicio_extras = len(df_origem) + 2
        linha_fim_extras = None

        if novas_linhas:
            df_extras = pd.DataFrame(novas_linhas)
            df_origem = pd.concat([df_origem, df_extras], ignore_index=True)
            linha_fim_extras = linha_inicio_extras + len(novas_linhas) - 1

        # 3. Salvar arquivo
        caminho_saida = filedialog.asksaveasfilename(
            title="Salvar planilha tratada como...",
            defaultextension=".xlsx",
            initialfile="Planilha_Tratada_Anydesk.xlsx",
            filetypes=[("Arquivos Excel", "*.xlsx")]
        )
        if not caminho_saida:
            return

        df_origem.to_excel(caminho_saida, index=False)

        # 4. Formatação com OpenPyXL
        wb = load_workbook(caminho_saida)
        ws = wb.active

        col_idx_anydesk = None
        for cell in ws[1]:
            if cell.value == "Anydesk":
                col_idx_anydesk = cell.column
                break

        preenchimento_vermelho = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
        preenchimento_amarelo = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

        if linha_fim_extras:
            for row in range(linha_inicio_extras, linha_fim_extras + 1):
                for col in range(1, ws.max_column + 1):
                    ws.cell(row=row, column=col).fill = preenchimento_amarelo

        if col_idx_anydesk:
            limite_vermelho = linha_inicio_extras if linha_fim_extras else ws.max_row + 1
            for row in range(2, limite_vermelho):
                celula = ws.cell(row=row, column=col_idx_anydesk)
                if celula.value is None or str(celula.value).strip() == "":
                    celula.value = None
                    celula.fill = preenchimento_vermelho

        for col in ws.columns:
            max_length = 0
            column_letter = col[0].column_letter
            for cell in col:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    pass
            ws.column_dimensions[column_letter].width = max(max_length + 4, 15)

        wb.save(caminho_saida)
        messagebox.showinfo("Sucesso!", f"Planilha gerada com sucesso em:\n{caminho_saida}")

    except Exception as e:
        messagebox.showerror("Erro inesperado", f"Ocorreu um erro ao processar:\n{str(e)}")


if __name__ == "__main__":
    main()
