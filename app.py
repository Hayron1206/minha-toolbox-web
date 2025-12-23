import streamlit as st
import pandas as pd
from PIL import Image
import io
import hashlib
import qrcode
import fitz  # PyMuPDF

# --- CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(
    page_title="Toolbox Pro",
    page_icon="🧰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GERENCIAMENTO DE ESTADO (NAVEGAÇÃO) ---
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def navigate_to(page_name):
    st.session_state.page = page_name

# --- CSS PERSONALIZADO (DESIGN SYSTEM) ---
st.markdown("""
<style>
    /* Importando fonte Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* Reset e Fonte Geral */
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: #2C3E50;
    }

    /* Fundo Geral */
    .stApp {
        background-color: #F8F9FA;
    }

    /* Banner Hero */
    .hero-banner {
        background: linear-gradient(90deg, #4A90E2 0%, #63A4FF 100%);
        padding: 3rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.2);
    }
    .hero-banner h1 {
        color: white !important;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .hero-banner p {
        font-size: 1.1rem;
        opacity: 0.9;
    }

    /* Cards do Dashboard */
    .dashboard-card {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        text-align: center;
        height: 100%;
        transition: transform 0.2s;
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        border-color: #4A90E2;
    }
    .card-icon {
        font-size: 40px;
        margin-bottom: 15px;
        background: #F0F7FF;
        width: 80px;
        height: 80px;
        line-height: 80px;
        border-radius: 50%;
        margin: 0 auto 20px auto;
        display: block;
    }
    .card-title {
        font-weight: 700;
        font-size: 1.2rem;
        margin-bottom: 10px;
        display: block;
    }
    .card-desc {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 20px;
        display: block;
    }

    /* Botões Estilizados */
    div.stButton > button {
        background-color: #4A90E2;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #357ABD;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
        transform: translateY(-1px);
    }
    
    /* Input Fields e Uploaders */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #E0E0E0;
    }
    .stFileUploader {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px dashed #4A90E2;
    }

    /* Sidebar Fix */
    section[data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #E0E0E0;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (MENU LATERAL) ---
with st.sidebar:
    st.markdown("## 🧰 Toolbox Pro")
    st.markdown("---")
    
    if st.button("🏠 Dashboard", use_container_width=True):
        navigate_to("Dashboard")
    
    st.caption("FERRAMENTAS")
    
    if st.button("📱 Gerador QR Code", use_container_width=True):
        navigate_to("QR Code")
    
    if st.button("📊 Unir Planilhas", use_container_width=True):
        navigate_to("Unir Planilhas")
        
    if st.button("📄 PDF Tools", use_container_width=True):
        navigate_to("PDF Tools")
        
    if st.button("🧹 Limpar Listas", use_container_width=True):
        navigate_to("Limpar Listas")
        
    if st.button("🖼️ Compressor Img", use_container_width=True):
        navigate_to("Compressor")

    st.markdown("---")
    st.info("Versão Web 1.0")

# ==============================================================================
# PÁGINA: DASHBOARD (HOME)
# ==============================================================================
if st.session_state.page == "Dashboard":
    # Banner Hero
    st.markdown("""
        <div class="hero-banner">
            <h1>👋 Bem-vindo à sua Toolbox</h1>
            <p>Selecione uma ferramenta abaixo para começar a trabalhar.</p>
        </div>
    """, unsafe_allow_html=True)

    # Grid de Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="dashboard-card">
            <span class="card-icon">📱</span>
            <span class="card-title">QR Code</span>
            <span class="card-desc">Gere códigos QR para links e textos.</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir QR Code", key="btn_home_qr", on_click=navigate_to, args=("QR Code",))

    with col2:
        st.markdown("""
        <div class="dashboard-card">
            <span class="card-icon">📊</span>
            <span class="card-title">Planilhas</span>
            <span class="card-desc">Una múltiplos arquivos Excel ou CSV.</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir Planilhas", key="btn_home_xls", on_click=navigate_to, args=("Unir Planilhas",))

    with col3:
        st.markdown("""
        <div class="dashboard-card">
            <span class="card-icon">📄</span>
            <span class="card-title">PDF Master</span>
            <span class="card-desc">Una documentos PDF em um único arquivo.</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir PDFs", key="btn_home_pdf", on_click=navigate_to, args=("PDF Tools",))

    with col4:
        st.markdown("""
        <div class="dashboard-card">
            <span class="card-icon">🧹</span>
            <span class="card-title">Listas</span>
            <span class="card-desc">Remova duplicatas de textos.</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir Limpeza", key="btn_home_list", on_click=navigate_to, args=("Limpar Listas",))


# ==============================================================================
# PÁGINA: QR CODE
# ==============================================================================
elif st.session_state.page == "QR Code":
    st.title("📱 Gerador de QR Code")
    st.markdown("---")
    
    col_config, col_preview = st.columns([1, 1])
    
    with col_config:
        st.subheader("Configuração")
        texto = st.text_input("Conteúdo (Link ou Texto):", placeholder="https://seu-site.com")
        cor_fill = st.color_picker("Cor do Código", "#000000")
        cor_back = st.color_picker("Cor do Fundo", "#FFFFFF")
        
    with col_preview:
        st.subheader("Resultado")
        if texto:
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(texto)
            qr.make(fit=True)
            img = qr.make_image(fill_color=cor_fill, back_color=cor_back)
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.image(byte_im, width=300)
            
            st.download_button(
                label="⬇️ Baixar QR Code (PNG)",
                data=byte_im,
                file_name="qrcode.png",
                mime="image/png"
            )
        else:
            st.info("Digite algo ao lado para gerar o código.")

# ==============================================================================
# PÁGINA: UNIR PLANILHAS
# ==============================================================================
elif st.session_state.page == "Unir Planilhas":
    st.title("📊 Unir Planilhas (Excel/CSV)")
    st.markdown("Junte dois arquivos baseados em uma coluna comum (Ex: CPF, SKU).")
    st.markdown("---")

    col1, col2 = st.columns(2)
    file1 = col1.file_uploader("Arquivo Principal", type=['xlsx', 'csv'])
    file2 = col2.file_uploader("Arquivo Secundário", type=['xlsx', 'csv'])
    
    chave = st.text_input("Nome da Coluna Chave:", placeholder="Ex: cpf, email, id_produto")
    
    if file1 and file2 and chave:
        if st.button("🔄 Processar e Unir Arquivos"):
            try:
                df1 = pd.read_excel(file1) if file1.name.endswith('.xlsx') else pd.read_csv(file1)
                df2 = pd.read_excel(file2) if file2.name.endswith('.xlsx') else pd.read_csv(file2)
                
                # Normalização básica
                df1[chave] = df1[chave].astype(str).str.strip().str.lower()
                df2[chave] = df2[chave].astype(str).str.strip().str.lower()
                
                df_final = pd.merge(df1, df2, on=chave, how="inner")
                
                st.success(f"Sucesso! {len(df_final)} linhas combinadas.")
                st.dataframe(df_final.head())
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False)
                
                st.download_button(
                    label="⬇️ Baixar Planilha Unificada",
                    data=output.getvalue(),
                    file_name="planilha_unida.xlsx",
                    mime="application/vnd.ms-excel"
                )
            except Exception as e:
                st.error(f"Erro ao processar: {e}. Verifique se o nome da coluna chave está correto.")

# ==============================================================================
# PÁGINA: PDF TOOLS
# ==============================================================================
elif st.session_state.page == "PDF Tools":
    st.title("📄 Ferramentas de PDF")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Unir PDFs", "Extrair Imagens (Beta)"])
    
    with tab1:
        st.subheader("Unir Múltiplos PDFs")
        files = st.file_uploader("Selecione os arquivos PDF", type=['pdf'], accept_multiple_files=True)
        
        if files and st.button("Juntar PDFs"):
            doc_final = fitz.open()
            for pdf_file in files:
                with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
                    doc_final.insert_pdf(doc)
            
            output = io.BytesIO()
            doc_final.save(output)
            st.success("PDFs unidos com sucesso!")
            st.download_button("⬇️ Baixar PDF Unido", output.getvalue(), "unido.pdf", "application/pdf")

    with tab2:
        st.info("Funcionalidade em desenvolvimento para extração de páginas.")

# ==============================================================================
# PÁGINA: LIMPAR LISTAS
# ==============================================================================
elif st.session_state.page == "Limpar Listas":
    st.title("🧹 Limpeza de Texto")
    st.markdown("Remove duplicatas e ordena listas.")
    st.markdown("---")
    
    txt_input = st.text_area("Cole sua lista aqui (um item por linha):", height=200)
    
    if txt_input:
        linhas = [x.strip() for x in txt_input.splitlines() if x.strip()]
        unicos = sorted(list(set(linhas)))
        duplicados = len(linhas) - len(unicos)
        
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Total Original", len(linhas))
        col_res2.metric("Duplicatas Removidas", duplicados)
        
        st.download_button("⬇️ Baixar Lista Limpa (.txt)", "\n".join(unicos), "lista_limpa.txt")

# ==============================================================================
# PÁGINA: COMPRESSOR
# ==============================================================================
elif st.session_state.page == "Compressor":
    st.title("🖼️ Compressor de Imagem")
    st.markdown("---")
    
    uploaded_img = st.file_uploader("Envie uma imagem (JPG/PNG)", type=['jpg', 'png', 'jpeg'])
    qualidade = st.slider("Qualidade da Compressão", 10, 90, 60)
    
    if uploaded_img:
        image = Image.open(uploaded_img)
        
        buf = io.BytesIO()
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        image.save(buf, format="JPEG", quality=qualidade, optimize=True)
        byte_im = buf.getvalue()
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Original", use_container_width=True)
            st.caption(f"Tamanho: {uploaded_img.size / 1024:.1f} KB")
            
        with col2:
            st.image(byte_im, caption="Comprimida", use_container_width=True)
            st.caption(f"Tamanho: {len(byte_im) / 1024:.1f} KB")
            
        st.download_button("⬇️ Baixar Imagem Otimizada", byte_im, "imagem_comprimida.jpg", "image/jpeg")
