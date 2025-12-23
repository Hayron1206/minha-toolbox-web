import streamlit as st
import pandas as pd
from PIL import Image
import io
import hashlib
import qrcode
import fitz  # PyMuPDF
import time

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
    # Rerun experimental para forçar atualização imediata da sidebar se necessário
    # st.experimental_rerun() 

# --- CSS PERSONALIZADO (DESIGN SYSTEM PREMIUM) ---
st.markdown("""
<style>
    /* Importando fonte Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* === RESET GLOBAL === */
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* Cores do Texto */
    h1, h2, h3, h4, h5, h6 { color: #1E293B; font-weight: 700; letter-spacing: -0.02em; }
    p, li, span, label { color: #334155; }
    
    /* Fundo Geral com Gradiente Sutil */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
    }

    /* === SIDEBAR PREMIUM === */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
        box-shadow: 4px 0 24px rgba(0,0,0,0.02);
    }
    
    /* === HERO BANNER (DEGRADÊ MODERNO) === */
    .hero-banner {
        background: linear-gradient(120deg, #2563EB 0%, #3B82F6 100%);
        padding: 4rem 3rem;
        border-radius: 24px;
        color: white;
        margin-bottom: 3rem;
        box-shadow: 0 20px 40px -10px rgba(37, 99, 235, 0.3);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -20%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 60%);
        transform: rotate(30deg);
    }
    .hero-banner h1 { color: white !important; font-size: 3rem; margin-bottom: 1rem; }
    .hero-banner p { color: rgba(255,255,255,0.9) !important; font-size: 1.25rem; font-weight: 300; }

    /* === CARDS FLUTUANTES === */
    .dashboard-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid #F1F5F9;
        box-shadow: 0 10px 30px -5px rgba(0,0,0,0.05);
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
        position: relative;
        top: 0;
    }
    .dashboard-card:hover {
        top: -8px;
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.1);
        border-color: #BFDBFE;
    }
    .card-icon {
        font-size: 48px;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        width: 96px;
        height: 96px;
        line-height: 96px;
        border-radius: 24px;
        margin: 0 auto 1.5rem auto;
        display: block;
        color: #2563EB;
    }
    .card-title { font-weight: 700; font-size: 1.25rem; color: #1E293B !important; margin-bottom: 0.5rem; display: block; }
    .card-desc { color: #64748B !important; font-size: 0.95rem; line-height: 1.5; margin-bottom: 1.5rem; display: block; }

    /* === BOTÕES CUSTOMIZADOS === */
    /* Botão Primário (Ação) */
    div.stButton > button {
        background: linear-gradient(to bottom, #3B82F6, #2563EB);
        color: white !important;
        border: 1px solid #1D4ED8;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
        width: 100%;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
        filter: brightness(110%);
    }
    div.stButton > button:active {
        transform: translateY(0);
    }
    
    /* Ajuste para botões secundários na sidebar (opcional, mantendo padrão por enquanto) */

    /* === INPUTS E FORMS === */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        color: #1E293B !important;
        padding: 10px 12px;
        transition: border-color 0.2s;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Uploader */
    .stFileUploader {
        background-color: #F8FAFC;
        border: 2px dashed #CBD5E1;
        border-radius: 16px;
        padding: 2rem;
        transition: border-color 0.2s;
    }
    .stFileUploader:hover {
        border-color: #3B82F6;
        background-color: #EFF6FF;
    }
    .stFileUploader label { font-weight: 600; color: #475569 !important; }
    .stFileUploader small { color: #94A3B8 !important; }

    /* === FOOTER === */
    .footer {
        text-align: center;
        margin-top: 4rem;
        padding: 2rem;
        border-top: 1px solid #E2E8F0;
        color: #94A3B8;
        font-size: 0.875rem;
    }
    
    /* Badge de Status */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .badge-blue { background-color: #DBEAFE; color: #1E40AF; }
    .badge-green { background-color: #DCFCE7; color: #166534; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (MENU LATERAL) ---
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="background: linear-gradient(135deg, #2563EB, #1E40AF); width: 64px; height: 64px; border-radius: 16px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto; box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.4);">
            <span style="font-size: 32px;">🧰</span>
        </div>
        <h2 style="margin:0; font-size: 1.25rem;">Toolbox Pro</h2>
        <p style="margin:0; font-size: 0.8rem; color: #94A3B8; font-weight: 500;">SUITE DE FERRAMENTAS</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Menu Navigation
    st.markdown('<p style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; margin-bottom: 0.5rem; letter-spacing: 0.05em;">MENU PRINCIPAL</p>', unsafe_allow_html=True)
    
    if st.button("🏠 Dashboard", use_container_width=True): navigate_to("Dashboard")
    
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; margin-bottom: 0.5rem; letter-spacing: 0.05em;">FERRAMENTAS</p>', unsafe_allow_html=True)
    
    if st.button("📱 Gerador QR Code", use_container_width=True): navigate_to("QR Code")
    if st.button("📊 Unir Planilhas", use_container_width=True): navigate_to("Unir Planilhas")
    if st.button("📄 PDF Tools", use_container_width=True): navigate_to("PDF Tools")
    if st.button("🧹 Limpar Listas", use_container_width=True): navigate_to("Limpar Listas")
    if st.button("🖼️ Compressor Img", use_container_width=True): navigate_to("Compressor")

    st.markdown("---")
    
    # Card de Info no Sidebar
    st.markdown("""
    <div style="background: #F8FAFC; padding: 1rem; border-radius: 12px; border: 1px solid #E2E8F0;">
        <p style="font-size: 0.8rem; margin-bottom: 0.5rem;"><strong>Status do Sistema</strong></p>
        <span class="status-badge badge-green">● Online</span>
        <p style="font-size: 0.7rem; color: #94A3B8; margin-top: 0.5rem;">v1.2.0 • Web App</p>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# PÁGINA: DASHBOARD (HOME)
# ==============================================================================
if st.session_state.page == "Dashboard":
    # Banner Hero
    st.markdown("""
        <div class="hero-banner">
            <div>
                <span class="status-badge badge-blue" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); margin-bottom: 1rem;">NOVIDADE: COMPRESSOR 2.0</span>
                <h1>Sua caixa de ferramentas,<br>agora na nuvem.</h1>
                <p>Otimize seu fluxo de trabalho com ferramentas rápidas, seguras e gratuitas.<br>Selecione uma opção abaixo para começar.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Grid de Cards
    st.markdown("### 🚀 Acesso Rápido")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="dashboard-card">
            <span class="card-icon">📱</span>
            <span class="card-title">QR Code</span>
            <span class="card-desc">Crie códigos QR instantâneos para links, Wi-Fi e textos.</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Acessar QR Code →", key="btn_home_qr", on_click=navigate_to, args=("QR Code",))

    with col2:
        st.markdown("""
        <div class="dashboard-card">
            <span class="card-icon">📊</span>
            <span class="card-title">Planilhas</span>
            <span class="card-desc">Combine arquivos Excel ou CSV em segundos.</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Acessar Planilhas →", key="btn_home_xls", on_click=navigate_to, args=("Unir Planilhas",))

    with col3:
        st.markdown("""
        <div class="dashboard-card">
            <span class="card-icon">📄</span>
            <span class="card-title">PDF Master</span>
            <span class="card-desc">Una múltiplos PDFs em um único documento organizado.</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Acessar PDFs →", key="btn_home_pdf", on_click=navigate_to, args=("PDF Tools",))

    with col4:
        st.markdown("""
        <div class="dashboard-card">
            <span class="card-icon">🧹</span>
            <span class="card-title">Listas</span>
            <span class="card-desc">Limpe duplicatas e ordene listas de texto.</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Acessar Limpeza →", key="btn_home_list", on_click=navigate_to, args=("Limpar Listas",))

    # Features Section (Extra Visual)
    st.markdown("<br><hr style='border-top: 1px solid #E2E8F0;'><br>", unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.info("🔒 **100% Seguro:** Seus arquivos são processados na memória e nunca são salvos.")
    with f_col2:
        st.info("⚡ **Rápido:** Processamento instantâneo usando Python otimizado.")
    with f_col3:
        st.info("📱 **Responsivo:** Funciona no computador, tablet e celular.")


# ==============================================================================
# PÁGINA: QR CODE
# ==============================================================================
elif st.session_state.page == "QR Code":
    st.markdown("## 📱 Gerador de QR Code")
    st.markdown("Transforme qualquer texto ou link em uma imagem escaneável.")
    st.markdown("---")
    
    col_config, col_preview = st.columns([1, 1], gap="large")
    
    with col_config:
        st.markdown("### 1. Configuração")
        st.markdown('<div style="background:white; padding:2rem; border-radius:16px; border:1px solid #E2E8F0;">', unsafe_allow_html=True)
        texto = st.text_input("Conteúdo (Link ou Texto):", placeholder="https://seu-site.com")
        
        c1, c2 = st.columns(2)
        with c1: cor_fill = st.color_picker("Cor do Código", "#000000")
        with c2: cor_back = st.color_picker("Cor do Fundo", "#FFFFFF")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_preview:
        st.markdown("### 2. Resultado")
        st.markdown('<div style="background:white; padding:2rem; border-radius:16px; border:1px solid #E2E8F0; text-align:center; min-height: 300px; display:flex; flex-direction:column; justify-content:center; align-items:center;">', unsafe_allow_html=True)
        
        if texto:
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(texto)
            qr.make(fit=True)
            img = qr.make_image(fill_color=cor_fill, back_color=cor_back)
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.image(byte_im, width=250)
            st.success("QR Code Gerado!")
            
            st.download_button(
                label="⬇️ Baixar Imagem (PNG)",
                data=byte_im,
                file_name="qrcode.png",
                mime="image/png"
            )
        else:
            st.markdown('<span style="font-size:3rem; opacity:0.2;">📷</span>', unsafe_allow_html=True)
            st.caption("Preencha o conteúdo ao lado para visualizar.")
            
        st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# PÁGINA: UNIR PLANILHAS
# ==============================================================================
elif st.session_state.page == "Unir Planilhas":
    st.markdown("## 📊 Unir Planilhas")
    st.markdown("Ferramenta poderosa para 'VLOOKUP' automático entre dois arquivos.")
    st.markdown("---")

    with st.expander("ℹ️ Como funciona? (Clique para ler)", expanded=True):
        st.write("1. Envie a planilha **Principal** (ex: Lista de Vendas).")
        st.write("2. Envie a planilha **Secundária** (ex: Cadastro de Clientes).")
        st.write("3. Indique o **nome da coluna** que existe nas duas (ex: 'CPF' ou 'ID').")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Arquivo Principal")
        file1 = st.file_uploader("Upload Planilha 1", type=['xlsx', 'csv'], key="f1")
    with col2:
        st.markdown("##### Arquivo Secundário")
        file2 = st.file_uploader("Upload Planilha 2", type=['xlsx', 'csv'], key="f2")
    
    st.markdown("<br>", unsafe_allow_html=True)
    chave = st.text_input("🔑 Nome da Coluna Chave (Comum aos dois arquivos):", placeholder="Ex: cpf, email, id_produto")
    
    if file1 and file2 and chave:
        if st.button("🚀 Processar e Unir Arquivos", type="primary"):
            with st.spinner("Lendo arquivos..."):
                try:
                    time.sleep(0.5) # Simula processamento visual
                    df1 = pd.read_excel(file1) if file1.name.endswith('.xlsx') else pd.read_csv(file1)
                    df2 = pd.read_excel(file2) if file2.name.endswith('.xlsx') else pd.read_csv(file2)
                    
                    # Normalização básica
                    df1[chave] = df1[chave].astype(str).str.strip().str.lower()
                    df2[chave] = df2[chave].astype(str).str.strip().str.lower()
                    
                    df_final = pd.merge(df1, df2, on=chave, how="inner")
                    
                    st.success(f"✅ Sucesso! {len(df_final)} linhas combinadas encontradas.")
                    
                    with st.expander("👀 Espiar Dados (Primeiras 5 linhas)"):
                        st.dataframe(df_final.head())
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_final.to_excel(writer, index=False)
                    
                    st.download_button(
                        label="⬇️ Baixar Resultado Final (.xlsx)",
                        data=output.getvalue(),
                        file_name="planilha_unida_toolbox.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                except Exception as e:
                    st.error(f"❌ Erro ao processar: {e}. Verifique se o nome da coluna chave está EXATAMENTE igual nos dois arquivos.")

# ==============================================================================
# PÁGINA: PDF TOOLS
# ==============================================================================
elif st.session_state.page == "PDF Tools":
    st.markdown("## 📄 Ferramentas de PDF")
    st.markdown("Manipule seus documentos sem instalar programas pesados.")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔗 Unir PDFs", "🖼️ Extrair Imagens (Beta)"])
    
    with tab1:
        st.markdown("#### Unir Múltiplos PDFs em um só")
        files = st.file_uploader("Selecione todos os PDFs (Segure Ctrl para selecionar vários)", type=['pdf'], accept_multiple_files=True)
        
        if files:
            st.info(f"{len(files)} arquivos selecionados.")
            if st.button("🧩 Juntar PDFs Agora"):
                with st.spinner("Fundindo documentos..."):
                    doc_final = fitz.open()
                    for pdf_file in files:
                        with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
                            doc_final.insert_pdf(doc)
                    
                    output = io.BytesIO()
                    doc_final.save(output)
                    st.success("✅ PDFs unidos com sucesso!")
                    st.download_button("⬇️ Baixar PDF Completo", output.getvalue(), "unido_toolbox.pdf", "application/pdf")

    with tab2:
        st.warning("⚠️ Funcionalidade Beta: Extrai a primeira página como imagem.")
        # Placeholder para futura implementação

# ==============================================================================
# PÁGINA: LIMPAR LISTAS
# ==============================================================================
elif st.session_state.page == "Limpar Listas":
    st.markdown("## 🧹 Higienização de Texto")
    st.markdown("Ideal para listas de emails, nomes ou códigos.")
    st.markdown("---")
    
    col_input, col_stats = st.columns([2, 1])
    
    with col_input:
        txt_input = st.text_area("Cole sua lista bruta aqui (um item por linha):", height=300, placeholder="item1\nitem2\nitem1 (duplicado)\nitem3...")
    
    with col_stats:
        st.markdown("### Estatísticas")
        container = st.container()
        if txt_input:
            linhas = [x.strip() for x in txt_input.splitlines() if x.strip()]
            unicos = sorted(list(set(linhas)))
            duplicados = len(linhas) - len(unicos)
            
            st.markdown(f"""
            <div style="background:white; padding:1.5rem; border-radius:12px; border:1px solid #E2E8F0; margin-bottom:1rem;">
                <h3 style="color:#64748B; font-size:0.9rem; margin:0;">TOTAL ENTRADA</h3>
                <p style="font-size:2rem; font-weight:700; color:#1E293B; margin:0;">{len(linhas)}</p>
            </div>
            <div style="background:white; padding:1.5rem; border-radius:12px; border:1px solid #E2E8F0; margin-bottom:1rem;">
                <h3 style="color:#EF4444; font-size:0.9rem; margin:0;">DUPLICATAS</h3>
                <p style="font-size:2rem; font-weight:700; color:#EF4444; margin:0;">-{duplicados}</p>
            </div>
             <div style="background:white; padding:1.5rem; border-radius:12px; border:1px solid #E2E8F0; border-left: 5px solid #10B981;">
                <h3 style="color:#10B981; font-size:0.9rem; margin:0;">TOTAL ÚNICOS</h3>
                <p style="font-size:2rem; font-weight:700; color:#10B981; margin:0;">{len(unicos)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.download_button("⬇️ Baixar Lista Limpa (.txt)", "\n".join(unicos), "lista_limpa.txt")
        else:
            st.info("Cole os dados ao lado para ver a mágica.")

# ==============================================================================
# PÁGINA: COMPRESSOR
# ==============================================================================
elif st.session_state.page == "Compressor":
    st.markdown("## 🖼️ Compressor de Imagem")
    st.markdown("Reduza o tamanho de arquivos JPG/PNG sem perder qualidade visível.")
    st.markdown("---")
    
    uploaded_img = st.file_uploader("Arraste sua imagem aqui", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_img:
        st.markdown("### Ajuste de Nível")
        qualidade = st.slider("Qualidade da Compressão (Menor = Arquivo menor)", 10, 100, 60)
        
        col_orig, col_new = st.columns(2)
        
        image = Image.open(uploaded_img)
        buf = io.BytesIO()
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # Processamento em tempo real
        image.save(buf, format="JPEG", quality=qualidade, optimize=True)
        byte_im = buf.getvalue()
        
        size_orig = uploaded_img.size / 1024
        size_new = len(byte_im) / 1024
        reducao = ((size_orig - size_new) / size_orig) * 100
        
        with col_orig:
            st.image(image, caption="Original", use_container_width=True)
            st.markdown(f"**Tamanho:** {size_orig:.1f} KB")
            
        with col_new:
            st.image(byte_im, caption=f"Comprimida (Qualidade {qualidade})", use_container_width=True)
            st.markdown(f"**Tamanho:** <span style='color:#10B981; font-weight:bold'>{size_new:.1f} KB</span>", unsafe_allow_html=True)
            st.markdown(f"📉 Redução de **{reducao:.1f}%**")
            
        st.download_button("⬇️ Baixar Imagem Otimizada", byte_im, "imagem_comprimida_toolbox.jpg", "image/jpeg")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
        <p>Desenvolvido por Hayron Rodrigues Neves com Python e Streamlit | Toolbox</p>
    </div>
""", unsafe_allow_html=True)

