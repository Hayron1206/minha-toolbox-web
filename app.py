import streamlit as st
import pandas as pd
from PIL import Image
import io
import hashlib
import qrcode
import fitz  # PyMuPDF
import time
import zipfile
import os

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

# --- CSS PERSONALIZADO (DESIGN SYSTEM PREMIUM CORRIGIDO) ---
st.markdown("""
<style>
    /* Importando fonte Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* === RESET GLOBAL & FORÇAR MODO CLARO === */
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* Forçar cores escuras em textos para evitar "branco no branco" */
    h1, h2, h3, h4, h5, h6 { color: #1E293B !important; font-weight: 700; letter-spacing: -0.02em; }
    p, li, span, label, div.stMarkdown, .stMarkdown p { color: #334155 !important; }
    
    /* Exceção: Textos dentro de toasts ou notificações de erro/sucesso podem precisar de cor clara.
       Abaixo garantimos que inputs tenham texto escuro. */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        color: #1E293B !important;
    }

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
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {
        color: #475569 !important;
    }
    
    /* === HERO BANNER === */
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
    /* Forçar branco apenas dentro do banner */
    .hero-banner h1, .hero-banner p, .hero-banner span { color: white !important; }
    .hero-banner h1 { font-size: 3rem; margin-bottom: 1rem; }
    .hero-banner p { font-size: 1.25rem; font-weight: 300; opacity: 0.9; }

    /* === CARDS FLUTUANTES (DASHBOARD) === */
    .dashboard-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid #F1F5F9;
        box-shadow: 0 10px 30px -5px rgba(0,0,0,0.05);
        text-align: center;
        transition: all 0.3s ease;
        height: 340px; /* Aumentei a altura para dar respiro */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        top: 0;
    }
    .dashboard-card:hover {
        top: -8px;
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.1);
        border-color: #BFDBFE;
    }
    .card-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start; /* Alinha conteúdo no topo */
    }
    .card-icon {
        font-size: 48px;
        margin-bottom: 2rem; /* Mais espaço abaixo do ícone */
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        width: 80px;
        height: 80px;
        line-height: 80px;
        border-radius: 20px;
        display: block;
        color: #2563EB;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.1);
    }
    .card-title { font-weight: 700; font-size: 1.25rem; color: #1E293B !important; margin-bottom: 0.75rem; display: block; }
    .card-desc { color: #64748B !important; font-size: 0.95rem; line-height: 1.5; margin-bottom: 1rem; display: block; }
    
    /* Botão dentro do card */
    .dashboard-card button {
        margin-top: auto;
    }

    /* === BOTÕES CUSTOMIZADOS === */
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
        color: white !important;
    }
    div.stButton > button p { color: white !important; } /* Garante texto branco no botão */

    /* === INPUTS E FORMS === */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 10px 12px;
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
    }
    .stFileUploader:hover {
        border-color: #3B82F6;
        background-color: #EFF6FF;
    }
    .stFileUploader label { font-weight: 600; color: #475569 !important; }
    .stFileUploader small { color: #94A3B8 !important; }

    /* === RESULTADOS E BOXES === */
    /* Container Visual Branco */
    div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px;
    }

    /* === FOOTER === */
    .footer {
        text-align: center;
        margin-top: 4rem;
        padding: 2rem;
        border-top: 1px solid #E2E8F0;
        color: #94A3B8 !important;
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
    .badge-blue { background-color: #DBEAFE; color: #1E40AF !important; }
    .badge-green { background-color: #DCFCE7; color: #166534 !important; }
    
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
    
    st.markdown('<p style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; margin-bottom: 0.5rem; letter-spacing: 0.05em;">MENU PRINCIPAL</p>', unsafe_allow_html=True)
    if st.button("🏠 Dashboard", use_container_width=True): navigate_to("Dashboard")
    
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; margin-bottom: 0.5rem; letter-spacing: 0.05em;">FERRAMENTAS</p>', unsafe_allow_html=True)
    
    # Lista de ferramentas atualizada
    if st.button("📱 Gerador QR Code", use_container_width=True): navigate_to("QR Code")
    if st.button("📊 Unir Planilhas", use_container_width=True): navigate_to("Unir Planilhas")
    if st.button("✂️ Divisor Planilhas", use_container_width=True): navigate_to("Divisor Planilhas")
    if st.button("📄 PDF Tools", use_container_width=True): navigate_to("PDF Tools")
    if st.button("🔐 Calc. Hash", use_container_width=True): navigate_to("Calc Hash")
    if st.button("🧹 Limpar Listas", use_container_width=True): navigate_to("Limpar Listas")
    if st.button("🖼️ Compressor Img", use_container_width=True): navigate_to("Compressor")

    st.markdown("---")
    
    st.markdown("""
    <div style="background: #F8FAFC; padding: 1rem; border-radius: 12px; border: 1px solid #E2E8F0;">
        <p style="font-size: 0.8rem; margin-bottom: 0.5rem;"><strong>Status</strong></p>
        <span class="status-badge badge-green">● Online</span>
        <p style="font-size: 0.7rem; color: #94A3B8; margin-top: 0.5rem;">v1.6.0 (Fix QR)</p>
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
                <span class="status-badge badge-blue" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); margin-bottom: 1rem;">NOVIDADE: NOVAS FERRAMENTAS</span>
                <h1>Sua caixa de ferramentas,<br>agora na nuvem.</h1>
                <p>Otimize seu fluxo de trabalho com ferramentas rápidas, seguras e gratuitas.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Grid de Cards (Agora com 4 colunas e melhor espaçamento)
    st.markdown("### 🚀 Acesso Rápido")
    
    # Linha 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-content">
                <span class="card-icon">📱</span>
                <span class="card-title">QR Code</span>
                <span class="card-desc">Crie códigos QR para links, Wi-Fi e textos.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir QR Code →", key="btn_home_qr", on_click=navigate_to, args=("QR Code",))
    with col2:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-content">
                <span class="card-icon">📊</span>
                <span class="card-title">Planilhas</span>
                <span class="card-desc">Combine arquivos Excel ou CSV em segundos.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir Unir →", key="btn_home_xls", on_click=navigate_to, args=("Unir Planilhas",))
    with col3:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-content">
                <span class="card-icon">✂️</span>
                <span class="card-title">Divisor</span>
                <span class="card-desc">Separe planilhas grandes em arquivos menores.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir Divisor →", key="btn_home_div", on_click=navigate_to, args=("Divisor Planilhas",))
    with col4:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-content">
                <span class="card-icon">📄</span>
                <span class="card-title">PDF Master</span>
                <span class="card-desc">Una múltiplos PDFs ou converta para imagem.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir PDFs →", key="btn_home_pdf", on_click=navigate_to, args=("PDF Tools",))

    st.markdown("<br>", unsafe_allow_html=True)

    # Linha 2
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-content">
                <span class="card-icon">🔐</span>
                <span class="card-title">Hash Calc</span>
                <span class="card-desc">Calcule MD5 e SHA256 de qualquer arquivo.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir Hash →", key="btn_home_hash", on_click=navigate_to, args=("Calc Hash",))
    with col6:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-content">
                <span class="card-icon">🧹</span>
                <span class="card-title">Listas</span>
                <span class="card-desc">Limpe duplicatas e ordene listas de texto.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir Limpeza →", key="btn_home_list", on_click=navigate_to, args=("Limpar Listas",))
    with col7:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-content">
                <span class="card-icon">🖼️</span>
                <span class="card-title">Compressor</span>
                <span class="card-desc">Otimize imagens JPG/PNG para web.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir Comp. →", key="btn_home_img", on_click=navigate_to, args=("Compressor",))
    with col8:
        # Placeholder visual para manter grid
        st.markdown("""
        <div class="dashboard-card" style="opacity:0.5; border-style:dashed;">
            <div class="card-content">
                <span class="card-icon" style="background:#f1f5f9; color:#94a3b8">🔜</span>
                <span class="card-title" style="color:#94a3b8 !important">Em breve</span>
                <span class="card-desc" style="color:#cbd5e1 !important">Mais ferramentas chegando...</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# PÁGINA: QR CODE (CORRIGIDO E FUNCIONAL)
# ==============================================================================
elif st.session_state.page == "QR Code":
    st.markdown("## 📱 Gerador de QR Code")
    st.markdown("Transforme qualquer texto ou link em uma imagem escaneável.")
    st.markdown("---")
    
    col_config, col_preview = st.columns([1, 1], gap="large")
    
    with col_config:
        st.markdown("### 1. Configuração")
        # Container Branco para Configuração
        with st.container():
            st.markdown('<div style="background:white; padding:20px; border-radius:10px; border:1px solid #E2E8F0;">', unsafe_allow_html=True)
            texto = st.text_input("Conteúdo (Link ou Texto):", placeholder="https://seu-site.com")
            
            c1, c2 = st.columns(2)
            with c1: cor_fill = st.color_picker("Cor do Código", "#000000")
            with c2: cor_back = st.color_picker("Cor do Fundo", "#FFFFFF")
            
            st.markdown("<br>", unsafe_allow_html=True)
            # Botão de ação explícito
            gerar_btn = st.button("✨ Gerar Código QR", type="primary", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
    with col_preview:
        st.markdown("### 2. Resultado")
        
        # O resultado agora fica dentro de um container nativo para evitar erros de layout
        with st.container():
            st.markdown('<div style="background:white; padding:30px; border-radius:10px; border:1px solid #E2E8F0; text-align:center; min-height: 350px; display:flex; flex-direction:column; justify-content:center; align-items:center;">', unsafe_allow_html=True)
            
            # Lógica: Gera se clicar no botão OU se já tiver texto e algo mudou
            if gerar_btn and texto:
                try:
                    qr = qrcode.QRCode(box_size=10, border=2)
                    qr.add_data(texto)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color=cor_fill, back_color=cor_back)
                    
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    # Exibe a imagem centralizada
                    st.image(byte_im, width=250, caption="Seu QR Code")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.download_button(
                        label="⬇️ Baixar Imagem (PNG)",
                        data=byte_im,
                        file_name="qrcode.png",
                        mime="image/png",
                        type="secondary"
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar: {e}")
            elif not texto:
                st.markdown('<span style="font-size:3rem; opacity:0.2;">📷</span>', unsafe_allow_html=True)
                st.caption("Digite o texto e clique em 'Gerar' para ver o resultado.")
            else:
                 # Estado inicial ou aguardando clique
                 st.info("Clique em 'Gerar Código QR' para atualizar.")

            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# PÁGINA: UNIR PLANILHAS
# ==============================================================================
elif st.session_state.page == "Unir Planilhas":
    st.markdown("## 📊 Unir Planilhas")
    st.markdown("Ferramenta poderosa para 'VLOOKUP' automático entre dois arquivos.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Arquivo Principal")
        file1 = st.file_uploader("Upload Planilha 1", type=['xlsx', 'csv'], key="f1")
    with col2:
        st.markdown("##### Arquivo Secundário")
        file2 = st.file_uploader("Upload Planilha 2", type=['xlsx', 'csv'], key="f2")
    
    st.markdown("<br>", unsafe_allow_html=True)
    chave = st.text_input("🔑 Nome da Coluna Chave:", placeholder="Ex: cpf, email, id_produto")
    
    if file1 and file2 and chave:
        if st.button("🚀 Processar e Unir Arquivos", type="primary"):
            try:
                df1 = pd.read_excel(file1) if file1.name.endswith('.xlsx') else pd.read_csv(file1)
                df2 = pd.read_excel(file2) if file2.name.endswith('.xlsx') else pd.read_csv(file2)
                
                # Normalização
                df1[chave] = df1[chave].astype(str).str.strip().str.lower()
                df2[chave] = df2[chave].astype(str).str.strip().str.lower()
                
                df_final = pd.merge(df1, df2, on=chave, how="inner")
                
                st.success(f"✅ Sucesso! {len(df_final)} linhas combinadas.")
                st.dataframe(df_final.head())
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False)
                
                st.download_button("⬇️ Baixar Resultado", output.getvalue(), "unido.xlsx", "application/vnd.ms-excel")
            except Exception as e:
                st.error(f"❌ Erro: {e}. Verifique o nome da coluna chave.")

# ==============================================================================
# PÁGINA: DIVISOR DE PLANILHAS (NOVO)
# ==============================================================================
elif st.session_state.page == "Divisor Planilhas":
    st.markdown("## ✂️ Divisor de Planilhas")
    st.markdown("Divida uma planilha grande em várias partes menores.")
    st.markdown("---")
    
    file_div = st.file_uploader("Upload da Planilha Grande", type=['xlsx', 'csv'])
    
    if file_div:
        df = pd.read_excel(file_div) if file_div.name.endswith('.xlsx') else pd.read_csv(file_div)
        st.info(f"Arquivo carregado com {len(df)} linhas.")
        
        metodo = st.radio("Como deseja dividir?", ["Por quantidade de linhas", "Por valor de uma coluna"])
        
        if metodo == "Por quantidade de linhas":
            qtd = st.number_input("Linhas por arquivo:", min_value=1, value=1000)
            if st.button("Dividir Agora"):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i in range(0, len(df), qtd):
                        chunk = df[i:i+qtd]
                        # Salva chunk
                        buf = io.BytesIO()
                        chunk.to_excel(buf, index=False)
                        zf.writestr(f"parte_{i//qtd + 1}.xlsx", buf.getvalue())
                
                st.success("Divisão concluída!")
                st.download_button("⬇️ Baixar Todos (ZIP)", zip_buffer.getvalue(), "planilhas_divididas.zip", "application/zip")
                
        else: # Por coluna
            colunas = df.columns.tolist()
            col_escolhida = st.selectbox("Escolha a coluna para agrupar:", colunas)
            if st.button("Dividir por Coluna"):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    grupos = df.groupby(col_escolhida)
                    for nome, dados in grupos:
                        nome_limpo = str(nome).replace("/","-")
                        buf = io.BytesIO()
                        dados.to_excel(buf, index=False)
                        zf.writestr(f"{col_escolhida}_{nome_limpo}.xlsx", buf.getvalue())
                
                st.success(f"Divisão concluída! {len(grupos)} arquivos gerados.")
                st.download_button("⬇️ Baixar Todos (ZIP)", zip_buffer.getvalue(), "planilhas_por_grupo.zip", "application/zip")

# ==============================================================================
# PÁGINA: PDF TOOLS (ATUALIZADO)
# ==============================================================================
elif st.session_state.page == "PDF Tools":
    st.markdown("## 📄 Ferramentas de PDF")
    st.markdown("Manipule seus documentos sem instalar programas pesados.")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔗 Unir PDFs", "🖼️ PDF para Imagem (Novo)"])
    
    with tab1:
        st.markdown("#### Unir Múltiplos PDFs")
        files = st.file_uploader("Selecione os PDFs (Ctrl+Click)", type=['pdf'], accept_multiple_files=True)
        if files and st.button("Juntar PDFs Agora"):
            doc_final = fitz.open()
            for pdf_file in files:
                with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
                    doc_final.insert_pdf(doc)
            output = io.BytesIO()
            doc_final.save(output)
            st.success("✅ PDFs unidos!")
            st.download_button("⬇️ Baixar PDF Completo", output.getvalue(), "unido.pdf", "application/pdf")

    with tab2:
        st.markdown("#### Converter PDF em Imagens (JPG)")
        file_pdf_img = st.file_uploader("Upload do PDF", type=['pdf'])
        if file_pdf_img and st.button("Converter Páginas"):
            with fitz.open(stream=file_pdf_img.read(), filetype="pdf") as doc:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, page in enumerate(doc):
                        pix = page.get_pixmap(dpi=150)
                        img_data = pix.tobytes("jpg")
                        zf.writestr(f"pagina_{i+1}.jpg", img_data)
                
                st.success(f"Conversão concluída! {len(doc)} páginas processadas.")
                st.download_button("⬇️ Baixar Imagens (ZIP)", zip_buffer.getvalue(), "paginas_pdf.zip", "application/zip")

# ==============================================================================
# PÁGINA: CALCULADORA HASH (NOVO)
# ==============================================================================
elif st.session_state.page == "Calc Hash":
    st.markdown("## 🔐 Calculadora de Hash")
    st.markdown("Verifique a integridade dos seus arquivos (MD5, SHA256).")
    st.markdown("---")
    
    file_hash = st.file_uploader("Arraste o arquivo para calcular o Hash")
    
    if file_hash:
        bytes_data = file_hash.getvalue()
        
        col_res1, col_res2 = st.columns(2)
        
        md5 = hashlib.md5(bytes_data).hexdigest()
        sha256 = hashlib.sha256(bytes_data).hexdigest()
        
        with col_res1:
            st.markdown("### MD5")
            st.code(md5, language="text")
        
        with col_res2:
            st.markdown("### SHA256")
            st.code(sha256, language="text")
        
        st.info("Dica: Use hashes para garantir que um arquivo baixado não foi corrompido ou alterado.")

# ==============================================================================
# PÁGINA: LIMPAR LISTAS
# ==============================================================================
elif st.session_state.page == "Limpar Listas":
    st.markdown("## 🧹 Higienização de Texto")
    st.markdown("---")
    
    col_input, col_stats = st.columns([2, 1])
    with col_input:
        txt_input = st.text_area("Cole sua lista bruta aqui:", height=300)
    with col_stats:
        if txt_input:
            linhas = [x.strip() for x in txt_input.splitlines() if x.strip()]
            unicos = sorted(list(set(linhas)))
            st.markdown(f"""
            <div class="result-box">
                <h3>Total: {len(linhas)}</h3>
                <h3 style="color:#10B981 !important">Únicos: {len(unicos)}</h3>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("⬇️ Baixar Limpo", "\n".join(unicos), "lista.txt")

# ==============================================================================
# PÁGINA: COMPRESSOR
# ==============================================================================
elif st.session_state.page == "Compressor":
    st.markdown("## 🖼️ Compressor de Imagem")
    st.markdown("---")
    img = st.file_uploader("Upload Imagem", type=['jpg', 'png'])
    if img:
        qual = st.slider("Qualidade", 10, 100, 60)
        image = Image.open(img)
        buf = io.BytesIO()
        if image.mode == 'RGBA': image = image.convert('RGB')
        image.save(buf, format="JPEG", quality=qual, optimize=True)
        byte_im = buf.getvalue()
        
        c1, c2 = st.columns(2)
        c1.image(image, caption="Original")
        c2.image(byte_im, caption="Comprimida")
        st.download_button("⬇️ Baixar", byte_im, "comprimida.jpg", "image/jpeg")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
        <p>Desenvolvido com ❤️ Python e Streamlit | Toolbox Pro © 2024</p>
    </div>
""", unsafe_allow_html=True)
