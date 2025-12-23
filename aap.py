import streamlit as st
import pandas as pd
from PIL import Image
import io
import hashlib
import qrcode
import fitz  # PyMuPDF

# Configuração da Página
st.set_page_config(page_title="Caixa de Ferramentas Web", layout="wide", page_icon="🧰")

st.title("🧰 Caixa de Ferramentas (Versão Web)")
st.markdown("Adaptado do seu código Python original para rodar no navegador.")

# Menu Lateral (Substitui as Abas do Tkinter)
opcao = st.sidebar.selectbox(
    "Escolha uma ferramenta",
    [
        "Gerador de QR Code",
        "Unir Planilhas",
        "Calculadora de Hash",
        "Compressor de Imagem",
        "Detector de Duplicatas (Texto)",
        "Manipulador de PDF (Unir)"
    ]
)

# --- 1. GERADOR DE QR CODE ---
if opcao == "Gerador de QR Code":
    st.header("Gerador de QR Code")
    texto = st.text_input("Digite o texto ou Link:")
    
    if texto:
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(texto)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para bytes para exibir no navegador
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        st.image(byte_im, caption="Seu QR Code", width=300)
        
        st.download_button(
            label="Baixar QR Code",
            data=byte_im,
            file_name="qrcode.png",
            mime="image/png"
        )

# --- 2. UNIR PLANILHAS ---
elif opcao == "Unir Planilhas":
    st.header("Unir Planilhas (Excel/CSV)")
    col1, col2 = st.columns(2)
    
    file1 = col1.file_uploader("Planilha Principal", type=['xlsx', 'csv'])
    file2 = col2.file_uploader("Planilha Secundária", type=['xlsx', 'csv'])
    
    chave = st.text_input("Nome da coluna chave (ex: CPF, SKU, Email):")
    
    if file1 and file2 and chave:
        try:
            df1 = pd.read_excel(file1) if file1.name.endswith('.xlsx') else pd.read_csv(file1)
            df2 = pd.read_excel(file2) if file2.name.endswith('.xlsx') else pd.read_csv(file2)
            
            st.write(f"Planilha 1: {df1.shape} | Planilha 2: {df2.shape}")
            
            if st.button("Unir Planilhas"):
                # Normaliza a chave para evitar erros de espaço/maiúscula
                df1[chave] = df1[chave].astype(str).str.strip().str.lower()
                df2[chave] = df2[chave].astype(str).str.strip().str.lower()
                
                df_final = pd.merge(df1, df2, on=chave, how="inner")
                
                st.success(f"Sucesso! {len(df_final)} linhas combinadas.")
                st.dataframe(df_final.head())
                
                # Botão de download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False)
                
                st.download_button(
                    label="Baixar Planilha Unida",
                    data=output.getvalue(),
                    file_name="uniao_final.xlsx",
                    mime="application/vnd.ms-excel"
                )
        except Exception as e:
            st.error(f"Erro: {e}. Verifique se o nome da coluna chave está igual nas duas planilhas.")

# --- 3. CALCULADORA DE HASH ---
elif opcao == "Calculadora de Hash":
    st.header("Calculadora de Hash")
    file = st.file_uploader("Selecione um arquivo")
    
    if file:
        bytes_data = file.getvalue()
        md5 = hashlib.md5(bytes_data).hexdigest()
        sha256 = hashlib.sha256(bytes_data).hexdigest()
        
        st.code(f"MD5:    {md5}", language="text")
        st.code(f"SHA256: {sha256}", language="text")

# --- 4. COMPRESSOR DE IMAGEM ---
elif opcao == "Compressor de Imagem":
    st.header("Compressor de Imagem")
    file = st.file_uploader("Envie uma imagem", type=['jpg', 'png', 'jpeg'])
    qualidade = st.slider("Qualidade (%)", 10, 90, 50)
    
    if file:
        image = Image.open(file)
        st.image(image, caption="Original", width=300)
        
        buf = io.BytesIO()
        if image.mode == 'RGBA':
            image = image.convert('RGB')
            
        image.save(buf, format="JPEG", quality=qualidade, optimize=True)
        byte_im = buf.getvalue()
        
        tamanho_original = file.size / 1024
        tamanho_novo = len(byte_im) / 1024
        
        st.write(f"Tamanho Original: {tamanho_original:.2f} KB -> Novo: {tamanho_novo:.2f} KB")
        
        st.download_button("Baixar Imagem Comprimida", data=byte_im, file_name="comprimida.jpg", mime="image/jpeg")

# --- 5. DETECTOR DE DUPLICATAS ---
elif opcao == "Detector de Duplicatas (Texto)":
    st.header("Limpar Listas (TXT)")
    texto_input = st.text_area("Cole sua lista aqui (um item por linha) ou faça upload de txt:")
    file = st.file_uploader("Ou envie arquivo .txt", type=['txt'])
    
    conteudo = ""
    if file:
        conteudo = file.getvalue().decode("utf-8")
    elif texto_input:
        conteudo = texto_input
        
    if conteudo:
        linhas = [x.strip() for x in conteudo.splitlines() if x.strip()]
        unicos = sorted(list(set(linhas)))
        duplicados = len(linhas) - len(unicos)
        
        st.info(f"Total: {len(linhas)} | Únicos: {len(unicos)} | Duplicados removidos: {duplicados}")
        
        st.download_button("Baixar Lista Limpa", data="\n".join(unicos), file_name="lista_limpa.txt")

# --- 6. MANIPULADOR PDF (Unir) ---
elif opcao == "Manipulador de PDF (Unir)":
    st.header("Unir múltiplos PDFs")
    files = st.file_uploader("Selecione os PDFs", type=['pdf'], accept_multiple_files=True)
    
    if files and st.button("Unir PDFs"):
        doc_final = fitz.open()
        for pdf_file in files:
            with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
                doc_final.insert_pdf(doc)
        
        output = io.BytesIO()
        doc_final.save(output)
        
        st.success("PDFs unidos!")
        st.download_button("Baixar PDF Unido", data=output.getvalue(), file_name="unido.pdf", mime="application/pdf")